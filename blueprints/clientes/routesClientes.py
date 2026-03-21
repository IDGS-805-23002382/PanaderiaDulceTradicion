# clientes/routesClientes.py
from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from models import db, Cliente
from forms import ClienteForm
from . import clientes_bp


@clientes_bp.route('/clientes')
# @login_required
def index():
    clientes = Cliente.query.all()
    return render_template('modulo-clientes/modulo-clientes.html', clientes=clientes)


@clientes_bp.route('/clientes/agregar', methods=['GET', 'POST'])
# @login_required
def agregar():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente(
            nombre    = form.nombre.data,
            telefono  = form.telefono.data,
            email     = form.email.data,
            direccion = form.direccion.data,
            estatus   = form.estatus.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente agregado correctamente.', 'success')
        return redirect(url_for('clientes.index'))
    return render_template('modulo-clientes/form-clientes.html', form=form, accion='Agregar')


@clientes_bp.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
# @login_required
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(obj=cliente)
    if form.validate_on_submit():
        cliente.nombre    = form.nombre.data
        cliente.telefono  = form.telefono.data
        cliente.email     = form.email.data
        cliente.direccion = form.direccion.data
        cliente.estatus   = form.estatus.data
        db.session.commit()
        flash('Cliente actualizado.', 'success')
        return redirect(url_for('clientes.index'))
    return render_template('modulo-clientes/form-clientes.html', form=form, accion='Editar')


@clientes_bp.route('/clientes/eliminar/<int:id>')
# @login_required
def eliminar(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado.', 'success')
    return redirect(url_for('clientes.index'))