# usuarios/routesUsuarios.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from werkzeug.security import generate_password_hash
from models import db, Usuario, Rol
from forms import UsuarioForm
from . import usuarios_bp


@usuarios_bp.route('/usuarios')
# @login_required
def index():
    usuarios = Usuario.query.all()
    return render_template('modulo-usuarios/modulo-usuarios.html', usuarios=usuarios)


@usuarios_bp.route('/usuarios/agregar', methods=['GET', 'POST'])
# @login_required
def agregar():
    form = UsuarioForm()
    form.id_rol.choices = [(r.id_rol, r.nombre) for r in Rol.query.all()]
    if form.validate_on_submit():
        usuario = Usuario(
            nombre   = form.nombre.data,
            email    = form.email.data,
            password = generate_password_hash(form.password.data),
            id_rol   = form.id_rol.data,
            activo = form.activo.data == "1"
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Usuario creado correctamente.', 'success')
        return redirect(url_for('usuarios.index'))
    return render_template('modulo-usuarios/form-usuarios.html', form=form, accion='Agregar')


@usuarios_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
# @login_required
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    form = UsuarioForm(obj=usuario)
    form.id_rol.choices = [(r.id_rol, r.nombre) for r in Rol.query.all()]

    if request.method == 'GET':                          # ← solo precargar en GET
        form.activo.data = "1" if usuario.activo else "0"

    if form.validate_on_submit():
        usuario.nombre = form.nombre.data
        usuario.email  = form.email.data
        usuario.id_rol = form.id_rol.data
        usuario.activo = form.activo.data == "1"
        if form.password.data:
            usuario.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('usuarios.index'))

    return render_template('modulo-usuarios/form-usuarios.html', form=form, accion='Editar')

@usuarios_bp.route('/usuarios/eliminar/<int:id>')
# @login_required
def eliminar(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('usuarios.index'))