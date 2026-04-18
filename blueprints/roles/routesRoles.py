# roles/routesRoles.py
from flask import render_template, redirect, url_for, flash
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message
from flask_login import login_required
from models import db, Rol
from forms import RolForm
from . import roles_bp


@roles_bp.route('/roles')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def index():
    roles = Rol.query.all()
    return render_template('modulo-roles/modulo-roles.html', roles=roles)


@roles_bp.route('/roles/agregar', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def agregar():
    form = RolForm()
    if form.validate_on_submit():
        rol = Rol(
            nombre      = form.nombre.data,
            descripcion = form.descripcion.data
        )
        db.session.add(rol)
        db.session.commit()
        flash('Rol creado correctamente.', 'success')
        return redirect(url_for('roles.index'))
    return render_template('modulo-roles/form-roles.html', form=form, accion='Agregar')


@roles_bp.route('/roles/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def editar(id):
    rol = Rol.query.get_or_404(id)
    form = RolForm(obj=rol)
    if form.validate_on_submit():
        rol.nombre      = form.nombre.data
        rol.descripcion = form.descripcion.data
        db.session.commit()
        flash('Rol actualizado.', 'success')
        return redirect(url_for('roles.index'))
    return render_template('modulo-roles/form-roles.html', form=form, accion='Editar')


@roles_bp.route('/roles/eliminar/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
def eliminar(id):
    rol = Rol.query.get_or_404(id)
    db.session.delete(rol)
    db.session.commit()
    flash('Rol eliminado.', 'success')
    return redirect(url_for('roles.index'))