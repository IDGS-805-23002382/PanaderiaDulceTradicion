

# blueprints/empleados/routesEmpleados.py
from flask import render_template, redirect, url_for, flash, request
from models import db, Empleado, Rol, Usuario
from forms import EmpleadoForm
from flask_login import login_required
from . import empleados_bp
from utils.decorators import empleado_required, gerente_or_admin_required, login_required_with_message
from werkzeug.security import generate_password_hash

@empleados_bp.route("/empleados")
@login_required
@gerente_or_admin_required
@empleado_required
def index():
    query = Empleado.query

    # FILTRO ESTATUS
    estatus = request.args.get('estatus')
    if estatus:
        query = query.filter(Empleado.estatus == estatus)

    # BÚSQUEDA
    buscar = request.args.get('buscar')
    if buscar:
        query = query.filter(Empleado.nombre.ilike(f'%{buscar}%'))

    # ORDEN
    orden = request.args.get('orden')
    if orden == 'az':
        query = query.order_by(Empleado.nombre.asc())
    elif orden == 'za':
        query = query.order_by(Empleado.nombre.desc())

    empleados = query.all()
    return render_template("modulo-empleado/modulo-empleado.html", empleados=empleados)


@empleados_bp.route("/empleados/agregar", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
def agregar():
    form = EmpleadoForm()
    form.id_rol.choices = [(r.id_rol, r.nombre) for r in Rol.query.all()]

    if form.validate_on_submit():
        
        try:
            nuevo_usuario = Usuario(
                email=form.email.data, 
                password=generate_password_hash("123456"),
                id_rol=form.id_rol.data,
                activo=True
            )
            db.session.add(nuevo_usuario)
            db.session.flush() 

            # 2. Crear el Empleado
            nuevo_empleado = Empleado(
                id_usuario=nuevo_usuario.id_usuario,
                nombre=form.nombre.data,
                telefono=form.telefono.data or None,
                direccion=form.direccion.data or None,
                puesto=form.puesto.data or None,
                salario=form.salario.data or 0,
                fecha_nacimiento=form.fecha_nacimiento.data if form.fecha_nacimiento.data else None,
                fecha_contratacion=form.fecha_contratacion.data if form.fecha_contratacion.data else None,
                estatus=form.estatus.data
            )

            db.session.add(nuevo_empleado)
            db.session.commit()

            flash('Empleado creado exitosamente.', 'success')
            return redirect(url_for('empleados.index'))

        except Exception as e:
            db.session.rollback()
            print(f"ERROR: {e}")
            flash(f'Error técnico: {str(e)[:100]}', 'danger')

    return render_template("modulo-empleado/form-empleado.html", form=form, accion='Agregar')


@empleados_bp.route("/empleados/editar/<int:id>", methods=['GET', 'POST'])
@login_required_with_message
@login_required
@gerente_or_admin_required
def editar(id):
    empleado = Empleado.query.get_or_404(id)
    usuario = empleado.usuario
    form = EmpleadoForm(obj=empleado)
    form.id_rol.choices = [(r.id_rol, r.nombre) for r in Rol.query.all()]

    if request.method == 'GET':
        # Si tu form tiene email, precarga
        if hasattr(form, 'email'):
            form.email.data = usuario.email
        form.id_rol.data = usuario.id_rol

    if form.validate_on_submit():
        # Validar email duplicado si el form tiene campo email
        if hasattr(form, 'email') and form.email.data:
            email_en_uso = Usuario.query.filter(
                Usuario.email == form.email.data, 
                Usuario.id_usuario != usuario.id_usuario
            ).first()

            if email_en_uso:
                flash('Error: El correo electrónico ya está registrado por otro usuario.', 'danger')
                return render_template("modulo-empleado/form-empleado.html", form=form, accion='Editar')

        try:
            # Actualizar Usuario
            if hasattr(form, 'email') and form.email.data:
                usuario.email = form.email.data
            usuario.id_rol = form.id_rol.data
            
            # Actualizar Empleado
            empleado.nombre = form.nombre.data
            empleado.telefono = form.telefono.data
            empleado.direccion = form.direccion.data
            empleado.puesto = form.puesto.data
            empleado.salario = form.salario.data
            empleado.estatus = form.estatus.data

            db.session.commit()
            flash('Empleado actualizado correctamente.', 'success')
            return redirect(url_for('empleados.index'))

        except Exception as e:
            db.session.rollback()
            print(f"Error al editar: {e}")
            flash('Error inesperado al guardar los cambios.', 'danger')

    return render_template("modulo-empleado/form-empleado.html", form=form, accion='Editar')


@empleados_bp.route("/empleados/eliminar/<int:id>", methods=['GET', 'POST'])
@login_required_with_message
@login_required
@gerente_or_admin_required
def eliminar(id):
    empleado = Empleado.query.get_or_404(id)
    if request.method == 'POST':
        try:
            usuario = empleado.usuario
            db.session.delete(empleado)
            if usuario:
                db.session.delete(usuario)
            db.session.commit()
            flash(f'Empleado {empleado.nombre} eliminado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar: {str(e)}', 'danger')
        return redirect(url_for('empleados.index'))
    return render_template("modulo-empleado/confirmar-eliminar.html", empleado=empleado)