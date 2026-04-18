
# clientes/routesClientes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Cliente, Usuario
from forms import ClienteForm
from . import clientes_bp
from utils.decorators import empleado_required, gerente_or_admin_required, login_required_with_message
from werkzeug.security import generate_password_hash


@clientes_bp.route('/clientes')
@login_required_with_message
@login_required
@gerente_or_admin_required
@empleado_required
def index():
    clientes = Cliente.query.all()
    return render_template('modulo-clientes/modulo-clientes.html', clientes=clientes)


@clientes_bp.route('/clientes/agregar', methods=['GET', 'POST'])
@login_required_with_message
@login_required
@gerente_or_admin_required
def agregar():
    form = ClienteForm()
    
    if form.validate_on_submit():
        # Verificar si el email ya existe en Usuario
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('El correo electrónico ya está registrado.', 'danger')
            return render_template('modulo-clientes/form-clientes.html', form=form, accion='Agregar')
        
        try:
            # 1. Crear el Usuario primero
            nuevo_usuario = Usuario(
                email=form.email.data,
                password=generate_password_hash("Cliente123"),  # Contraseña por defecto
                id_rol=5,  # Ajusta según tu BD: 1=Admin, 2=Gerente, 3=Cliente
                activo=True
            )
            db.session.add(nuevo_usuario)
            db.session.flush()  
            
            cliente = Cliente(
                id_usuario=nuevo_usuario.id_usuario,  
                nombre=form.nombre.data,
                telefono=form.telefono.data,
                direccion=form.direccion.data,
                estatus=form.estatus.data
            )
            db.session.add(cliente)
            db.session.commit()
            
            flash('Cliente agregado correctamente.', 'success')
            return redirect(url_for('clientes.index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear cliente: {e}")
            flash(f'Error al crear el cliente: {str(e)}', 'danger')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'danger')
    
    return render_template('modulo-clientes/form-clientes.html', form=form, accion='Agregar')


@clientes_bp.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required_with_message
@login_required
@gerente_or_admin_required
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    usuario = cliente.usuario  # Obtener el usuario vinculado
    
    form = ClienteForm(obj=cliente)
    
    if request.method == 'GET':
        # Precargar el email desde Usuario
        form.email.data = usuario.email
    
    if form.validate_on_submit():
        # Verificar si el email ya existe en otro usuario
        email_existente = Usuario.query.filter(
            Usuario.email == form.email.data,
            Usuario.id_usuario != usuario.id_usuario
        ).first()
        
        if email_existente:
            flash('El correo electrónico ya está registrado por otro usuario.', 'danger')
            return render_template('modulo-clientes/form-clientes.html', form=form, accion='Editar')
        
        try:
            # Actualizar Usuario
            usuario.email = form.email.data
            cliente.nombre = form.nombre.data
            cliente.telefono = form.telefono.data
            cliente.direccion = form.direccion.data
            cliente.estatus = form.estatus.data
            
            db.session.commit()
            flash('Cliente actualizado correctamente.', 'success')
            return redirect(url_for('clientes.index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al editar cliente: {e}")
            flash('Error al actualizar el cliente.', 'danger')
    
    return render_template('modulo-clientes/form-clientes.html', form=form, accion='Editar')


@clientes_bp.route('/clientes/eliminar/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def eliminar(id):
    cliente = Cliente.query.get_or_404(id)
    try:
        # Eliminar también el usuario asociado
        usuario = cliente.usuario
        db.session.delete(cliente)
        if usuario:
            db.session.delete(usuario)
        db.session.commit()
        flash('Cliente eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar cliente: {e}")
        flash('Error al eliminar el cliente.', 'danger')
    
    return redirect(url_for('clientes.index'))