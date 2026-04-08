from flask import render_template, request, redirect, url_for, flash
from datetime import date, datetime
from models import Producto, Orden, db, Receta, DetalleOrden, MateriaPrima, Sucursal, InventarioMateriaPrima, MovimientoInventario, InventarioProducto, MovimientoInventarioProducto
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import forms
from . import ordenProduccion_bp

def convertir_a_base(cantidad, unidad):
    unidad = (unidad or '').lower().strip()

    if unidad in ['kg']:
        return cantidad * 1000  # kg → g
    elif unidad in ['l', 'litro', 'litros']:
        return cantidad * 1000  # l → ml
    else:
        return cantidad  # g, ml, pz

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
    form.id_sucursal.choices = [(s.id_sucursal, s.nombre) for s in Sucursal.query.all()]
    form.id_producto.choices = [(p.id_producto, p.nombre) for p in Producto.query.filter_by(estatus='activo').all()]
    
    # INICIALIZAR TODAS LAS VARIABLES EN 0 O VACÍO (se borrarán en cada GET)
    total_costo_orden = 0
    costo_unitario_pan = 0
    costo_por_receta = 0
    ingredientes_calculados = []
    receta_nombre = "Seleccione un producto"
    sucursal_nombre = ""
    piezas_totales = 0
    rendimiento_receta = 20
    
    hay_stock_suficiente = True
    faltantes = []

    # IMPORTANTE: Si es GET, mostrar formulario vacío
    if request.method == 'GET':
        # Resetear campos del formulario
        form.cantidad_recetas.data = None
        form.id_producto.data = None
        form.id_sucursal.data = None
        
        return render_template(
            'modulo-ordenes/agregarOrden.html',
            form=form,
            total_costo=0,
            costo_unitario=0,
            costo_por_receta=0,
            ingredientes=[],
            receta_nombre=receta_nombre,
            sucursal_nombre="",
            cantidad_recetas=0,
            piezas_totales=0,
            rendimiento_receta=rendimiento_receta,
            hay_stock_suficiente=True,
            faltantes=[]
        )

    # PROCESAR POST (solo si viene del formulario)
    if request.method == 'POST':
        id_prod = request.form.get('id_producto')
        id_suc = request.form.get('id_sucursal')
        cantidad_recetas = int(request.form.get('cantidad_recetas', 0))

        sucursal_obj = Sucursal.query.get(id_suc)
        if sucursal_obj:
            sucursal_nombre = sucursal_obj.nombre

        if id_prod and cantidad_recetas > 0:
            receta = Receta.query.filter_by(id_producto=id_prod).first()

            if receta:
                receta_nombre = receta.nombre
                rendimiento_receta = receta.rendimiento_piezas or 20
                piezas_totales = cantidad_recetas * rendimiento_receta

                total_receta = 0
                ingredientes_base = []

                # CALCULAR INGREDIENTES EN UNIDAD BASE
                for det in receta.ingredientes:
                    mp = det.materia
                    tipo = (det.tipo or '').lower().strip()

                    # Normalizar tipos
                    if tipo in ['gr','gramos']:
                        tipo = 'g'
                    elif tipo in ['kg','kilogramos']:
                        tipo = 'kg'
                    elif tipo in ['ml','mililitros']:
                        tipo = 'ml'
                    elif tipo in ['l','litros']:
                        tipo = 'l'
                    elif tipo in ['pieza','pza']:
                        tipo = 'pz'

                    cantidad = float(det.cantidad)

                    # CONVERTIR A BASE
                    cantidad_base = convertir_a_base(cantidad, tipo)

                    # Calcular costo según tipo
                    if tipo in ['g','kg','ml','l']:
                        costo_unit = mp.precio_por_gramo_ml
                    elif tipo == 'pz':
                        costo_unit = mp.precio_por_pieza
                    else:
                        costo_unit = float(mp.precio_unitario)

                    subtotal = cantidad_base * costo_unit
                    total_receta += subtotal

                    ingredientes_base.append({
                        "nombre": mp.nombre,
                        "id_materia": mp.id_materia,
                        "cantidad": cantidad_base,  # YA EN BASE
                        "tipo": tipo,
                        "tipo_original": det.tipo,
                        "costo_unit": costo_unit
                    })

                costo_por_receta = total_receta
                total_costo_orden = total_receta * cantidad_recetas
                costo_unitario_pan = total_receta / rendimiento_receta if rendimiento_receta > 0 else 0

                ingredientes_calculados = []
                faltantes = []
                hay_stock_suficiente = True

                # VALIDACIÓN DE STOCK (YA EN BASE)
                for ing in ingredientes_base:
                    cantidad_total = ing["cantidad"] * cantidad_recetas

                    inventario = InventarioMateriaPrima.query.filter_by(
                        id_materia=ing["id_materia"],
                        id_sucursal=id_suc
                    ).first()

                    stock_disponible = inventario.stock_actual if inventario else 0

                    # Mostrar stock en unidad legible para el usuario
                    if ing["tipo_original"] in ['l', 'litros']:
                        stock_mostrar = stock_disponible / 1000
                        unidad_mostrar = 'l'
                        necesario_mostrar = cantidad_total / 1000
                    elif ing["tipo_original"] in ['kg', 'kilogramos']:
                        stock_mostrar = stock_disponible / 1000
                        unidad_mostrar = 'kg'
                        necesario_mostrar = cantidad_total / 1000
                    else:
                        stock_mostrar = stock_disponible
                        unidad_mostrar = ing["tipo_original"]
                        necesario_mostrar = cantidad_total

                    if stock_disponible < cantidad_total:
                        hay_stock_suficiente = False
                        faltantes.append({
                            "nombre": ing["nombre"],
                            "necesario": round(necesario_mostrar, 2),
                            "disponible": round(stock_mostrar, 2),
                            "unidad": unidad_mostrar,
                            "deficit": round(necesario_mostrar - stock_mostrar, 2)
                        })

                    ingredientes_calculados.append({
                        "nombre": ing["nombre"],
                        "cantidad": round(necesario_mostrar, 2),
                        "unidad": unidad_mostrar,
                        "costo": round(cantidad_total * ing["costo_unit"], 2),
                        "stock_disponible": round(stock_mostrar, 2),
                        "stock_suficiente": stock_disponible >= cantidad_total,
                        "stock_real_base": stock_disponible,
                        "necesario_base": cantidad_total
                    })

                # CONFIRMAR ORDEN
                if 'confirmar' in request.form:
                    if not hay_stock_suficiente:
                        flash('No hay stock suficiente', 'error')
                        return render_template('modulo-ordenes/agregarOrden.html', 
                                              form=form, 
                                              ingredientes=ingredientes_calculados,
                                              total_costo=round(total_costo_orden,2),
                                              costo_unitario=round(costo_unitario_pan,2),
                                              costo_por_receta=round(costo_por_receta,2),
                                              receta_nombre=receta_nombre,
                                              sucursal_nombre=sucursal_nombre,
                                              cantidad_recetas=cantidad_recetas,
                                              piezas_totales=piezas_totales,
                                              rendimiento_receta=rendimiento_receta,
                                              hay_stock_suficiente=hay_stock_suficiente,
                                              faltantes=faltantes)

                    nueva_orden = Orden(
                        id_sucursal=id_suc,
                        id_usuario=1,  # Cambiar por usuario logueado
                        fecha_produccion=datetime.now().date(),
                        total_unidades=piezas_totales,
                        costo_total_estimado=total_costo_orden,
                        estatus='planeada',
                        notas=f"Producción de {cantidad_recetas} receta(s)"
                    )
                    db.session.add(nueva_orden)
                    db.session.flush()

                    detalle = DetalleOrden(
                        id_orden=nueva_orden.id_orden,
                        id_producto=id_prod,
                        cantidad=piezas_totales,
                        cantidad_recetas=cantidad_recetas,
                        costo_unitario_produccion=costo_unitario_pan,
                        subtotal_costo=total_costo_orden
                    )
                    db.session.add(detalle)

                    # DESCONTAR INVENTARIO (USANDO UNIDAD BASE)
                    for ing in ingredientes_base:
                        cantidad_total_base = ing["cantidad"] * cantidad_recetas

                        inventario = InventarioMateriaPrima.query.filter_by(
                            id_materia=ing["id_materia"],
                            id_sucursal=id_suc
                        ).first()

                        if inventario:
                            inventario.stock_actual -= cantidad_total_base

                            movimiento = MovimientoInventario(
                                id_materia=ing["id_materia"],
                                id_sucursal=id_suc,
                                cantidad=-cantidad_total_base,
                                tipo='salida_produccion',
                                referencia=f'Orden #{nueva_orden.id_orden}',
                                fecha=datetime.now()
                            )
                            db.session.add(movimiento)

                    db.session.commit()
                    flash('Orden creada correctamente', 'success')
                    
                    # REDIRIGIR para evitar reenvío de datos al recargar
                    return redirect(url_for('ordenProduccion.agregarOrden'))

    return render_template(
        'modulo-ordenes/agregarOrden.html',
        form=form,
        total_costo=round(total_costo_orden,2),
        costo_unitario=round(costo_unitario_pan,2),
        costo_por_receta=round(costo_por_receta,2),
        ingredientes=ingredientes_calculados,
        receta_nombre=receta_nombre,
        sucursal_nombre=sucursal_nombre,
        cantidad_recetas=cantidad_recetas if 'cantidad_recetas' in locals() else 0,
        piezas_totales=piezas_totales,
        rendimiento_receta=rendimiento_receta,
        hay_stock_suficiente=hay_stock_suficiente,
        faltantes=faltantes
    )
    
    
