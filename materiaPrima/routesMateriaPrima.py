from flask import render_template, request, redirect, url_for, flash
from models import MateriaPrima, Proveedor, db
from sqlalchemy import or_
from . import materiaPrima_bp

import forms


@materiaPrima_bp.route('/materiaPrima')
def materiaPrima():

    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = MateriaPrima.query

    # BUSCAR
    if buscar and buscar.strip() != "":
        query = query.filter(
            or_(
                MateriaPrima.nombre.ilike(f"%{buscar}%"),
                MateriaPrima.unidad_medida.ilike(f"%{buscar}%")
            )
        )

    # FILTRAR POR ESTATUS
    if estatus:
        query = query.filter(MateriaPrima.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(MateriaPrima.nombre.asc())

    elif orden == "za":
        query = query.order_by(MateriaPrima.nombre.desc())

    # OBTENER DATOS
    materiaPrima = query.all()

    return render_template(
        "modulo-materiaPrima/modulo-materiaPrima.html",
        materiaPrima=materiaPrima
    )

# AGREGAR MATERIA PRIMA
@materiaPrima_bp.route('/agregarMateriaPrima', methods=['GET','POST'])
def agregarMateriaPrima():

    form = forms.MateriaPrimaForm()

    # cargar proveedores en el select
    proveedores = Proveedor.query.all()
    form.id_proveedor.choices = [(p.id_proveedor, p.nombre) for p in proveedores]

    if form.validate_on_submit():

        nueva_materia = MateriaPrima(
            nombre=form.nombre.data,
            unidad_medida=form.unidad_medida.data,
            stock_actual=form.stock_actual.data,
            stock_minimo=form.stock_minimo.data,
            precio_unitario=form.precio_unitario.data,
            id_proveedor=form.id_proveedor.data,
            fecha_ultima_compra=form.fecha_ultima_compra.data,
            estatus=form.estatus.data
        )

        db.session.add(nueva_materia)
        db.session.commit()

        return redirect(url_for('materiaPrima.materiaPrima'))

    return render_template(
        'modulo-materiaPrima/agregarMateriaPrima.html',
        form=form
    )


# DETALLE
@materiaPrima_bp.route('/detalleMateriaPrima/<int:id>')
def detalleMateriaPrima(id):

    materia = MateriaPrima.query.get_or_404(id)

    return render_template(
        'modulo-materiaPrima/detallesMateriaPrima.html',
        materia=materia
    )


# EDITAR
@materiaPrima_bp.route('/editarMateriaPrima/<int:id>', methods=['GET','POST'])
def modificarMateriaPrima(id):

    materiaPrima = MateriaPrima.query.get_or_404(id)

    form = forms.MateriaPrimaForm(obj=materiaPrima)

    proveedores = Proveedor.query.all()
    form.id_proveedor.choices = [(p.id_proveedor, p.nombre) for p in proveedores]

    if form.validate_on_submit():

        materiaPrima.nombre = form.nombre.data
        materiaPrima.unidad_medida = form.unidad_medida.data
        materiaPrima.stock_actual = form.stock_actual.data
        materiaPrima.stock_minimo = form.stock_minimo.data
        materiaPrima.precio_unitario = form.precio_unitario.data
        materiaPrima.id_proveedor = form.id_proveedor.data
        materiaPrima.fecha_ultima_compra = form.fecha_ultima_compra.data
        materiaPrima.estatus = form.estatus.data

        db.session.commit()

        return redirect(url_for('materiaPrima.materiaPrima'))

    return render_template(
        'modulo-materiaPrima/modificarMateriaPrima.html',
        form=form,
        materiaPrima=materiaPrima
    )


# DESACTIVAR
@materiaPrima_bp.route('/eliminarMateriaPrima/<int:id>', methods=['GET','POST'])
def eliminarMateriaPrima(id):

    materiaPrima = MateriaPrima.query.get_or_404(id)

    if request.method == 'POST':

        if materiaPrima.estatus == "inactivo":
            flash("Esta materia prima ya está desactivada.", "warning")
            return redirect(url_for('materiaPrima.materiaPrima'))

        materiaPrima.estatus = "inactivo"
        db.session.commit()

        flash("Materia prima desactivada correctamente.", "success")

        return redirect(url_for('materiaPrima.materiaPrima'))

    return render_template(
        'modulo-materiaPrima/eliminarMateriaPrima.html',
        materiaPrima=materiaPrima
    )