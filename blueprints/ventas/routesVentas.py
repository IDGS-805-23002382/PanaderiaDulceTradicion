from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response, current_app
from models import db, Producto, Sucursal, InventarioProducto, MovimientoInventarioProducto
from flask_login import current_user, login_required
from bson.objectid import ObjectId

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('/agregar_al_carrito', methods=['POST'])
@login_required
def agregar_al_carrito():
    ids_seleccionados = request.form.getlist('id_producto[]')
    todas_cantidades = request.form.getlist('cantidad[]')
    todos_ids_maestros = request.form.getlist('todos_los_ids[]')

    carrito = session.get('carrito', {})

    for i, id_p in enumerate(todos_ids_maestros):
        if str(id_p) in ids_seleccionados:
            producto = Producto.query.get(int(id_p))
            if producto:
                # VALIDACIÓN DE STOCK AQUÍ
                inv = InventarioProducto.query.filter_by(id_producto=producto.id_producto, id_sucursal=1).first()
                
                try:
                    cantidad_pedida = int(todas_cantidades[i]) if int(todas_cantidades[i]) > 0 else 1
                except:
                    cantidad_pedida = 1

                # Si no hay inventario o la cantidad supera el stock
                if not inv or inv.stock_actual < cantidad_pedida:
                    flash(f"No hay suficiente stock de {producto.nombre}. Disponible: {inv.stock_actual if inv else 0}", "danger")
                    continue # Salta este producto y sigue con el siguiente

                # Si pasa la validación, se agrega al carrito
                id_str = str(id_p)
                if id_str in carrito:
                    carrito[id_str]['cantidad'] += cantidad_pedida
                else:
                    carrito[id_str] = {
                        'nombre': producto.nombre,
                        'precio': float(producto.precio_venta),
                        'cantidad': cantidad_pedida
                    }
                flash(f"{producto.nombre} agregado al carrito", "success")

    session['carrito'] = carrito
    session.modified = True
    return redirect(url_for('catalogo'))

@ventas_bp.route('/pago')
@login_required
def ver_pago():
    carrito = session.get('carrito', {})
    
    if not carrito:
        flash("Tu carrito está vacío, elige algunos productos primero.", "warning")
        return redirect(url_for('catalogo'))
    
    total = sum(item['precio'] * item['cantidad'] for item in carrito.values())
    sucursal = Sucursal.query.get(1)
    return render_template('modulo-ventas/pago.html', carrito=carrito, total=total, sucursal=sucursal)

@ventas_bp.route('/eliminar_del_carrito/<id_producto>')
@login_required
def eliminar_del_carrito(id_producto):
    carrito = session.get('carrito', {})
    if str(id_producto) in carrito:
        carrito.pop(str(id_producto))
        session['carrito'] = carrito
        session.modified = True
    return redirect(url_for('ventas.ver_pago'))

@ventas_bp.route('/finalizar_compra', methods=['POST'])
@login_required
def finalizar_compra():
    carrito = session.get('carrito', {})
    if not carrito:
        flash("Tu carrito está vacío", "warning")
        return redirect(url_for('home'))

    metodo_pago = request.form.get('metodo_pago', 'No especificado')
    nombre_cliente = request.form.get('nombre_cliente', 'Cliente Web')
    total = sum(item['precio'] * item['cantidad'] for item in carrito.values())
    ID_SUCURSAL_ONLINE = 1 

    try:
        detalles_para_mongo = []
        for id_p, item in carrito.items():
            producto_id = int(id_p)
            cantidad_vender = int(item['cantidad'])

            inventario = InventarioProducto.query.filter_by(
                id_producto=producto_id, 
                id_sucursal=ID_SUCURSAL_ONLINE
            ).first()

            if not inventario or inventario.stock_actual < cantidad_vender:
                stock_disp = inventario.stock_actual if inventario else 0
                flash(f"Stock insuficiente para {item['nombre']}. Disponible: {stock_disp}", "danger")
                db.session.rollback()
                return redirect(url_for('ventas.ver_pago'))

            inventario.stock_actual -= cantidad_vender

            movimiento = MovimientoInventarioProducto(
                id_producto=producto_id,
                id_sucursal=ID_SUCURSAL_ONLINE,
                tipo='salida_venta_online',
                cantidad=cantidad_vender,
                referencia=f'Venta Web - Cliente: {current_user.nombre}',
                fecha=datetime.now()
            )
            db.session.add(movimiento)

            detalles_para_mongo.append({
                'id_producto': producto_id,
                'nombre_producto': item['nombre'],
                'cantidad': cantidad_vender,
                'precio_unitario': float(item['precio']),
                'subtotal': float(item['precio'] * cantidad_vender)
            })

            venta_doc = {
                    'id_usuario': current_user.id_usuario,
                    'nombre_cliente': nombre_cliente,
                    'fecha': datetime.now(),
                    'metodo_pago': metodo_pago, 
                    'tipo': 'online',
                    'estatus': 'completado',
                    'total': total,
                    'detalles': detalles_para_mongo
                }

        mongo = current_app.mongo
        resultado = mongo.db.ventas.insert_one(venta_doc)
        db.session.commit()

        session.pop('carrito', None)
    
        flash("¡Gracias por tu compra!", "success")
        return redirect(url_for('catalogo'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error crítico: {str(e)}", "danger")
        return redirect(url_for('ventas.ver_pago'))

@ventas_bp.route('/historial')
@login_required
def historial_ventas():
    mongo = current_app.mongo
    if hasattr(current_user, 'id_rol') and current_user.id_rol == 1:
        ventas = list(mongo.db.ventas.find().sort('fecha', -1))
    else:
        ventas = list(mongo.db.ventas.find({'id_usuario': current_user.id_usuario}).sort('fecha', -1))
    return render_template('modulo-ventas/historial.html', ventas=ventas)

@ventas_bp.route('/detalle/<string:id_venta>')
@login_required
def ver_detalle_venta(id_venta):
    mongo = current_app.mongo
    try:
        venta = mongo.db.ventas.find_one({'_id': ObjectId(id_venta)})
    except:
        flash("ID de venta inválido", "danger")
        return redirect(url_for('ventas.historial_ventas'))
    if not venta:
        flash("Venta no encontrada", "warning")
        return redirect(url_for('ventas.historial_ventas'))
    return render_template('modulo-ventas/detalle_venta.html', venta=venta)

@ventas_bp.route('/ticket/cliente/<string:id_venta>')
def ticket_cliente(id_venta):
    mongo = current_app.mongo
    try:
        # Buscamos la venta en MongoDB
        venta = mongo.db.ventas.find_one({'_id': ObjectId(id_venta)})
        
        if not venta:
            flash("El ticket solicitado no existe.", "warning")
            return redirect(url_for('home')) # O a tu página principal
            
        return render_template('modulo-ventas/ticket_publico.html', venta=venta)
    except Exception as e:
        return "Enlace de ticket inválido", 400