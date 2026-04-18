from datetime import datetime
from bson.objectid import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response, current_app, jsonify
from models import Producto, Sucursal, InventarioProducto, MovimientoInventarioProducto, db
from flask_login import current_user, login_required
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message

ventasSucursal_bp = Blueprint('ventasSucursal', __name__)


@ventasSucursal_bp.route('/pos/seleccionar_sucursal', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
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
@login_required_with_message
@gerente_or_admin_required
@empleado_required
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
@login_required_with_message
@gerente_or_admin_required
@empleado_required
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
@login_required_with_message
@gerente_or_admin_required
def pos_eliminar(id_producto):
    carrito_pos = session.get('carrito_pos', {})
    carrito_pos.pop(str(id_producto), None)
    session['carrito_pos'] = carrito_pos
    session.modified = True
    return redirect(url_for('ventasSucursal.pos'))


@ventasSucursal_bp.route('/pos/registrar', methods=['POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def pos_registrar():
    carrito_pos = session.get('carrito_pos', {})

    if not carrito_pos:
        flash("El carrito está vacío", "warning")
        return redirect(url_for('ventasSucursal.pos'))

    id_sucursal    = session.get('pos_sucursal')
    metodo_pago    = request.form.get('metodo_pago')
    nombre_cliente = request.form.get('nombre_cliente', 'Cliente mostrador').strip() or 'Cliente mostrador'
    total          = sum(item['cantidad'] * item['precio'] for item in carrito_pos.values())

    # --- VALIDACIÓN, DESCUENTO Y REGISTRO DE MOVIMIENTOS EN MYSQL ---
    try:
        for id_p, item in carrito_pos.items():
            producto_id       = int(id_p)
            cantidad_a_vender = int(item['cantidad'])

            inventario = InventarioProducto.query.filter_by(
                id_producto=producto_id,
                id_sucursal=id_sucursal
            ).first()

            if not inventario:
                flash(f"Error: El producto {item['nombre']} no tiene inventario en esta sucursal.", "danger")
                return redirect(url_for('ventasSucursal.pos'))

            if inventario.stock_actual < cantidad_a_vender:
                flash(f"Error: Stock insuficiente para {item['nombre']}. Solo quedan {inventario.stock_actual} unidades.", "danger")
                return redirect(url_for('ventasSucursal.pos'))

            # Descontar stock
            inventario.stock_actual -= cantidad_a_vender

            # Registrar movimiento
            movimiento = MovimientoInventarioProducto(
                id_producto=producto_id,
                id_sucursal=id_sucursal,
                tipo='salida_venta',
                cantidad=cantidad_a_vender,
                referencia=f'Venta POS - {nombre_cliente}',
                fecha=datetime.now()
            )
            db.session.add(movimiento)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar inventario: {str(e)}", "danger")
        return redirect(url_for('ventasSucursal.pos'))

    # --- PREPARAR DETALLES PARA MONGODB ---
    sucursal_obj = Sucursal.query.get(id_sucursal) if id_sucursal else None

    detalles = []
    for id_p, datos in carrito_pos.items():
        producto = Producto.query.get(int(id_p))
        detalles.append({
            'id_producto':     int(id_p),
            'nombre_producto': producto.nombre if producto else datos['nombre'],
            'cantidad':        int(datos['cantidad']),
            'precio_unitario': float(datos['precio']),
            'subtotal':        float(datos['precio']) * int(datos['cantidad'])
        })

    # --- DOCUMENTO LIMPIO PARA MONGODB ---
    venta_doc = {
        'tipo':             'sucursal',
        'id_empleado':      current_user.id_usuario,
        'nombre_empleado':  current_user.nombre_mostrable,   # ← quién vendió
        'id_usuario':       current_user.id_usuario,
        'nombre_cliente':   nombre_cliente,                  # ← a quién se vendió
        'total':            total,
        'fecha':            datetime.now(),
        'id_sucursal':      int(id_sucursal) if id_sucursal else None,
        'nombre_sucursal':  sucursal_obj.nombre if sucursal_obj else None,
        'metodo_pago':      metodo_pago,
        'estatus':          'completada',
        'detalles':         detalles
    }

    try:
        mongo = current_app.mongo
        resultado = mongo.db.ventas.insert_one(venta_doc)
        session.pop('carrito_pos', None)
        flash("Venta registrada exitosamente", "success")
        return redirect(url_for('ventasSucursal.pos_ticket', id_venta=str(resultado.inserted_id)))
    except Exception as e:
        flash(f"Error al registrar en MongoDB: {str(e)}", "danger")
        return redirect(url_for('ventasSucursal.pos'))


@ventasSucursal_bp.route('/pos/ticket/<string:id_venta>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def pos_ticket(id_venta):
    mongo = current_app.mongo
    venta = mongo.db.ventas.find_one({'_id': ObjectId(id_venta)})

    if not venta:
        flash("Venta no encontrada", "danger")
        return redirect(url_for('ventasSucursal.pos'))

    id_suc = venta.get('id_sucursal')
    try:
        sucursal = Sucursal.query.get(int(id_suc)) if id_suc else None
    except (ValueError, TypeError):
        sucursal = None

    return render_template('modulo-pos/ticket.html',
                           venta=venta, sucursal=sucursal)


@ventasSucursal_bp.route('/pos/cambiar_sucursal')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def cambiar_sucursal():
    session.pop('pos_sucursal', None)
    session.pop('carrito_pos', None)
    return redirect(url_for('ventasSucursal.seleccionar_sucursal'))