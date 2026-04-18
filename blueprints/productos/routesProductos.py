from flask import render_template, request, redirect, url_for, flash, Response
from models import Producto, Categoria, db, Receta, InventarioProducto, Sucursal, MovimientoInventarioProducto, DetalleCompra 
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import os
from . import productos_bp
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message
from flask_login import login_required
import forms
import base64

# blueprints/productos/routesProductos.py (agregar al final del archivo)

def calcular_valores_producto(id_producto):
    """
    Calcula automáticamente:
    - Costo unitario (desde receta)
    - Precio de venta (costo + 60%)
    """
    from models import DetalleCompra, Compra
    
    producto = Producto.query.get(id_producto)
    if not producto or not producto.receta:
        return False
    
    receta = producto.receta
    total_costo = 0
    
    for detalle in receta.ingredientes:
        materia = detalle.materia
        cantidad = float(detalle.cantidad)
        tipo = (detalle.tipo or '').lower().strip()
        
        # Obtener costo unitario de la última compra
        ultima_compra = db.session.query(DetalleCompra.precio_unitario_compra)\
            .join(Compra)\
            .filter(DetalleCompra.id_materia == materia.id_materia)\
            .filter(Compra.estado == 'recibida')\
            .order_by(Compra.fecha_entrega.desc())\
            .first()
        
        costo_unitario = float(ultima_compra[0]) if ultima_compra and ultima_compra[0] else 0
        
        # Convertir según tipo de unidad
        if tipo in ['kg', 'kilogramo', 'kilogramos']:
            cantidad = cantidad * 1000
        elif tipo in ['l', 'litro', 'litros']:
            cantidad = cantidad * 1000
        
        total_costo += cantidad * costo_unitario
    
    rendimiento = receta.rendimiento_piezas or 1
    costo_por_pieza = round(total_costo / rendimiento, 2) if rendimiento > 0 else 0
    
    # Actualizar producto
    producto.costo_unitario_estimado = costo_por_pieza
    producto.precio_venta = round(costo_por_pieza * 1.6, 2)
    
    db.session.commit()
    return True

@productos_bp.app_template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ""

# LISTAR PRODUCTOS
@productos_bp.route('/productos')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def productos():

    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Producto.query

    if buscar and buscar.strip() != "":
        query = query.filter(
            Producto.nombre.ilike(f"%{buscar}%")
        )

    if estatus:
        query = query.filter(Producto.estatus == estatus)

    if orden == "az":
        query = query.order_by(Producto.nombre.asc())
    elif orden == "za":
        query = query.order_by(Producto.nombre.desc())

    productos = query.all()

    cambios = False

    for p in productos:
        # Solo recalcular si tiene receta
        if p.receta and p.receta.ingredientes:
            total_costo = 0
            rendimiento = p.receta.rendimiento_piezas or 1
            
            for detalle in p.receta.ingredientes:
                materia = detalle.materia
                cantidad = float(detalle.cantidad)
                tipo = (detalle.tipo or '').lower().strip()
                
                # 🔥 OBTENER COSTO UNITARIO DE LA MATERIA PRIMA
                costo_unitario = obtener_costo_materia_prima(materia.id_materia)
                
                if costo_unitario == 0:
                    # Si no hay costo, intentar obtener de la última compra
                    ultima_compra = db.session.query(DetalleCompra.precio_unitario_compra)\
                        .filter(DetalleCompra.id_materia == materia.id_materia)\
                        .order_by(DetalleCompra.id_detalle.desc())\
                        .first()
                    
                    if ultima_compra:
                        costo_unitario = float(ultima_compra[0])
                
                # Convertir según el tipo de unidad
                if tipo in ['g', 'gramo', 'gramos']:
                    # Cantidad ya está en gramos
                    pass
                elif tipo in ['kg', 'kilogramo', 'kilogramos']:
                    cantidad = cantidad * 1000  # Convertir kg a gramos
                elif tipo in ['ml', 'mililitro', 'mililitros']:
                    pass  # Cantidad ya está en ml
                elif tipo in ['l', 'litro', 'litros']:
                    cantidad = cantidad * 1000  # Convertir litros a ml
                elif tipo in ['pz', 'pieza', 'piezas']:
                    # Para piezas, el costo unitario ya es por pieza
                    pass
                
                total_costo += cantidad * costo_unitario
            
            # Calcular costo por pieza del producto final
            costo_por_pieza = round(total_costo / rendimiento, 2) if rendimiento > 0 else 0
            
            # Actualizar costo estimado del producto
            #if p.costo_unitario_estimado != costo_por_pieza:
                #p.costo_unitario_estimado = costo_por_pieza
                #cambios = True
            
            # Calcular precio de venta sugerido (60% de margen)
            precio_sugerido = round(costo_por_pieza * 1.6, 2)
            
            # Solo actualizar si el precio actual es menor al sugerido o es 0
            #if p.precio_venta == 0 or p.precio_venta < precio_sugerido:
             #   p.precio_venta = precio_sugerido
              #  cambios = True

    if cambios:
        db.session.commit()

    return render_template(
        "modulo-productos/modulo-productos.html",
        productos=productos
    )


