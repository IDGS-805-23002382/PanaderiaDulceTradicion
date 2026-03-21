from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from models import Producto, Orden, db, Receta, DetalleOrden, MateriaPrima
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import forms
from . import ordenProduccion_bp

@ordenProduccion_bp.route('/ordenes')
def listarOrdenes():

    ordenes = Orden.query.all()

    return render_template(
        'modulo-ordenes/modulo-ordenes.html',
        ordenes=ordenes
    )

@ordenProduccion_bp.route('/agregarOrden', methods=['GET', 'POST'])
def agregarOrden():

    form = forms.OrdenForm()

    productos = Producto.query.filter_by(estatus='activo').all()

    # llenar select
    form.id_producto.choices = [
        (p.id_producto, p.nombre)
        for p in productos
    ]

    if form.validate_on_submit():

        producto = Producto.query.get(form.id_producto.data)
        cantidad = form.cantidad.data

        receta = Receta.query.filter_by(
            id_producto=producto.id_producto,
            estatus='activo'
        ).first()

        if not receta:
            flash("El producto no tiene receta activa", "warning")
            return redirect(url_for('ordenProduccion.agregarOrden'))

        # validar stock
        for ingrediente in receta.ingredientes:

            consumo = float(ingrediente.cantidad_por_pieza) * cantidad
            materia = MateriaPrima.query.get(ingrediente.id_materia)

            if materia.stock_actual < consumo:
                flash(f"No hay suficiente {materia.nombre}", "danger")
                return redirect(url_for('ordenProduccion.agregarOrden'))

        nueva_orden = Orden(
            cliente_nombre=form.cliente_nombre.data,
            cliente_telefono=form.cliente_telefono.data,
            fecha=datetime.utcnow(),
            cajera="Cajera 1",
            total=0
        )

        db.session.add(nueva_orden)
        db.session.flush()

        precio = float(producto.precio_venta)
        subtotal = precio * cantidad

        detalle = DetalleOrden(
            id_orden=nueva_orden.id_orden,
            id_producto=producto.id_producto,
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=subtotal
        )

        db.session.add(detalle)
        nueva_orden.total = subtotal

        # descontar materia
        for ingrediente in receta.ingredientes:

            consumo = float(ingrediente.cantidad_por_pieza) * cantidad
            materia = MateriaPrima.query.get(ingrediente.id_materia)
            materia.stock_actual -= consumo

        db.session.commit()

        flash("Orden registrada correctamente", "success")
        return redirect(url_for('ordenProduccion.agregarOrden'))

    return render_template(
        'modulo-ordenes/agregarOrden.html',
        form=form,
        productos=productos
    )