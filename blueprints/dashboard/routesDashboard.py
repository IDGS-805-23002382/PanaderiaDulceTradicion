from flask import render_template, current_app, request 
from flask_login import current_user, login_required
from models import Producto, MateriaPrima, Orden, Sucursal, Compra, InventarioMateriaPrima, db
from blueprints.dashboard import dashboard_bp
from datetime import datetime, timedelta

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    mongo = current_app.mongo
    hoy = datetime.now()

    inicio_dia = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0)

    # ── FILTROS ─────────────────────────────────────────────
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    tipo = request.args.get('tipo')

    query = {'fecha': {'$gte': inicio_mes}}

    if fecha_inicio:
        query['fecha']['$gte'] = datetime.strptime(fecha_inicio, '%Y-%m-%d')

    if fecha_fin:
        query['fecha']['$lte'] = datetime.strptime(fecha_fin, '%Y-%m-%d')

    if tipo:
        query['tipo'] = tipo

    ventas_filtradas = list(mongo.db.ventas.find(query))

    # ── MÉTRICAS ─────────────────────────────────────────────
    ventas_hoy = [v for v in ventas_filtradas if v.get('fecha') >= inicio_dia]
    ventas_semana = [v for v in ventas_filtradas if v.get('fecha') >= inicio_semana]

    total_hoy = sum(v.get('total', 0) for v in ventas_hoy)
    total_semana = sum(v.get('total', 0) for v in ventas_semana)
    total_mes = sum(v.get('total', 0) for v in ventas_filtradas)

    num_ventas_hoy = len(ventas_hoy)
    ticket_promedio = round(total_hoy / num_ventas_hoy, 2) if num_ventas_hoy > 0 else 0

    # ── 🔥 TOP PRODUCTOS CORREGIDO ─────────────────────────────
    conteo_productos = {}

    for venta in ventas_filtradas:
        detalles = venta.get('detalles', [])

        # Debug opcional (puedes imprimir para verificar)
        # print(detalles)

        for detalle in detalles:
            nombre = detalle.get('nombre_producto')
            cantidad = detalle.get('cantidad', 0)

            # Validar datos
            if not nombre:
                continue

            try:
                cantidad = float(cantidad)
            except:
                cantidad = 0

            conteo_productos[nombre] = conteo_productos.get(nombre, 0) + cantidad

    # Ordenar correctamente
    top_productos = sorted(
        conteo_productos.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    # ── VENTAS POR TIPO ───────────────────────────────────────
    ventas_online = sum(1 for v in ventas_filtradas if v.get('tipo') == 'online')
    ventas_sucursal = sum(1 for v in ventas_filtradas if v.get('tipo') == 'sucursal')

    # ── EVOLUCIÓN ─────────────────────────────────────────────
    evolucion = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)

        inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = dia.replace(hour=23, minute=59, second=59)

        total_dia = sum(
            v.get('total', 0)
            for v in mongo.db.ventas.find({
                'fecha': {'$gte': inicio, '$lte': fin}
            })
        )

        evolucion.append({
            'dia': dia.strftime('%d/%m'),
            'total': float(total_dia)
        })

    # ── INVENTARIO ────────────────────────────────────────────
    materias_stock_bajo = db.session.query(MateriaPrima, InventarioMateriaPrima)\
        .join(InventarioMateriaPrima, MateriaPrima.id_materia == InventarioMateriaPrima.id_materia)\
        .filter(
            InventarioMateriaPrima.stock_actual <= InventarioMateriaPrima.stock_minimo,
            MateriaPrima.estatus == 'activo'
        ).all()

    total_productos_activos = Producto.query.filter_by(estatus='activo').count()

    # ── PRODUCCIÓN ────────────────────────────────────────────
    ordenes_planeadas = Orden.query.filter_by(estatus='pendiente').count()
    ordenes_completadas = Orden.query.filter_by(estatus='completada').count()

    # ── COMPRAS ───────────────────────────────────────────────
    compras_mes = Compra.query.filter(
        Compra.fecha_estimada_entrega >= inicio_mes,
        Compra.estado == "recibida"
    ).all()

    total_compras_mes = sum(c.total or 0 for c in compras_mes)

    # ── SUCURSALES ────────────────────────────────────────────
    total_sucursales = Sucursal.query.filter_by(estatus='activo').count()

    return render_template('modulo-dashboard/dashboard.html',
        total_hoy=total_hoy,
        total_semana=total_semana,
        total_mes=total_mes,
        num_ventas_hoy=num_ventas_hoy,
        ticket_promedio=ticket_promedio,
        top_productos=top_productos,
        ventas_online=ventas_online,
        ventas_sucursal=ventas_sucursal,
        evolucion=evolucion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipo=tipo,
        materias_stock_bajo=materias_stock_bajo,
        total_productos_activos=total_productos_activos,
        ordenes_planeadas=ordenes_planeadas,
        ordenes_completadas=ordenes_completadas,
        compras_mes=compras_mes,
        num_compras_mes=len(compras_mes),
        total_compras_mes=total_compras_mes,
        total_sucursales=total_sucursales,
        current_user=current_user
    )