def obtener_costo_materia_prima(id_materia):
    """
    Obtiene el costo unitario de una materia prima
    Prioridad:
    1. Precio de la última compra
    2. Costo promedio de inventario
    """
    from models import DetalleCompra, Compra, InventarioMateriaPrima
    
    # Opción 1: Último precio de compra
    ultima_compra = db.session.query(DetalleCompra.precio_unitario_compra)\
        .join(Compra)\
        .filter(DetalleCompra.id_materia == id_materia)\
        .filter(Compra.estado == 'recibida')\
        .order_by(Compra.fecha_entrega.desc())\
        .first()
    
    if ultima_compra and ultima_compra[0]:
        return float(ultima_compra[0])
    
    # Opción 2: Calcular costo promedio del inventario actual
    inventario = InventarioMateriaPrima.query.filter_by(id_materia=id_materia).first()
    if inventario and inventario.stock_actual > 0:
        # Aquí podrías calcular el costo promedio ponderado
        # Por ahora, retornar 0
        return 0
    
    return 0

# AGREGAR PRODUCTO - CON VALIDACIÓN DE DUPLICADO
@productos_bp.route('/agregarProducto', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def agregarProducto():

    form = forms.ProductoForm()

    categorias = Categoria.query.all()
    form.id_categoria.choices = [(c.id_categoria, c.nombre) for c in categorias]

    if form.validate_on_submit():
        producto_existente = Producto.query.filter_by(
            nombre=form.nombre.data
        ).first()

        if producto_existente:
            flash(f"Ya existe un producto con el nombre '{form.nombre.data}'.", "danger")
            return render_template(
                'modulo-productos/agregarProducto.html',
                form=form
            )

        imagen = request.files.get("imagen")

        imagen_bytes = None

        if imagen and imagen.filename != "":
            imagen_bytes = imagen.read()

        nuevo_producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            id_categoria=form.id_categoria.data,
            #precio_venta=form.precio_venta.data,
            #costo_unitario_estimado=form.costo_unitario_estimado.data,
            imagen_url=imagen_bytes,
            #dias_caducidad=form.dias_caducidad.data,
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

# EDITAR PRODUCTO - CON VALIDACIÓN DE DUPLICADO (excluyendo el producto actual)
@productos_bp.route('/editarProducto/<int:id>', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def modificarProducto(id):

    producto = Producto.query.get_or_404(id)

    form = forms.ProductoForm(obj=producto)

    categorias = Categoria.query.all()
    form.id_categoria.choices = [(c.id_categoria, c.nombre) for c in categorias]

    if form.validate_on_submit():

       
        producto_existente = Producto.query.filter(
            Producto.nombre == form.nombre.data,
            Producto.id_producto != id  # Excluir el producto actual
        ).first()
        
        if producto_existente:
            flash(f"Ya existe otro producto con el nombre '{form.nombre.data}'.", "danger")
            return render_template(
                'modulo-productos/modificarProducto.html',
                form=form,
                producto=producto
            )

        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.id_categoria = form.id_categoria.data
        #producto.precio_venta = form.precio_venta.data
        #producto.costo_unitario_estimado = form.costo_unitario_estimado.data
        #producto.dias_caducidad = form.dias_caducidad.data
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
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
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

# ========== FUNCIONES PARA CÁLCULOS FINANCIEROS ==========

def calcular_costos_operativos_reales():
    """
    Calcula la mano de obra diaria promedio y gastos operativos mensuales
    desde las tablas de nóminas y gastos extra.
    
    Returns:
        tuple: (costo_mano_obra_por_lote, gastos_operativos_por_lote)
    """
    from models import NominaIndividual, GastoExtra
    from datetime import date, timedelta
    from decimal import Decimal
    
    hoy = date.today()
    
    # ========== 1. CALCULAR MANO DE OBRA REAL (últimos 30 días) ==========
    fecha_inicio_nomina = hoy - timedelta(days=30)
    
    # Sumar todas las nóminas pagadas en los últimos 30 días
    total_nomina = db.session.query(db.func.sum(NominaIndividual.monto_pagado))\
        .filter(
            NominaIndividual.estatus == 'pagado',
            NominaIndividual.fecha_pago >= fecha_inicio_nomina
        ).scalar() or Decimal('0')
    
    # Contar días hábiles (aproximación: 22 días laborables por mes)
    # O puedes usar el número real de días en el periodo
    dias_laborables = 22
    
    # Costo diario de mano de obra
    costo_mano_obra_diario = float(total_nomina) / dias_laborables if dias_laborables > 0 else 80.00
    
    # Distribuir por lote (asumiendo X lotes por día - valor por defecto 5 lotes/día)
    lotes_por_dia = 5
    costo_mano_obra_por_lote = costo_mano_obra_diario / lotes_por_dia if lotes_por_dia > 0 else 80.00
    
    # Si no hay nóminas registradas, usar valor por defecto
    if costo_mano_obra_por_lote <= 0:
        costo_mano_obra_por_lote = 80.00
    
    # ========== 2. CALCULAR GASTOS OPERATIVOS REALES (últimos 30 días) ==========
    fecha_inicio_gastos = hoy - timedelta(days=30)
    
    # Sumar todos los gastos extra de los últimos 30 días
    total_gastos = db.session.query(db.func.sum(GastoExtra.monto))\
        .filter(GastoExtra.fecha >= fecha_inicio_gastos)\
        .scalar() or Decimal('0')
    
    # Gastos diarios
    costo_gastos_diario = float(total_gastos) / 30 if total_gastos > 0 else 50.00
    
    # Distribuir por lote
    costo_gastos_por_lote = costo_gastos_diario / lotes_por_dia if lotes_por_dia > 0 else 50.00
    
    # Si no hay gastos registrados, usar valor por defecto
    if costo_gastos_por_lote <= 0:
        costo_gastos_por_lote = 50.00
    
    return round(costo_mano_obra_por_lote, 2), round(costo_gastos_por_lote, 2)

@productos_bp.route('/detalleProducto/<int:id>', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def detalleProducto(id):
    from models import HistorialPreciosMateriaPrima, DetalleCompra, Compra, MovimientoInventario
    from datetime import datetime, timedelta
    from utils.calculos import obtener_ultimo_costo_materia, obtener_detalle_ultima_compra
    
    producto = Producto.query.get_or_404(id)
    receta = Receta.query.filter_by(id_producto=id).first()
    
    # ========== CARGAR DATOS REALES DE NÓMINAS Y FINANZAS ==========
    costo_mano_obra_real, costo_gastos_reales = calcular_costos_operativos_reales()
    
    # Variables por defecto para el escandallo
    ingredientes = []
    total_costo_receta = 0
    total_sin_iva = 0
    costo_total_con_iva = 0
    rendimiento = 1
    margen_ganancia = 60
    iva_porcentaje = 16
    precios_sugeridos = {
        'economico': {'sin_iva': 0, 'con_iva': 0},
        'estandar': {'sin_iva': 0, 'con_iva': 0},
        'premium': {'sin_iva': 0, 'con_iva': 0}
    }
    margenes = {'economico': 40, 'estandar': 60, 'premium': 100}
    ganancia_potencial = 0
    costo_lote_total = 0
    costo_por_pieza = 0
    costo_con_iva = 0
    iva_producto = 0
    total_compras_mes = 0
    total_movimientos_mes = 0
    
    # Usar valores reales o manuales
    mano_obra = costo_mano_obra_real
    gastos = costo_gastos_reales
    
    # Procesar POST si viene del formulario (permite sobrescribir manualmente)
    if request.method == 'POST' and receta:
        try:
            # Si el usuario quiere sobrescribir manualmente
            if request.form.get('usar_valores_reales') == 'false':
                mano_obra = float(request.form.get('mano_obra', costo_mano_obra_real))
                gastos = float(request.form.get('gastos', costo_gastos_reales))
            else:
                # Si no, usar los valores reales calculados
                mano_obra = costo_mano_obra_real
                gastos = costo_gastos_reales
            
            iva_porcentaje = float(request.form.get('iva_porcentaje', 16))
            margen_ganancia = float(request.form.get('margen_ganancia', 60))
        except:
            pass
    
    # Calcular escandallo si existe receta
    if receta:
        rendimiento = receta.rendimiento_piezas or 1
        
        for detalle in receta.ingredientes:
            materia = detalle.materia
            tipo = (detalle.tipo or '').lower().strip()
            cantidad = float(detalle.cantidad)
            
            # Obtener el costo actual desde el historial
            costo_unitario = obtener_ultimo_costo_materia(materia.id_materia)
            
            # Obtener información de la última compra
            info_ultima_compra = obtener_detalle_ultima_compra(materia.id_materia)
            
            # Determinar la unidad de visualización y convertir cantidad a base
            if tipo in ['g', 'gramo', 'gramos']:
                cantidad_base = cantidad
                unidad_visual = 'g'
            elif tipo in ['kg', 'kilogramo', 'kilogramos']:
                cantidad_base = cantidad * 1000
                unidad_visual = 'kg'
            elif tipo in ['ml', 'mililitro', 'mililitros']:
                cantidad_base = cantidad
                unidad_visual = 'ml'
            elif tipo in ['l', 'litro', 'litros']:
                cantidad_base = cantidad * 1000
                unidad_visual = 'L'
            elif tipo in ['pz', 'pieza', 'piezas']:
                cantidad_base = cantidad
                unidad_visual = 'pz'
            else:
                cantidad_base = cantidad
                unidad_visual = tipo
            
            # Calcular subtotal
            subtotal = cantidad_base * costo_unitario
            total_costo_receta += subtotal
            
            # Calcular IVA
            iva = subtotal * (iva_porcentaje / 100)
            subtotal_con_iva = subtotal + iva
            total_sin_iva += subtotal
            costo_total_con_iva += subtotal_con_iva
            
            # Formatear costo unitario para mostrar
            if costo_unitario == 0:
                costo_mostrar = 0
                warning_precio = "⚠️ Sin precio registrado"
            else:
                costo_mostrar = costo_unitario
                warning_precio = None
            
            ingredientes.append({
                'id_materia': materia.id_materia,
                'nombre': materia.nombre,
                'cantidad': round(cantidad, 2),
                'unidad': unidad_visual,
                'costo_unitario': costo_mostrar,
                'subtotal': round(subtotal, 2),
                'subtotal_con_iva': round(subtotal_con_iva, 2),
                'iva': round(iva, 2),
                'warning': warning_precio,
                'ultima_compra': info_ultima_compra
            })
        
        # Ordenar por subtotal (mayor a menor)
        ingredientes.sort(key=lambda x: x['subtotal'], reverse=True)
        
        # Calcular porcentajes de participación
        for ing in ingredientes:
            ing['porcentaje'] = (ing['subtotal'] / total_costo_receta * 100) if total_costo_receta > 0 else 0
        
        # Calcular costos totales
        costo_insumos = total_costo_receta
        costo_lote_total = costo_insumos + mano_obra + gastos
        costo_por_pieza = costo_lote_total / rendimiento if rendimiento > 0 else 0
        
        # Calcular IVA del producto final
        iva_producto = costo_por_pieza * (iva_porcentaje / 100)
        costo_con_iva = costo_por_pieza + iva_producto
        
        # Calcular precios sugeridos con diferentes márgenes
        margenes = {
            'economico': 40,
            'estandar': margen_ganancia,
            'premium': 100
        }
        
        precios_sugeridos = {
            'economico': {
                'sin_iva': costo_por_pieza * (1 + margenes['economico'] / 100),
                'con_iva': costo_por_pieza * (1 + margenes['economico'] / 100) * (1 + iva_porcentaje / 100)
            },
            'estandar': {
                'sin_iva': costo_por_pieza * (1 + margenes['estandar'] / 100),
                'con_iva': costo_por_pieza * (1 + margenes['estandar'] / 100) * (1 + iva_porcentaje / 100)
            },
            'premium': {
                'sin_iva': costo_por_pieza * (1 + margenes['premium'] / 100),
                'con_iva': costo_por_pieza * (1 + margenes['premium'] / 100) * (1 + iva_porcentaje / 100)
            }
        }
        
        ganancia_potencial = (precios_sugeridos['estandar']['sin_iva'] - costo_por_pieza) * rendimiento
        
        # Obtener resumen del último mes
        fecha_hace_mes = datetime.now() - timedelta(days=30)
        
        total_compras_mes = db.session.query(db.func.sum(Compra.total))\
            .filter(Compra.estado == 'recibida')\
            .filter(Compra.fecha_entrega >= fecha_hace_mes)\
            .scalar() or 0
        
        total_movimientos_mes = db.session.query(db.func.sum(MovimientoInventario.cantidad))\
            .filter(MovimientoInventario.tipo == 'entrada')\
            .filter(MovimientoInventario.fecha >= fecha_hace_mes)\
            .scalar() or 0

    return render_template(
        'modulo-productos/detallesProducto.html',
        producto=producto,
        receta=receta,
        rendimiento=rendimiento,
        ingredientes=ingredientes,
        total_costo_receta=round(total_costo_receta, 2),
        total_sin_iva=round(total_sin_iva, 2),
        costo_total_con_iva=round(costo_total_con_iva, 2),
        mano_obra=round(mano_obra, 2),
        gastos=round(gastos, 2),
        costo_mano_obra_real=round(costo_mano_obra_real, 2),
        costo_gastos_reales=round(costo_gastos_reales, 2),
        costo_lote_total=round(costo_lote_total, 2),
        costo_por_pieza=round(costo_por_pieza, 4),
        costo_con_iva=round(costo_con_iva, 2),
        iva_porcentaje=iva_porcentaje,
        iva_producto=round(iva_producto, 2),
        precios_sugeridos=precios_sugeridos,
        margenes=margenes,
        margen_ganancia=margen_ganancia,
        ganancia_potencial=round(ganancia_potencial, 2),
        total_compras_mes=round(total_compras_mes, 2),
        total_movimientos_mes=round(total_movimientos_mes, 2)
    )
# MOSTRAR IMAGEN DEL PRODUCTO
@productos_bp.route('/producto_imagen/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def producto_imagen(id):
    producto = Producto.query.get_or_404(id)
    
    if producto.imagen_url:
        return Response(producto.imagen_url, mimetype='image/jpeg')
    
    # Imagen por defecto si no hay imagen
    return "", 404

@productos_bp.route('/inventario')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def verInventario():
    buscar = request.args.get("buscar")
    id_sucursal = request.args.get("sucursal", type=int)
    
    query = InventarioProducto.query
    
    # Filtrar por sucursal
    if id_sucursal:
        query = query.filter_by(id_sucursal=id_sucursal)
    
    # Buscar por nombre de producto
    if buscar:
        query = query.join(Producto).filter(
            Producto.nombre.ilike(f"%{buscar}%")
        )
    
    inventarios = query.all()
    sucursales = Sucursal.query.filter_by(estatus='activo').all()
    
    return render_template(
        'inventarioProducto/inventarioProducto.html',
        inventarios=inventarios,
        sucursales=sucursales,
        sucursal_seleccionada=id_sucursal
    )

@productos_bp.route('/historialInventario/<int:id_producto>/<int:id_sucursal>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def historialInventario(id_producto, id_sucursal):
   
    movimientos = MovimientoInventarioProducto.query.filter_by(
        id_producto=id_producto,
        id_sucursal=id_sucursal
    ).order_by(MovimientoInventarioProducto.fecha.desc()).all()
    
    producto = Producto.query.get_or_404(id_producto)
    sucursal = Sucursal.query.get_or_404(id_sucursal)
    
    return render_template(
        'inventarioProducto/historial.html',
        movimientos=movimientos,
        producto=producto,
        sucursal=sucursal
    )

@productos_bp.route('/producto/<int:id>/aplicar_precio', methods=['POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def aplicar_precio(id):
    producto = Producto.query.get_or_404(id)
    nuevo_precio = request.form.get('precio_sugerido')
    try:
        producto.precio_venta = float(nuevo_precio)
        db.session.commit()
        flash(f'Precio actualizado a ${float(nuevo_precio):.2f} correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar el precio: {str(e)}', 'danger')
    return redirect(url_for('productos.detalleProducto', id=id))
   
@productos_bp.route('/ajustar_stock/<int:id_inventario>', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def ajustarStock(id_inventario):
    inventario = InventarioProducto.query.get_or_404(id_inventario)
    
    if request.method == 'POST':
        cantidad = int(request.form.get('cantidad', 0))
        tipo = request.form.get('tipo')
        
        if tipo == 'agregar':
            inventario.stock_actual += cantidad
            mensaje = f"Se agregaron {cantidad} unidades"
        elif tipo == 'quitar':
            if inventario.stock_actual >= cantidad:
                inventario.stock_actual -= cantidad
                mensaje = f"Se quitaron {cantidad} unidades"
            else:
                flash('No hay suficiente stock', 'error')
                return redirect(url_for('productos.verInventario'))
        
        # Registrar movimiento
        
        movimiento = MovimientoInventarioProducto(
            id_producto=inventario.id_producto,
            id_sucursal=inventario.id_sucursal,
            cantidad=cantidad,
            tipo='ajuste_manual',
            referencia=f'Ajuste manual por usuario'
        )
        db.session.add(movimiento)
        db.session.commit()
        
        flash(mensaje, 'success')
        return redirect(url_for('productos.verInventario'))
    
    return render_template('inventarioProducto/ajustar_stock.html', inventario=inventario)

