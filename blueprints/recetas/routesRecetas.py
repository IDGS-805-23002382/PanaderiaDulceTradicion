from flask import render_template, request, redirect, url_for, flash
from models import Receta, Producto, DetalleReceta, MateriaPrima, db, DetalleReceta
from sqlalchemy import or_

from . import recetas_bp
import forms


# LISTAR RECETAS
@recetas_bp.route('/recetas')
def recetas():

    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Receta.query

    # BUSCAR
    if buscar and buscar.strip() != "":
        query = query.filter(
            Receta.nombre.ilike(f"%{buscar}%")
        )

    # FILTRAR POR ESTATUS
    if estatus:
        query = query.filter(Receta.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(Receta.nombre.asc())

    elif orden == "za":
        query = query.order_by(Receta.nombre.desc())

    recetas = query.all()

    return render_template(
        "modulo-recetas/modulo-recetas.html",
        recetas=recetas
    )


# AGREGAR RECETA
@recetas_bp.route('/agregarReceta', methods=['GET','POST'])
def agregarReceta():

    form = forms.RecetaForm()

    productos = Producto.query.all()
    form.id_producto.choices = [(p.id_producto, p.nombre) for p in productos]

    if form.validate_on_submit():

        # VALIDAR SI YA EXISTE
        receta_existente = Receta.query.filter_by(
            nombre=form.nombre.data
        ).first()

        if receta_existente:
            flash("Ya existe una receta con ese nombre.", "warning")
            return redirect(url_for('recetas.agregarReceta'))

        nueva_receta = Receta(
            id_producto=form.id_producto.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            rendimiento_piezas=form.rendimiento_piezas.data,
            estatus=form.estatus.data
        )

        db.session.add(nueva_receta)
        db.session.commit()

        flash("Receta agregada correctamente", "success")

        return redirect(url_for('recetas.recetas'))

    return render_template(
        'modulo-recetas/agregarReceta.html',
        form=form
    )


# DETALLE RECETA (MATERIAS PRIMAS)
@recetas_bp.route('/detalleReceta/<int:id>')
def detalleReceta(id):

    receta = Receta.query.get_or_404(id)

    ingredientes = DetalleReceta.query.filter_by(
        id_receta=id
    ).all()

    return render_template(
        'modulo-recetas/detalleReceta.html',
        receta=receta,
        ingredientes=ingredientes
    )


# EDITAR RECETA
@recetas_bp.route('/editarReceta/<int:id>', methods=['GET','POST'])
def modificarReceta(id):

    receta = Receta.query.get_or_404(id)

    form = forms.RecetaForm(obj=receta)

    productos = Producto.query.all()
    form.id_producto.choices = [(p.id_producto, p.nombre) for p in productos]

    if form.validate_on_submit():

        receta.id_producto = form.id_producto.data
        receta.nombre = form.nombre.data
        receta.descripcion = form.descripcion.data
        receta.rendimiento_piezas = form.rendimiento_piezas.data
        receta.estatus = form.estatus.data

        db.session.commit()

        flash("Receta actualizada correctamente", "success")

        return redirect(url_for('recetas.recetas'))

    return render_template(
        'modulo-recetas/modificarReceta.html',
        form=form,
        receta=receta
    )


# DESACTIVAR RECETA
@recetas_bp.route('/eliminarReceta/<int:id>', methods=['GET','POST'])
def eliminarReceta(id):

    receta = Receta.query.get_or_404(id)

    if request.method == 'POST':

        if receta.estatus == "inactivo":
            flash("Esta receta ya está desactivada.", "warning")
            return redirect(url_for('recetas.recetas'))

        receta.estatus = "inactivo"

        db.session.commit()

        flash("Receta desactivada correctamente.", "success")

        return redirect(url_for('recetas.recetas'))

    return render_template(
        'modulo-recetas/eliminarReceta.html',
        receta=receta
    )