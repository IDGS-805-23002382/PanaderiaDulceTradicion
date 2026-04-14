from flask import render_template, current_app, request 
from flask_login import current_user, login_required
from models import Producto, MateriaPrima, Orden, Sucursal, Compra, db, InventarioProducto, InventarioMateriaPrima
from blueprints.dashboard import dashboard_bp
from datetime import datetime, timedelta

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    mongo = current_app.mongo
    hoy_dt = datetime.now()
    
    # RANGOS DE FECHA BASE
    hoy_inicio = hoy_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    semana_inicio = hoy_inicio - timedelta(days=hoy_dt.weekday())
    mes_inicio = hoy_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 1. --- FILTROS DINÁMICOS ---
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    tipo_filtro = request.args.get('tipo') 

    query_periodo = {}
    if fecha_inicio_str and fecha_fin_str:
        f_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
        f_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query_periodo['fecha'] = {'$gte': f_inicio, '$lte': f_fin}
    else:
        query_periodo['fecha'] = {'$gte': mes_inicio}

    if tipo_filtro and tipo_filtro != 'todos':
        query_periodo['tipo'] = tipo_filtro

    # 2. --- MÉTRICAS DE VENTAS (MongoDB) ---
    ventas_periodo = list(mongo.db.ventas.find(query_periodo))
    total_periodo = sum(v.get('total', 0) for v in ventas_periodo)
    num_ventas = len(ventas_periodo)
    ticket_promedio = total_periodo / num_ventas if num_ventas > 0 else 0

    total_hoy = sum(v.get('total', 0) for v in mongo.db.ventas.find({'fecha': {'$gte': hoy_inicio}}))
    num_ventas_hoy = mongo.db.ventas.count_documents({'fecha': {'$gte': hoy_inicio}})
    total_semana = sum(v.get('total', 0) for v in mongo.db.ventas.find({'fecha': {'$gte': semana_inicio}}))
    total_mes = sum(v.get('total', 0) for v in mongo.db.ventas.find({'fecha': {'$gte': mes_inicio}}))

    ventas_online = sum(v.get('total', 0) for v in ventas_periodo if v.get('tipo') == 'online')
    ventas_sucursal = sum(v.get('total', 0) for v in ventas_periodo if v.get('tipo') == 'sucursal')

    evolucion = []
    for i in range(6, -1, -1):
        d_inicio = hoy_inicio - timedelta(days=i)
        d_fin = d_inicio + timedelta(days=1)
        t_dia = sum(v.get('total', 0) for v in mongo.db.ventas.find({'fecha': {'$gte': d_inicio, '$lt': d_fin}}))
        evolucion.append({'dia': d_inicio.strftime('%d/%m'), 'total': t_dia})

    # 3. --- MÉTRICAS DE COMPRAS Y PRODUCCIÓN (SQL) ---
    compras_mes = Compra.query.filter(Compra.fecha_orden >= mes_inicio).all()
    total_compras_mes = sum(c.total for c in compras_mes)
    num_compras_mes = len(compras_mes)

    total_productos_activos = Producto.query.filter_by(estatus='activo').count()
    total_sucursales = Sucursal.query.count()

    # Inventario bajo (Alertas)
    productos_stock_bajo = InventarioProducto.query.filter(InventarioProducto.stock_actual < 10).all()
    materias_criticas = InventarioMateriaPrima.query.filter(InventarioMateriaPrima.stock_actual < 5).all()

    # Top Productos
    conteo_productos = {}
    for v in ventas_periodo:
        for d in v.get('detalles', []):
            n = d.get('nombre')
            conteo_productos[n] = conteo_productos.get(n, 0) + d.get('cantidad', 0)
    top_productos = sorted(conteo_productos.items(), key=lambda x: x[1], reverse=True)[:5]

    ordenes_planeadas = Orden.query.filter_by(estatus='planeada').count()
    ordenes_completadas = Orden.query.filter_by(estatus='completada').count()

    # 4. --- MÉTRICAS DE CLIENTES ---
    try:
        from models import Cliente
        total_clientes = Cliente.query.count()
    except Exception:
        total_clientes = 0
        
    return render_template('modulo-dashboard/dashboard.html',
        total_clientes=total_clientes,
        total_periodo=total_periodo,
        total_hoy=total_hoy,
        num_ventas_hoy=num_ventas_hoy,
        total_semana=total_semana,
        total_mes=total_mes,
        total_compras_mes=total_compras_mes,
        num_compras_mes=num_compras_mes,
        total_productos_activos=total_productos_activos,
        total_sucursales=total_sucursales,
        ventas_online=ventas_online,
        ventas_sucursal=ventas_sucursal,
        evolucion=evolucion,
        num_ventas=num_ventas,
        ticket_promedio=ticket_promedio,
        productos_stock_bajo=productos_stock_bajo,
        materias_criticas=materias_criticas,
        top_productos=top_productos,
        ordenes_planeadas=ordenes_planeadas,
        ordenes_completadas=ordenes_completadas,
        fecha_inicio=fecha_inicio_str,
        fecha_fin=fecha_fin_str,
        tipo_seleccionado=tipo_filtro,
        now=datetime.now()
    )