from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from models import Producto, Orden, db, Receta, DetalleOrden, MateriaPrima, Sucursal, InventarioMateriaPrima, MovimientoInventario
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

    # 🔹 Selects
    form.id_sucursal.choices = [(s.id_sucursal, s.nombre) for s in Sucursal.query.all()]
    productos = Producto.query.filter_by(estatus='activo').all()
    form.id_producto.choices = [(p.id_producto, p.nombre) for p in productos]

    receta_nombre = "Seleccione un producto"
    total_costo = 0
    costo_unitario = 0
    ingredientes_calculados = []
    inventario_ok = True

    if request.method == 'POST':
        id_prod = request.form.get('id_producto')
        cantidad = int(request.form.get('cantidad', 0))
        id_sucursal = request.form.get('id_sucursal')

        if id_prod:
            receta = Receta.query.filter_by(id_producto=id_prod, estatus='activo').first()

            if receta:
                receta_nombre = receta.nombre

                if cantidad > 0:

                    # 🔥 BASE: rendimiento (ej: 20 piezas)
                    veces_receta = cantidad / float(receta.rendimiento_piezas or 1)

                    total_costo = 0
                    inventario_ok = True
                    ingredientes_calculados = []

                    for ingrediente in receta.ingredientes:

                        cantidad_total = float(ingrediente.cantidad) * veces_receta
                        costo = cantidad_total * float(ingrediente.materia.precio_unitario)

                        inventario = InventarioMateriaPrima.query.filter_by(
                            id_materia=ingrediente.id_materia,
                            id_sucursal=id_sucursal
                        ).first()

                        stock = inventario.stock_actual if inventario else 0
                        suficiente = stock >= cantidad_total

                        if not suficiente:
                            inventario_ok = False

                        ingredientes_calculados.append({
                            "nombre": ingrediente.materia.nombre,
                            "cantidad": round(cantidad_total, 2),
                            "tipo": ingrediente.materia.unidad_contenido,
                            "stock": round(stock, 2),
                            "costo": round(costo, 2),
                            "suficiente": suficiente
                        })

                        total_costo += costo

                    costo_unitario = total_costo / cantidad if cantidad > 0 else 0

            else:
                receta_nombre = "Sin receta"

        # 🔥 CONFIRMAR PRODUCCIÓN
        if 'btn_confirmar' in request.form and form.validate_on_submit():

            if not inventario_ok:
                flash("No hay suficiente inventario", "error")
                return redirect(url_for('ordenProduccion.agregarOrden'))

            nueva_orden = Orden(
                id_sucursal=form.id_sucursal.data,
                id_usuario=1,
                fecha_produccion=datetime.now().date(),
                total_unidades=cantidad,
                costo_total_estimado=total_costo,
                estatus='planeada'
            )

            db.session.add(nueva_orden)
            db.session.flush()

            detalle = DetalleOrden(
                id_orden=nueva_orden.id_orden,
                id_producto=id_prod,
                cantidad=cantidad,
                costo_unitario_produccion=costo_unitario,
                subtotal_costo=total_costo
            )

            db.session.add(detalle)

            # 🔻 Descontar inventario
            for ing in ingredientes_calculados:

                materia = MateriaPrima.query.filter_by(nombre=ing["nombre"]).first()

                inventario = InventarioMateriaPrima.query.filter_by(
                    id_materia=materia.id_materia,
                    id_sucursal=form.id_sucursal.data
                ).first()

                if inventario:
                    inventario.stock_actual -= ing["cantidad"]

                    movimiento = MovimientoInventario(
                        id_materia=materia.id_materia,
                        id_sucursal=form.id_sucursal.data,
                        tipo='salida',
                        cantidad=ing["cantidad"],
                        referencia=f'Orden {nueva_orden.id_orden}'
                    )

                    db.session.add(movimiento)

            db.session.commit()

            flash("Orden generada correctamente", "success")
            return redirect(url_for('ordenProduccion.listarOrdenes'))

    return render_template(
        'modulo-ordenes/agregarOrden.html',
        form=form,
        productos=productos,
        receta_nombre=receta_nombre,
        total_costo=total_costo,
        costo_unitario=costo_unitario,
        ingredientes=ingredientes_calculados,
        inventario_ok=inventario_ok
    )