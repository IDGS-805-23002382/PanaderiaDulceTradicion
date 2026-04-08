from datetime import datetime
from bson.objectid import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response, current_app
from models import Producto, Sucursal
from flask_login import current_user, login_required

ventasSucursal_bp = Blueprint('ventasSucursal', __name__)


@ventasSucursal_bp.route('/pos/seleccionar_sucursal', methods=['GET', 'POST'])
@login_required
def seleccionar_sucursal():
    if request.method == 'POST':
        id_sucursal = request.form.get('id_sucursal')
        session['pos_sucursal'] = int(id_sucursal)
        session.modified = True
        return redirect(url_for('ventasSucursal.pos'))

    sucursales = Sucursal.query.filter_by(estatus='activo').all()
    return render_template('modulo-pos/seleccionar_sucursal.html',
                           sucursales=sucursales)


@ventasSucursal_bp.route('/pos')
@login_required
def pos():
    if 'pos_sucursal' not in session:
        return redirect(url_for('ventasSucursal.seleccionar_sucursal'))

    sucursal = Sucursal.query.get(session['pos_sucursal'])
    productos = Producto.query.filter_by(estatus='activo').all()
    carrito_pos = session.get('carrito_pos', {})
    total = sum(item['precio'] * item['cantidad'] for item in carrito_pos.values())

    return render_template('modulo-pos/pos.html',
                           sucursal=sucursal,
                           productos=productos,
                           carrito_pos=carrito_pos,
                           total=total)


@ventasSucursal_bp.route('/pos/agregar', methods=['POST'])
@login_required
def pos_agregar():
    id_producto = request.form.get('id_producto')
    cantidad = int(request.form.get('cantidad', 1))

    producto = Producto.query.get(int(id_producto))
    if not producto:
        flash("Producto no encontrado", "danger")
        return redirect(url_for('ventasSucursal.pos'))

    carrito_pos = session.get('carrito_pos', {})
    id_str = str(id_producto)

    if id_str in carrito_pos:
        carrito_pos[id_str]['cantidad'] += cantidad
    else:
        carrito_pos[id_str] = {
            'nombre': producto.nombre,
            'precio': float(producto.precio_venta),
            'cantidad': cantidad,
            'id_producto': int(id_producto)
        }

    session['carrito_pos'] = carrito_pos
    session.modified = True
    return redirect(url_for('ventasSucursal.pos'))


@ventasSucursal_bp.route('/pos/eliminar/<id_producto>')
@login_required
def pos_eliminar(id_producto):
    carrito_pos = session.get('carrito_pos', {})
    carrito_pos.pop(str(id_producto), None)
    session['carrito_pos'] = carrito_pos
    session.modified = True
    return redirect(url_for('ventasSucursal.pos'))


@ventasSucursal_bp.route('/pos/registrar', methods=['POST'])
@login_required
def pos_registrar():
    carrito_pos = session.get('carrito_pos', {})

    if not carrito_pos:
        flash("El carrito está vacío", "warning")
        return redirect(url_for('ventasSucursal.pos'))

    id_sucursal  = session.get('pos_sucursal')
    metodo_pago  = request.form.get('metodo_pago')
    nombre_cliente = request.form.get('nombre_cliente', 'Cliente general')
    total = sum(item['cantidad'] * item['precio'] for item in carrito_pos.values())

    sucursal_obj = Sucursal.query.get(id_sucursal) if id_sucursal else None
    
    detalles = []
    for id_producto, datos in carrito_pos.items():
            producto = Producto.query.get(int(id_producto))
            detalles.append({
                'id_producto': int(id_producto),
                'nombre_producto': producto.nombre if producto else datos['nombre'],
                'cantidad': int(datos['cantidad']),
                'precio_unitario': float(datos['precio']),
                'subtotal': float(datos['precio']) * int(datos['cantidad'])
            })

    venta_doc = {
            'tipo': 'sucursal',                     
            'fecha': datetime.now(),
            'id_sucursal': int(id_sucursal) if id_sucursal else None,
            'nombre_sucursal': sucursal_obj.nombre if sucursal_obj else None,
            'id_usuario': current_user.id_usuario,
            'nombre_usuario': current_user.nombre,
            'nombre_cliente': nombre_cliente,
            'metodo_pago': metodo_pago,
            'total': total,
            'estatus': 'completada',
            'detalles': detalles
        }
    try:
        mongo = current_app.mongo
        resultado = mongo.db.ventas.insert_one(venta_doc)
        session.pop('carrito_pos', None)
        flash("Venta registrada exitosamente", "success")
        return redirect(url_for('ventasSucursal.pos_ticket', id_venta=str(resultado.inserted_id)))
    except Exception as e:
            flash(f"Error: {str(e)}" , "danger")
            return redirect(url_for('ventasSucursal.pos'))    


@ventasSucursal_bp.route('/pos/ticket/<string:id_venta>')
@login_required
def pos_ticket(id_venta):
    mongo = current_app.mongo
    venta = mongo.db.ventas.find_one({'_id': ObjectId(id_venta)})
    
    print(f"VENTA ENCONTRADA: {venta}")
    print(f"ID SUCURSAL: {venta.get('id_sucursal')}")
    print(f"TIPO: {type(venta.get('id_sucursal'))}")
    
    if not venta:
        flash("Venta no encontrada", "danger")
        return redirect(url_for('ventasSucursal.pos_ticket', id_venta=str(resultado.inserted_id)))
    
    id_suc = venta.get('id_sucursal')
    try:
        
        sucursal = Sucursal.query.get(int(id_suc)) if id_suc else None
    except (ValueError, TypeError):
        sucursal = None
        
    return render_template('modulo-pos/ticket.html',
                           venta=venta, sucursal=sucursal)


@ventasSucursal_bp.route('/pos/cambiar_sucursal')
@login_required
def cambiar_sucursal():
    session.pop('pos_sucursal', None)
    session.pop('carrito_pos', None)
    return redirect(url_for('ventasSucursal.seleccionar_sucursal'))