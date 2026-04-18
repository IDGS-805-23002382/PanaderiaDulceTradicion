from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response, current_app
from models import db, Producto, Sucursal, InventarioProducto, MovimientoInventarioProducto
from flask_login import current_user, login_required
from bson.objectid import ObjectId
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message


ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('/agregar_al_carrito', methods=['POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def agregar_al_carrito():
    ids_seleccionados = request.form.getlist('id_producto[]')
    todas_cantidades = request.form.getlist('cantidad[]')
    todos_ids_maestros = request.form.getlist('todos_los_ids[]')

    carrito = session.get('carrito', {})

    for i, id_p in enumerate(todos_ids_maestros):
        if str(id_p) in ids_seleccionados:
            producto = Producto.query.get(int(id_p))
            if producto:
                inv = InventarioProducto.query.filter_by(id_producto=producto.id_producto, id_sucursal=1).first()
                
                try:
                    cantidad_pedida = int(todas_cantidades[i]) if int(todas_cantidades[i]) > 0 else 1
                except:
                    cantidad_pedida = 1

                if not inv or inv.stock_actual < cantidad_pedida:
                    flash(f"No hay suficiente stock de {producto.nombre}. Disponible: {inv.stock_actual if inv else 0}", "danger")
                    continue

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
    return redirect(url_for('ventas.ver_pago'))


@ventas_bp.route('/pago')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def ver_pago():
    carrito = session.get('carrito', {})
    productos_disponibles = Producto.query.filter_by(estatus='activo').all()
    total = sum(item['precio'] * item['cantidad'] for item in carrito.values())
    lista_sucursales = Sucursal.query.filter_by(estatus='activo').all()

    # Calcular total de piezas y tiempo de espera
    total_piezas = sum(item['cantidad'] for item in carrito.values())
    tiempo_espera = '2 horas' if total_piezas >= 20 else '30 minutos'

    return render_template('modulo-ventas/pago.html', 
                           carrito_pos=carrito, 
                           total=total, 
                           sucursales=lista_sucursales,
                           productos_catalogo=productos_disponibles,
                           total_piezas=total_piezas,
                           tiempo_espera=tiempo_espera)


@ventas_bp.route('/eliminar_del_carrito/<id_producto>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def eliminar_del_carrito(id_producto):
    carrito = session.get('carrito', {})
    if str(id_producto) in carrito:
        carrito.pop(str(id_producto))
        session['carrito'] = carrito
        session.modified = True
    return redirect(url_for('ventas.ver_pago'))


@ventas_bp.route('/finalizar_compra', methods=['POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def finalizar_compra():
    carrito = session.get('carrito', {})
    if not carrito:
        flash("Tu carrito está vacío", "warning")
        return redirect(url_for('home'))

    metodo_pago     = request.form.get('metodo_pago', 'No especificado')
    metodo_entrega  = request.form.get('metodo_entrega', 'sucursal') 
    direccion_envio = request.form.get('direccion_envio', '').strip()
    nombre_cliente = current_user.nombre_mostrable
    total           = sum(item['precio'] * item['cantidad'] for item in carrito.values())
    ID_SUCURSAL_ONLINE = int(request.form.get('id_sucursal'))

    # Validar que si eligió domicilio, haya ingresado dirección
    if metodo_entrega == 'domicilio' and not direccion_envio:
        flash("Por favor ingresa tu dirección de envío.", "danger")
        return redirect(url_for('ventas.ver_pago'))

    try:
        detalles_para_mongo = []
        for id_p, item in carrito.items():
            producto_id    = int(id_p)
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
                referencia=f'Venta Web - Cliente: {current_user.nombre_mostrable}',
                fecha=datetime.now()
            )
            db.session.add(movimiento)

            detalles_para_mongo.append({
                'id_producto':     producto_id,
                'nombre_producto': item['nombre'],
                'cantidad':        cantidad_vender,
                'precio_unitario': float(item['precio']),
                'subtotal':        float(item['precio'] * cantidad_vender)
            })

        # Documento de venta — incluye método de entrega y dirección si aplica
        venta_doc = {
            'id_usuario':      current_user.id_usuario,
            'nombre_cliente':  nombre_cliente,
            'fecha':           datetime.now(),
            'metodo_pago':     metodo_pago,
            'metodo_entrega':  metodo_entrega,
            'tipo':            'online',
            'estatus':         'completado',
            'total':           total,
            'detalles':        detalles_para_mongo
        }

        # Solo guardamos dirección si el cliente eligió domicilio
        if metodo_entrega == 'domicilio':
            venta_doc['direccion_envio'] = direccion_envio

        mongo = current_app.mongo
        mongo.db.ventas.insert_one(venta_doc)
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
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def historial_ventas():
    mongo = current_app.mongo
    if hasattr(current_user, 'id_rol') and current_user.id_rol == 1:
        ventas = list(mongo.db.ventas.find().sort('fecha', -1))
    else:
        ventas = list(mongo.db.ventas.find({'id_usuario': current_user.id_usuario}).sort('fecha', -1))
    return render_template('modulo-ventas/historial.html', ventas=ventas)

@ventas_bp.route('/mis-compras')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def mis_compras():
    mongo = current_app.mongo
    # Filtramos por el ID del usuario actual y que sean de tipo 'online'
    compras_cliente = mongo.db.ventas.find({
        'id_usuario': current_user.id_usuario,
        'tipo': 'online'
    }).sort('fecha', -1) # Ordenar de la más reciente a la más antigua
    
    return render_template('modulo-ventas/mis_compras.html', ventas=compras_cliente)

@ventas_bp.route('/detalle/<string:id_venta>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
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


@ventas_bp.route('/actualizar_cantidad', methods=['POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def actualizar_cantidad():
    id_producto = request.form.get('id_producto')
    try:
        nueva_cantidad = int(request.form.get('cantidad', 1))
    except (ValueError, TypeError):
        nueva_cantidad = 1

    carrito = session.get('carrito', {})

    if id_producto in carrito:
        inv = InventarioProducto.query.filter_by(
            id_producto=int(id_producto), 
            id_sucursal=1
        ).first()

        stock_disponible = inv.stock_actual if inv else 0

        if nueva_cantidad > stock_disponible:
            flash(f"Stock insuficiente. Solo hay {stock_disponible} disponibles.", "danger")
        elif nueva_cantidad <= 0:
            carrito.pop(id_producto)
            flash("Producto eliminado del pedido.", "info")
        else:
            carrito[id_producto]['cantidad'] = nueva_cantidad
        
        session['carrito'] = carrito
        session.modified = True

    return redirect(url_for('ventas.ver_pago'))


@ventas_bp.route('/eliminar_del_pago/<id_producto>')
@login_required
@login_required_with_message
@gerente_or_admin_required
def eliminar_del_pago(id_producto):
    carrito = session.get('carrito', {})
    if str(id_producto) in carrito:
        carrito.pop(str(id_producto))
        session['carrito'] = carrito
        session.modified = True
        flash("Producto eliminado del pedido", "info")
    return redirect(url_for('ventas.ver_pago'))


@ventas_bp.route('/ticket/cliente/<string:id_venta>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def ticket_cliente(id_venta):
    mongo = current_app.mongo
    try:
        venta = mongo.db.ventas.find_one({'_id': ObjectId(id_venta)})
        if not venta:
            flash("El ticket solicitado no existe.", "warning")
            return redirect(url_for('home'))
        return render_template('modulo-ventas/ticket_publico.html', venta=venta)
    except Exception as e:
        return "Enlace de ticket inválido", 400