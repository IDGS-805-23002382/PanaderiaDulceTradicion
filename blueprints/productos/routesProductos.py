from flask import render_template, request, redirect, url_for, flash
from models import Producto, Categoria, db, Receta
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import os
from . import productos_bp

import forms
import base64

@productos_bp.app_template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ""

# LISTAR PRODUCTOS
@productos_bp.route('/productos')
def productos():

    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Producto.query

    # BUSCAR
    if buscar and buscar.strip() != "":
        query = query.filter(
            or_(
                Producto.nombre.ilike(f"%{buscar}%"),
            )
        )

    # FILTRAR POR ESTATUS
    if estatus:
        query = query.filter(Producto.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(Producto.nombre.asc())

    elif orden == "za":
        query = query.order_by(Producto.nombre.desc())

    productos = query.all()

    return render_template(
        "modulo-productos/modulo-productos.html",
        productos=productos
    )


@productos_bp.route('/agregarProducto', methods=['GET','POST'])
def agregarProducto():

    form = forms.ProductoForm()

    categorias = Categoria.query.all()
    form.id_categoria.choices = [(c.id_categoria, c.nombre) for c in categorias]

    if form.validate_on_submit():

        # VALIDAR SI YA EXISTE UN PRODUCTO CON EL MISMO NOMBRE
        producto_existente = Producto.query.filter_by(
            nombre=form.nombre.data
        ).first()

        if producto_existente:
            flash("Ya existe un producto con ese nombre.", "warning")
            return redirect(url_for('productos.agregarProducto'))

        imagen = request.files.get("imagen")

        imagen_bytes = None

        if imagen and imagen.filename != "":
            imagen_bytes = imagen.read()

        nuevo_producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            id_categoria=form.id_categoria.data,
            precio_venta=form.precio_venta.data,
            costo_unitario_estimado=form.costo_unitario_estimado.data,
            imagen_url=imagen_bytes,
            dias_caducidad=form.dias_caducidad.data,
            estatus=form.estatus.data
        )

        db.session.add(nuevo_producto)
        db.session.commit()

        flash("Producto agregado correctamente", "success")

        return redirect(url_for('productos.productos'))

    return render_template(
        'modulo-productos/agregarProducto.html',
        form=form
    )


@productos_bp.route('/detalleProducto/<int:id>')
def detalleProducto(id):

    producto = Producto.query.get_or_404(id)

    receta = Receta.query.filter_by(
        id_producto=id
    ).first()

    return render_template(
        'modulo-productos/detallesProducto.html',
        producto=producto,
        receta=receta
    )


@productos_bp.route('/editarProducto/<int:id>', methods=['GET','POST'])
def modificarProducto(id):

    producto = Producto.query.get_or_404(id)

    form = forms.ProductoForm(obj=producto)

    categorias = Categoria.query.all()
    form.id_categoria.choices = [(c.id_categoria, c.nombre) for c in categorias]

    if form.validate_on_submit():

        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.id_categoria = form.id_categoria.data
        producto.precio_venta = form.precio_venta.data
        producto.costo_unitario_estimado = form.costo_unitario_estimado.data
        producto.dias_caducidad = form.dias_caducidad.data
        producto.estatus = form.estatus.data

        # Obtener imagen nueva si el usuario sube una
        imagen = request.files.get("imagen")

        if imagen and imagen.filename != "":
            producto.imagen_url = imagen.read()

        db.session.commit()

        flash("Producto actualizado correctamente", "success")

        return redirect(url_for('productos.productos'))

    return render_template(
        'modulo-productos/modificarProducto.html',
        form=form,
        producto=producto
    )


# DESACTIVAR PRODUCTO
@productos_bp.route('/eliminarProducto/<int:id>', methods=['GET','POST'])
def eliminarProducto(id):

    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':

        if producto.estatus == "inactivo":
            flash("Este producto ya está desactivado.", "warning")
            return redirect(url_for('productos.productos'))

        producto.estatus = "inactivo"

        db.session.commit()

        flash("Producto desactivado correctamente.", "success")

        return redirect(url_for('productos.productos'))

    return render_template(
        'modulo-productos/eliminarProducto.html',
        producto=producto
    )