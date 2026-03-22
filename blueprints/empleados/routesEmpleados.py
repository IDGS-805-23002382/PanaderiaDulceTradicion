# blueprints/empleados/routesEmpleados.py
from flask import render_template, redirect, url_for, flash, request
from models import db, Empleado, Rol
from forms import EmpleadoForm
from flask_login import login_required
from . import empleados_bp
from utils.decorators import empleado_required, gerente_or_admin_required

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
@empleado_required
def agregar():
    form = EmpleadoForm()
    form.id_rol.choices = [(r.id_rol, r.nombre) for r in Rol.query.all()]
    if form.validate_on_submit():
        empleado = Empleado(
            nombre             = form.nombre.data,
            telefono           = form.telefono.data,
            email              = form.email.data,
            direccion          = form.direccion.data,
            puesto             = form.puesto.data,
            salario            = form.salario.data,
            fecha_nacimiento   = form.fecha_nacimiento.data,
            fecha_contratacion = form.fecha_contratacion.data,
            id_rol             = form.id_rol.data,
            estatus            = form.estatus.data
        )
        db.session.add(empleado)
        db.session.commit()
        flash('Empleado agregado correctamente.', 'success')
        return redirect(url_for('empleados.index'))
    return render_template("modulo-empleado/form-empleado.html", form=form, accion='Agregar')


@empleados_bp.route("/empleados/editar/<int:id>", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
@empleado_required
def editar(id):
    empleado = Empleado.query.get_or_404(id)
    form = EmpleadoForm(obj=empleado)
    form.id_rol.choices = [(r.id_rol, r.nombre) for r in Rol.query.all()]
    if form.validate_on_submit():
        empleado.nombre             = form.nombre.data
        empleado.telefono           = form.telefono.data
        empleado.email              = form.email.data
        empleado.direccion          = form.direccion.data
        empleado.puesto             = form.puesto.data
        empleado.salario            = form.salario.data
        empleado.fecha_nacimiento   = form.fecha_nacimiento.data
        empleado.fecha_contratacion = form.fecha_contratacion.data
        empleado.id_rol             = form.id_rol.data
        empleado.estatus            = form.estatus.data
        db.session.commit()
        flash('Empleado actualizado.', 'success')
        return redirect(url_for('empleados.index'))
    return render_template("modulo-empleado/form-empleado.html", form=form, accion='Editar')


@empleados_bp.route("/empleados/eliminar/<int:id>", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
@empleado_required
def eliminar(id):
    empleado = Empleado.query.get_or_404(id)
    if request.method == 'POST':
        db.session.delete(empleado)
        db.session.commit()
        flash(f'Empleado {empleado.nombre} eliminado correctamente.', 'success')
        return redirect(url_for('empleados.index'))
    return render_template("modulo-empleado/confirmar-eliminar.html", empleado=empleado)