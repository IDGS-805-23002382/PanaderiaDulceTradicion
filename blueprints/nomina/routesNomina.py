# blueprints/finanzas/routesFinanzas.py
from flask import render_template, redirect, url_for, flash, request, jsonify
from models import db, GastoExtra, Orden, Compra, NominaIndividual
from flask_login import login_required
from . import finanzas_bp
from utils.decorators import gerente_or_admin_required
from datetime import date, timedelta
from decimal import Decimal
import datetime


def _rango(periodo):
    """Devuelve (fecha_inicio, fecha_fin) según el periodo solicitado."""
    hoy = date.today()
    if periodo == 'semana':
        inicio = hoy - timedelta(days=hoy.weekday())          # lunes de esta semana
        fin    = inicio + timedelta(days=6)
    elif periodo == 'anio':
        inicio = date(hoy.year, 1, 1)
        fin    = date(hoy.year, 12, 31)
    else:  # mes (default)
        inicio = date(hoy.year, hoy.month, 1)
        # último día del mes
        if hoy.month == 12:
            fin = date(hoy.year, 12, 31)
        else:
            fin = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
    return inicio, fin


def _totales(inicio, fin):
    """Calcula todos los totales financieros para el rango dado."""

    # INGRESOS — ordenes completadas
    ingresos = db.session.query(db.func.sum(Orden.total))\
        .filter(
            Orden.estatus == 'completada',
            db.func.date(Orden.fecha) >= inicio,
            db.func.date(Orden.fecha) <= fin
        ).scalar() or Decimal('0')

    # EGRESOS — compras a proveedor
    egresos_compras = db.session.query(db.func.sum(Compra.total))\
        .filter(
            db.func.date(Compra.fecha) >= inicio,
            db.func.date(Compra.fecha) <= fin
        ).scalar() or Decimal('0')

    # EGRESOS — nómina pagada
    egresos_nomina = db.session.query(db.func.sum(NominaIndividual.monto_pagado))\
        .filter(
            NominaIndividual.estatus == 'pagado',
            db.func.date(NominaIndividual.fecha_pago) >= inicio,
            db.func.date(NominaIndividual.fecha_pago) <= fin
        ).scalar() or Decimal('0')

    # EGRESOS — gastos extra
    egresos_gastos = db.session.query(db.func.sum(GastoExtra.monto))\
        .filter(
            GastoExtra.fecha >= inicio,
            GastoExtra.fecha <= fin
        ).scalar() or Decimal('0')

    total_egresos = egresos_compras + egresos_nomina + egresos_gastos
    saldo_neto    = ingresos - total_egresos

    return {
        'ingresos':        float(ingresos),
        'egresos_compras': float(egresos_compras),
        'egresos_nomina':  float(egresos_nomina),
        'egresos_gastos':  float(egresos_gastos),
        'total_egresos':   float(total_egresos),
        'saldo_neto':      float(saldo_neto),
    }


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@finanzas_bp.route("/finanzas")
@login_required
@gerente_or_admin_required
def index():
    periodo = request.args.get('periodo', 'mes')   # semana | mes | anio
    inicio, fin = _rango(periodo)
    totales = _totales(inicio, fin)

    # Últimos gastos extra para mostrar en tabla
    gastos_recientes = GastoExtra.query\
        .filter(GastoExtra.fecha >= inicio, GastoExtra.fecha <= fin)\
        .order_by(GastoExtra.fecha.desc()).limit(10).all()

    # Ventas recientes del periodo
    ventas_recientes = Orden.query\
        .filter(
            Orden.estatus == 'completada',
            db.func.date(Orden.fecha) >= inicio,
            db.func.date(Orden.fecha) <= fin
        ).order_by(Orden.fecha.desc()).limit(10).all()

    # Compras recientes del periodo
    compras_recientes = Compra.query\
        .filter(
            db.func.date(Compra.fecha) >= inicio,
            db.func.date(Compra.fecha) <= fin
        ).order_by(Compra.fecha.desc()).limit(10).all()

    # Nóminas pagadas del periodo
    nominas_recientes = NominaIndividual.query\
        .filter(
            NominaIndividual.estatus == 'pagado',
            db.func.date(NominaIndividual.fecha_pago) >= inicio,
            db.func.date(NominaIndividual.fecha_pago) <= fin
        ).order_by(NominaIndividual.fecha_pago.desc()).limit(10).all()

    return render_template("modulo-finanzas/modulo-finanzas.html",
        periodo          = periodo,
        inicio           = inicio,
        fin              = fin,
        totales          = totales,
        gastos_recientes = gastos_recientes,
        ventas_recientes = ventas_recientes,
        compras_recientes= compras_recientes,
        nominas_recientes= nominas_recientes,
    )


# ─── GASTOS EXTRA CRUD ───────────────────────────────────────────────────────

@finanzas_bp.route("/finanzas/gastos")
@login_required
@gerente_or_admin_required
def gastos():
    gastos = GastoExtra.query.order_by(GastoExtra.fecha.desc()).all()
    return render_template("modulo-finanzas/gastos.html", gastos=gastos)


@finanzas_bp.route("/finanzas/gastos/nuevo", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
def nuevo_gasto():
    CATEGORIAS = ['Renta', 'Servicios', 'Mantenimiento', 'Equipo', 'Limpieza', 'Otros']
    if request.method == 'POST':
        gasto = GastoExtra(
            concepto  = request.form.get('concepto'),
            monto     = Decimal(request.form.get('monto') or '0'),
            fecha     = date.fromisoformat(request.form.get('fecha')),
            categoria = request.form.get('categoria'),
            notas     = request.form.get('notas')
        )
        db.session.add(gasto)
        db.session.commit()
        flash('Gasto registrado correctamente.', 'success')
        return redirect(url_for('finanzas.gastos'))
    return render_template("modulo-finanzas/form-gasto.html",
                           categorias=CATEGORIAS, gasto=None)


@finanzas_bp.route("/finanzas/gastos/editar/<int:id>", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
def editar_gasto(id):
    CATEGORIAS = ['Renta', 'Servicios', 'Mantenimiento', 'Equipo', 'Limpieza', 'Otros']
    gasto = GastoExtra.query.get_or_404(id)
    if request.method == 'POST':
        gasto.concepto  = request.form.get('concepto')
        gasto.monto     = Decimal(request.form.get('monto') or '0')
        gasto.fecha     = date.fromisoformat(request.form.get('fecha'))
        gasto.categoria = request.form.get('categoria')
        gasto.notas     = request.form.get('notas')
        db.session.commit()
        flash('Gasto actualizado.', 'success')
        return redirect(url_for('finanzas.gastos'))
    return render_template("modulo-finanzas/form-gasto.html",
                           categorias=CATEGORIAS, gasto=gasto)


@finanzas_bp.route("/finanzas/gastos/eliminar/<int:id>", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
def eliminar_gasto(id):
    gasto = GastoExtra.query.get_or_404(id)
    if request.method == 'POST':
        db.session.delete(gasto)
        db.session.commit()
        flash('Gasto eliminado.', 'success')
        return redirect(url_for('finanzas.gastos'))
    return render_template("modulo-finanzas/confirmar-eliminar-gasto.html", gasto=gasto)