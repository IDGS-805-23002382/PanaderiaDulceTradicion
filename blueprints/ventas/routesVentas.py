from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response, current_app
# Importamos los modelos necesarios, incluyendo InventarioProducto
from models import db, Producto, Sucursal, InventarioProducto
from flask_login import current_user, login_required
from bson.objectid import ObjectId

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('/agregar_al_carrito', methods=['POST'])
@login_required
def agregar_al_carrito():
    ids_seleccionados = request.form.getlist('id_producto[]')
    todas_cantidades  = request.form.getlist('cantidad[]')
    todos_ids_maestros = request.form.getlist('todos_los_ids[]')

    carrito = session.get('carrito', {})

    for i, id_p in enumerate(todos_ids_maestros):
        if str(id_p) in ids_seleccionados:
            producto = Producto.query.get(int(id_p))
            if producto:
                cant_val = todas_cantidades[i] if i < len(todas_cantidades) else '1'
                try:
                    cantidad = int(cant_val) if int(cant_val) > 0 else 1
                except:
                    cantidad = 1

                id_str = str(id_p)
                if id_str in carrito:
                    carrito[id_str]['cantidad'] += cantidad
                else:
                    carrito[id_str] = {
                        'nombre': producto.nombre,
                        'precio': float(producto.precio_venta),
                        'cantidad': cantidad
                    }
    
    session['carrito'] = carrito
    flash("Productos agregados al carrito", "success")
    return redirect(url_for('ventas.ver_carrito'))

@ventas_bp.route('/carrito')
@login_required
def ver_carrito():
    carrito = session.get('carrito', {})
    total = sum(item['precio'] * item['cantidad'] for item in carrito.values())
    return render_template('modulo-ventas/carrito.html', carrito=carrito, total=total)

@ventas_bp.route('/finalizar_venta', methods=['POST'])
@login_required
def finalizar_venta():
    mongo = current_app.mongo
    carrito = session.get('carrito', {})

    if not carrito:
        flash("El carrito está vacío", "danger")
        return redirect(url_for('ventas.ver_carrito'))

    # --- INTEGRACIÓN CON INVENTARIO ---
    
    # 1. Validar stock en la tabla InventarioProducto antes de procesar
    for id_p, item in carrito.items():
        # Buscamos el registro en la tabla de inventarios para este producto
        # (Se toma el primero disponible para simplificar la validación)
        inv = InventarioProducto.query.filter_by(id_producto=int(id_p)).first()
        
        if not inv:
            flash(f"El producto {item['nombre']} no tiene registro de inventario.", "danger")
            return redirect(url_for('ventas.ver_carrito'))
        
        if inv.stock_actual < item['cantidad']:
            flash(f"No hay stock suficiente de {item['nombre']}. Disponible: {inv.stock_actual}", "danger")
            return redirect(url_for('ventas.ver_carrito'))

    # 2. Si hay stock suficiente, procedemos a descontar y preparar datos para Mongo
    detalles_mongo = []
    total_venta = 0

    for id_p, item in carrito.items():
        inv = InventarioProducto.query.filter_by(id_producto=int(id_p)).first()
        
        # Descontar del stock real en MySQL
        inv.stock_actual -= item['cantidad']
        
        subtotal = item['precio'] * item['cantidad']
        total_venta += subtotal
        detalles_mongo.append({
            'id_producto': int(id_p),
            'nombre': item['nombre'],
            'cantidad': item['cantidad'],
            'precio_unitario': item['precio'],
            'subtotal': subtotal
        })

    # Guardar cambios en la base de datos MySQL
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar el inventario: {str(e)}", "danger")
        return redirect(url_for('ventas.ver_carrito'))

    # 3. Guardar la venta en MongoDB
    nueva_venta = {
        'id_usuario': current_user.id_usuario,
        'usuario_nombre': current_user.nombre,
        'fecha': datetime.now(),
        'detalles': detalles_mongo,
        'total': total_venta,
        'tipo': 'presencial'
    }

    resultado = mongo.db.ventas.insert_one(nueva_venta)
    
    # Limpiar carrito
    session.pop('carrito', None)
    flash(f"Venta realizada con éxito. Total: ${total_venta}", "success")
    
    return redirect(url_for('ventas.ver_detalle_venta', id_venta=str(resultado.inserted_id)))

@ventas_bp.route('/historial')
@login_required
def historial_ventas():
    mongo = current_app.mongo
    # Ajuste de roles según tu modelo de Usuario
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

@ventas_bp.route('/eliminar_del_carrito/<int:id_producto>')
@login_required
def eliminar_del_carrito(id_producto):
    carrito = session.get('carrito', {})
    id_str = str(id_producto)
    if id_str in carrito:
        session.modified = True
        del carrito[id_str]
        flash("Producto eliminado del carrito", "info")
    return redirect(url_for('ventas.ver_carrito'))