@ordenProduccion_bp.route('/panel')
def panelCocina():
    ordenes_pendientes = Orden.query.filter_by(estatus='planeada').order_by(Orden.fecha_produccion.asc()).all()
    ordenes_preparacion = Orden.query.filter_by(estatus='preparacion').order_by(Orden.fecha_produccion.asc()).all()
    ordenes_canceladas = Orden.query.filter_by(estatus='cancelada').order_by(Orden.fecha_produccion.desc()).limit(20).all()
    
    return render_template('modulo-ordenes/panel.html', 
                         ordenes_pendientes=ordenes_pendientes,
                         ordenes_preparacion=ordenes_preparacion,
                         ordenes_canceladas=ordenes_canceladas)

@ordenProduccion_bp.route('/cambiar_estado/<int:id_orden>', methods=['POST'])
def cambiar_estado(id_orden):
    orden = Orden.query.get_or_404(id_orden)

    nuevo_estatus = request.form.get('estatus')

    if nuevo_estatus:
        # Si la orden se está completando
        if nuevo_estatus == 'completada' and orden.estatus != 'completada':
            
            # Obtener el detalle de la orden
            detalle = DetalleOrden.query.filter_by(id_orden=id_orden).first()
            
            if detalle:
                # Obtener o crear inventario para este producto en esta sucursal
                inventario = InventarioProducto.query.filter_by(
                    id_producto=detalle.id_producto,
                    id_sucursal=orden.id_sucursal
                ).first()
                
                if not inventario:
                    inventario = InventarioProducto(
                        id_producto=detalle.id_producto,
                        id_sucursal=orden.id_sucursal,
                        stock_actual=0,
                        stock_minimo=0
                    )
                    db.session.add(inventario)
                
                # Sumar las unidades producidas
                inventario.stock_actual += detalle.cantidad
                
                # Registrar movimiento en bitácora
                bitacora_movimiento = MovimientoInventarioProducto(
                    id_producto=detalle.id_producto,
                    id_sucursal=orden.id_sucursal,
                    cantidad=detalle.cantidad,
                    tipo='entrada_produccion',
                    referencia=f'Orden #{orden.id_orden}',
                    fecha=datetime.now()
                )
                db.session.add(bitacora_movimiento)
                
                flash(f'Se agregaron {detalle.cantidad} unidades al inventario', 'success')
        
        orden.estatus = nuevo_estatus

        if nuevo_estatus == 'cancelada':
            orden.motivo_cancelacion = request.form.get('motivo_cancelacion')

        db.session.commit()
        flash('Estado actualizado correctamente', 'success')

    return redirect(url_for('ordenProduccion.panelCocina'))

