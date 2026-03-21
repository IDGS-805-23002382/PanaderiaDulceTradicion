from flask import render_template
from models import Empleado

# empleado/routesEmpleados.py
from flask import render_template, redirect, url_for, flash
from models import db, Empleado, Rol
from forms import EmpleadoForm
from flask_login import login_required

from . import empleados_bp


@empleados_bp.route("/empleados")

def index():

    empleados = Empleado.query.all()

    return render_template(
        "modulo-empleado/modulo-empleado.html",
        empleados=empleados
    )

# @login_required
def index():
    empleados = Empleado.query.all()
    return render_template("modulo-empleado/modulo-empleado.html", empleados=empleados)


@empleados_bp.route("/empleados/agregar", methods=['GET', 'POST'])
# @login_required
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
# @login_required
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


@empleados_bp.route("/empleados/eliminar/<int:id>")
# @login_required
def eliminar(id):
    empleado = Empleado.query.get_or_404(id)
    db.session.delete(empleado)
    db.session.commit()
    flash('Empleado eliminado.', 'success')
    return redirect(url_for('empleados.index'))
