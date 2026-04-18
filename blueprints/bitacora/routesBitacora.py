from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Bitacora
from sqlalchemy import or_, desc
from datetime import datetime, timedelta
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message


bitacora_bp = Blueprint('bitacora', __name__, url_prefix='/bitacora')


@bitacora_bp.route('/')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def ver_bitacora():
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 20
    buscar = request.args.get('buscar', '')
    accion_filtro = request.args.get('accion', '')
    tabla_filtro = request.args.get('tabla', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')

    query = Bitacora.query

    # 🔍 BÚSQUEDA (usando los campos CORRECTOS de tu modelo)
    if buscar:
        query = query.filter(
            or_(
                Bitacora.usuario_nombre.ilike(f'%{buscar}%'),  # ← CORREGIDO: usuario_nombre
                Bitacora.accion.ilike(f'%{buscar}%'),
                Bitacora.tabla.ilike(f'%{buscar}%'),
                Bitacora.descripcion.ilike(f'%{buscar}%'),
                Bitacora.ip_usuario.ilike(f'%{buscar}%')       # ← ip_usuario existe
            )
        )

    # 🎯 FILTROS
    if accion_filtro:
        query = query.filter(Bitacora.accion == accion_filtro)

    if tabla_filtro:
        query = query.filter(Bitacora.tabla == tabla_filtro)

    # 📅 FECHAS
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Bitacora.fecha_hora >= fecha_desde_dt)
        except:
            pass

    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Bitacora.fecha_hora <= fecha_hasta_dt)
        except:
            pass

    # ⬇️ ORDEN
    query = query.order_by(desc(Bitacora.fecha_hora))

    # 📄 PAGINACIÓN
    logs = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

    # 📊 FILTROS DINÁMICOS (filtrar valores None)
    acciones = [a[0] for a in db.session.query(Bitacora.accion).distinct().all() if a[0]]
    tablas = [t[0] for t in db.session.query(Bitacora.tabla).distinct().all() if t[0]]

    return render_template(
        'bitacora/ver_bitacora.html',
        logs=logs,
        buscar=buscar,
        accion_filtro=accion_filtro,
        tabla_filtro=tabla_filtro,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        acciones=acciones,
        tablas=tablas
    )


@bitacora_bp.route('/detalle/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def detalle_log(id):
    log = Bitacora.query.get_or_404(id)
    return render_template('bitacora/detalle_log.html', log=log)


@bitacora_bp.route('/limpiar', methods=['POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def limpiar_bitacora():
    # 🔐 VALIDACIÓN DE ADMIN
    if not hasattr(current_user, "id_rol") or current_user.id_rol != 1:
        flash('No tienes permisos para realizar esta acción', 'danger')
        return redirect(url_for('bitacora.ver_bitacora'))

    try:
        fecha_limite = datetime.now() - timedelta(days=180)

        eliminados = Bitacora.query.filter(
            Bitacora.fecha_hora < fecha_limite
        ).delete()

        db.session.commit()

        flash(f'Se eliminaron {eliminados} registros antiguos', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al limpiar: {str(e)}', 'danger')

    return redirect(url_for('bitacora.ver_bitacora'))