@ordenProduccion_bp.route('/detalle_orden/<int:id_orden>')
def detalle_orden(id_orden):
    # Obtener la orden con sus relaciones
    orden = Orden.query.get_or_404(id_orden)
    
    # Obtener el detalle de la orden
    detalle = DetalleOrden.query.filter_by(id_orden=id_orden).first()
    
    if not detalle:
        flash('No se encontraron detalles para esta orden', 'error')
        return redirect(url_for('ordenProduccion.listarOrdenes'))
    
    # Obtener la receta del producto
    receta = Receta.query.filter_by(id_producto=detalle.id_producto).first()
    
    # Calcular materia prima requerida
    materia_prima_detalle = []
    costo_total_materia_prima = 0
    
    if receta:
        for detalle_receta in receta.ingredientes:
            mp = detalle_receta.materia
            cantidad_por_receta = float(detalle_receta.cantidad)
            unidad = detalle_receta.tipo
            cantidad_total = cantidad_por_receta * detalle.cantidad_recetas
            
            # Determinar el precio según la unidad
            if unidad in ['pz', 'pieza', 'piezas']:
                # Para piezas, usar precio_por_pieza si existe
                costo_unitario = getattr(mp, 'precio_por_pieza', 0)
            else:
                # Para gramos, ml, etc., usar precio_por_gramo_ml
                costo_unitario = getattr(mp, 'precio_por_gramo_ml', 0)
            
            # Mostrar cantidades en unidades legibles
            if unidad in ['kg', 'kilogramos']:
                cantidad_mostrar = cantidad_total
                unidad_mostrar = 'kg'
            elif unidad in ['l', 'litro', 'litros']:
                cantidad_mostrar = cantidad_total
                unidad_mostrar = 'L'
            elif unidad in ['g', 'gramos', 'gr'] and cantidad_total >= 1000:
                cantidad_mostrar = cantidad_total / 1000
                unidad_mostrar = 'kg'
            elif unidad in ['ml', 'mililitros'] and cantidad_total >= 1000:
                cantidad_mostrar = cantidad_total / 1000
                unidad_mostrar = 'L'
            else:
                cantidad_mostrar = cantidad_total
                unidad_mostrar = unidad or 'unidad'
            
            subtotal = cantidad_total * costo_unitario
            
            materia_prima_detalle.append({
                'nombre': mp.nombre,
                'cantidad_por_receta': cantidad_por_receta,
                'unidad_por_receta': unidad,
                'cantidad_total': round(cantidad_mostrar, 2),
                'unidad_total': unidad_mostrar,
                'costo_unitario': costo_unitario,
                'subtotal': round(subtotal, 2)
            })
            
            costo_total_materia_prima += subtotal
    
    # Obtener información de la sucursal
    sucursal = Sucursal.query.get(orden.id_sucursal)
    
    # Obtener el producto
    producto = Producto.query.get(detalle.id_producto)
    
    return render_template(
        'modulo-ordenes/detalle_orden.html',
        orden=orden,
        detalle=detalle,
        producto=producto,
        sucursal=sucursal,
        materia_prima=materia_prima_detalle,
        costo_total_materia_prima=round(costo_total_materia_prima, 2)
    )
