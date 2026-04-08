from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response, current_app
from models import Producto, Sucursal
from flask_login import current_user, login_required
from bson.objectid import ObjectId

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('/agregar_al_carrito', methods=['POST'])
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
                        'cantidad': cantidad,
                        'id_producto': int(id_p)
                    }

    session['carrito'] = carrito
    session.modified = True
    flash("Productos añadidos con éxito", "success")
    return redirect(url_for('ventas.ver_venta'))


@ventas_bp.route('/venta')
@login_required
def ver_venta():
    carrito = session.get('carrito', {})
    total = sum(item['precio'] * item['cantidad'] for item in carrito.values())
    sucursales = Sucursal.query.filter_by(estatus='activo').all()
    
    productos_carrito = {}
    for id_str, item in carrito.items():
        producto = Producto.query.get(int(id_str))
        if producto:
            productos_carrito[id_str] = {
                **item,
                'id_producto': int(id_str),
                'imagen_url': producto.imagen_url if producto else None
            }
    return render_template('modulo-ventas/pago.html',
                           carrito=productos_carrito,
                           total=total,
                           sucursales=sucursales,
                           current_user=current_user)


@ventas_bp.route('/registrar_venta', methods=['POST'])
@login_required
def registrar_venta():
    carrito = session.get('carrito', {})

    if not carrito:
        flash("El carrito está vacío", "warning")
        return redirect(url_for('ventas.ver_venta'))

    id_sucursal = request.form.get('id_sucursal')
    metodo_pago = request.form.get('metodo_pago')
    nombre_cliente = request.form.get('nombre_cliente', 'Cliente general')
    total = sum(item['cantidad'] * item['precio'] for item in carrito.values())


    detalle = []
    for id_producto, datos in carrito.items():
        producto = Producto.query.get(int(id_producto))
        detalle.append({
            'id_producto': int(id_producto),
            'nombre_producto': producto.nombre if producto else datos['nombre'],
            'cantidad': int(datos['cantidad']),
            'precio_unitario': float(datos['precio']),
            'subtotal': float(datos['precio']) * float(datos['cantidad'])
        })
        
    sucursal = Sucursal.query.get(int(id_sucursal)) if id_sucursal else None
    
    
  #Documento MongoDB
    venta_doc = {
        'tipo': 'online',
        'fecha': datetime.now(),
        'id_sucursal': int(id_sucursal) if id_sucursal else None,
        'nombre_sucursal': sucursal.nombre if sucursal else None,
        'id_usuario': current_user.id_usuario,
        'nombre_usuario': current_user.nombre,
        'nombre_cliente': nombre_cliente,
        'metodo_pago': metodo_pago,
        'total': total,
        'estatus': 'completada',
        'detalle': detalle
     }
    try:
        mongo = current_app.mongo
        resultado = mongo.db.ventas.insert_one(venta_doc)
        session.pop('carrito', None)
        flash("Venta registrada con éxito", "success")
        return redirect(url_for('catalogo',
                                id_venta=str(resultado.inserted_id)))

    except Exception as e:
        flash(f"Error al procesar la venta: {str(e)}", "danger")
        return redirect(url_for('ventas.ver_venta'))
    
    
@ventas_bp.route('/actualizar_cantidad/<int:id_producto>', methods=['POST'])
@login_required
def actualizar_cantidad(id_producto):
    nueva_cantidad = int(request.form.get('cantidad', 1))
    carrito = session.get('carrito', {})
    id_str = str(id_producto)
    
    if id_str in carrito:
        if nueva_cantidad <= 0:
            del carrito[id_str]
            flash("Producto eliminado", "info")
        else:
            carrito[id_str]['cantidad'] = nueva_cantidad
            flash("Cantidad actualizada", "success")
    else:
        flash("Producto no encontrado", "warning")
    
    session['carrito'] = carrito
    session.modified = True
    return redirect(url_for('ventas.ver_venta'))


@ventas_bp.route('/historial')
@login_required
def historial_ventas():
    mongo = current_app.mongo
    
    if current_user.rol.nombre == 'admin':
        ventas = list(mongo.db.ventas.find().sort('fecha', -1))
    else:
        ventas = list(mongo.db.ventas.find({'id_usuario': current_user.id_usuario}).sort('fecha', -1))
    return render_template('modulo-ventas/historial.html',
                           ventas=ventas,
                           current_user=current_user)


@ventas_bp.route('/detalle/<string:id_venta>')
@login_required
def ver_detalle_venta(id_venta):
    mongo = current_app.mongo
    
    try:
        venta = mongo.db.ventas.find_one({'_id': ObjectId(id_venta)})
    except:
        flash("ID de venta es invalido", "danger")
        return redirect(url_for('ventas.historial_ventas'))

    if not venta:
        flash("Venta no encontrada", "advertencia")
        return redirect(url_for('ventas.historial_ventas'))
    
    if venta['id_usuario'] != current_user.id_usuario and current_user.rol.nombre != 'admin':
        return redirect(url_for('ventas.historial_ventas'))
    return render_template('modulo-ventas/detalle_venta.html', venta=venta)
    

@ventas_bp.route('/producto_imagen/<int:id>')
def producto_imagen(id):
    producto = Producto.query.get_or_404(id)
    if producto.imagen_url:
        return Response(producto.imagen_url, mimetype='image/jpeg')
    return "", 404


@ventas_bp.route('/eliminar_del_carrito/<int:id_producto>')
@login_required
def eliminar_del_carrito(id_producto):
    carrito = session.get('carrito', {})
    id_str = str(id_producto)
    
    if id_str in carrito:
        del carrito[id_str]
        session['carrito'] = carrito
        session.modified = True
        flash("Producto eliminado del carrito", "success")
    else:
        flash("Producto no encontrado en el carrito", "warning")
    
    return redirect(url_for('ventas.ver_venta'))