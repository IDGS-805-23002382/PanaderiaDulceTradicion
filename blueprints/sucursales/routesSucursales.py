from flask import render_template, request, redirect, url_for
from forms import SucursalForm
from models import db, Sucursal
from . import sucursales_bp


@sucursales_bp.route('/sucursales/')
def sucursales():

    sucursales = Sucursal.query.filter_by(estatus='activo').all()

    return render_template(
        "modulo-sucursales/listaSucursales.html",
        sucursales=sucursales
    )


@sucursales_bp.route('/registrarSucursal', methods=['GET','POST'])
def registrarSucursal():

    form = SucursalForm()

    if form.validate_on_submit():

        nueva = Sucursal(
            nombre=form.nombre.data,
            direccion=form.direccion.data,
            telefono=form.telefono.data,
            ciudad=form.ciudad.data
        )

        db.session.add(nueva)
        db.session.commit()

        return redirect(url_for('sucursales.sucursales'))

    return render_template("modulo-sucursales/formSucursales.html", form=form)


@sucursales_bp.route('/editarSucursal/<int:id>', methods=['GET','POST'])
def editarSucursal(id):

    sucursal = Sucursal.query.get_or_404(id)

    if request.method == 'POST':
        sucursal.nombre = request.form['nombre']
        sucursal.direccion = request.form['direccion']
        sucursal.telefono = request.form['telefono']
        sucursal.ciudad = request.form['ciudad']

        db.session.commit()

        return redirect(url_for('sucursales.sucursales'))

    return render_template(
        "modulo-sucursales/editarSucursales.html",
        sucursal=sucursal
    )
    
    
@sucursales_bp.route('/desactivarSucursal/<int:id>')
def desactivarSucursal(id):

    sucursal = Sucursal.query.get_or_404(id)

    sucursal.estatus = 'inactivo'

    db.session.commit()

    return redirect(url_for('sucursales.sucursales'))   