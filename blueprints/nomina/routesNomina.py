# blueprints/nomina/routesNomina.py
from flask import render_template, redirect, url_for, flash, request
from models import db, NominaIndividual, NominaGrupal, Empleado
from flask_login import login_required
from . import nomina_bp
from utils.decorators import gerente_or_admin_required
from datetime import date
from decimal import Decimal


# ─── RESUMEN GLOBAL ──────────────────────────────────────────────────────────

@nomina_bp.route("/nomina")
@login_required
@gerente_or_admin_required
def index():
    """Vista principal: resumen global de todas las nóminas."""
    grupales    = NominaGrupal.query.order_by(NominaGrupal.fecha_registro.desc()).all()
    individuales_sueltas = NominaIndividual.query.filter_by(id_nomina_grupal=None)\
                            .order_by(NominaIndividual.fecha_registro.desc()).all()

    # Totales globales
    total_pagado    = db.session.query(db.func.sum(NominaIndividual.monto_pagado))\
                        .filter(NominaIndividual.estatus == 'pagado').scalar() or 0
    total_pendiente = db.session.query(db.func.sum(NominaIndividual.monto_pagado))\
                        .filter(NominaIndividual.estatus == 'pendiente').scalar() or 0
    total_incidencia = db.session.query(db.func.sum(NominaIndividual.monto_pagado))\
                        .filter(NominaIndividual.estatus == 'incidencia').scalar() or 0

    return render_template("modulo-nomina/modulo-nomina.html",
        grupales=grupales,
        individuales_sueltas=individuales_sueltas,
        total_pagado=total_pagado,
        total_pendiente=total_pendiente,
        total_incidencia=total_incidencia
    )


# ─── NÓMINA INDIVIDUAL ───────────────────────────────────────────────────────

@nomina_bp.route("/nomina/individual/nueva", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
def nueva_individual():
    """Crear una nómina para un solo empleado."""
    empleados = Empleado.query.filter_by(estatus='activo').order_by(Empleado.nombre).all()

    if request.method == 'POST':
        id_empleado  = request.form.get('id_empleado', type=int)
        periodo      = request.form.get('periodo')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin    = request.form.get('fecha_fin')
        monto        = request.form.get('monto_pagado')

        empleado = Empleado.query.get_or_404(id_empleado)
        salario  = empleado.salario or Decimal('0')

        nomina = NominaIndividual(
            id_empleado  = id_empleado,
            periodo      = periodo,
            fecha_inicio = date.fromisoformat(fecha_inicio),
            fecha_fin    = date.fromisoformat(fecha_fin),
            puesto       = empleado.puesto,
            salario_base = salario,
            monto_pagado = Decimal(monto) if monto else (salario / 2 if periodo == 'quincenal' else salario),
            estatus      = 'pendiente'
        )
        db.session.add(nomina)
        db.session.commit()
        flash(f'Nómina individual creada para {empleado.nombre}.', 'success')
        return redirect(url_for('nomina.detalle_individual', id=nomina.id_nomina_ind))

    return render_template("modulo-nomina/form-individual.html", empleados=empleados)


@nomina_bp.route("/nomina/individual/<int:id>")
@login_required
@gerente_or_admin_required
def detalle_individual(id):
    nomina = NominaIndividual.query.get_or_404(id)
    return render_template("modulo-nomina/detalle-individual.html", nomina=nomina)


@nomina_bp.route("/nomina/individual/<int:id>/editar", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
def editar_individual(id):
    nomina = NominaIndividual.query.get_or_404(id)

    if request.method == 'POST':
        nomina.periodo      = request.form.get('periodo')
        nomina.fecha_inicio = date.fromisoformat(request.form.get('fecha_inicio'))
        nomina.fecha_fin    = date.fromisoformat(request.form.get('fecha_fin'))
        nomina.puesto       = request.form.get('puesto')
        nomina.salario_base = Decimal(request.form.get('salario_base') or '0')
        nomina.monto_pagado = Decimal(request.form.get('monto_pagado') or '0')
        fecha_pago_raw      = request.form.get('fecha_pago')
        nomina.fecha_pago   = date.fromisoformat(fecha_pago_raw) if fecha_pago_raw else None
        nomina.estatus      = request.form.get('estatus')
        nomina.notas        = request.form.get('notas')

        # Recalcular total del grupal si pertenece a uno
        if nomina.id_nomina_grupal:
            grupal = NominaGrupal.query.get(nomina.id_nomina_grupal)
            grupal.total_pagado = sum(n.monto_pagado for n in grupal.individuales)

        db.session.commit()
        flash('Nómina actualizada correctamente.', 'success')
        return redirect(url_for('nomina.detalle_individual', id=id))

    return render_template("modulo-nomina/editar-individual.html", nomina=nomina)


@nomina_bp.route("/nomina/individual/<int:id>/pagar", methods=['POST'])
@login_required
@gerente_or_admin_required
def pagar_individual(id):
    nomina = NominaIndividual.query.get_or_404(id)
    nomina.estatus   = 'pagado'
    nomina.fecha_pago = date.today()

    if nomina.id_nomina_grupal:
        grupal = NominaGrupal.query.get(nomina.id_nomina_grupal)
        grupal.total_pagado = sum(
            n.monto_pagado for n in grupal.individuales if n.estatus == 'pagado'
        )

    db.session.commit()
    flash(f'Pago registrado para {nomina.empleado.nombre}.', 'success')

    # Regresar al detalle grupal si viene de uno
    if nomina.id_nomina_grupal:
        return redirect(url_for('nomina.detalle_grupal', id=nomina.id_nomina_grupal))
    return redirect(url_for('nomina.index'))


# ─── NÓMINA GRUPAL ───────────────────────────────────────────────────────────

@nomina_bp.route("/nomina/grupal/nueva", methods=['GET', 'POST'])
@login_required
@gerente_or_admin_required
def nueva_grupal():
    """Genera una nómina grupal seleccionando empleados."""
    empleados = Empleado.query.filter_by(estatus='activo').order_by(Empleado.nombre).all()

    if request.method == 'POST':
        nombre       = request.form.get('nombre')
        periodo      = request.form.get('periodo')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin    = request.form.get('fecha_fin')
        ids_empleados = request.form.getlist('empleados')  # checkboxes

        if not ids_empleados:
            flash('Selecciona al menos un empleado.', 'warning')
            return redirect(url_for('nomina.nueva_grupal'))

        grupal = NominaGrupal(
            nombre       = nombre,
            periodo      = periodo,
            fecha_inicio = date.fromisoformat(fecha_inicio),
            fecha_fin    = date.fromisoformat(fecha_fin),
            total_pagado = 0
        )
        db.session.add(grupal)
        db.session.flush()

        total = Decimal('0')
        for emp_id in ids_empleados:
            emp = Empleado.query.get(int(emp_id))
            if not emp:
                continue
            salario = emp.salario or Decimal('0')
            monto   = salario / 2 if periodo == 'quincenal' else salario

            ind = NominaIndividual(
                id_empleado      = emp.id_empleado,
                id_nomina_grupal = grupal.id_nomina_grupal,
                periodo          = periodo,
                fecha_inicio     = date.fromisoformat(fecha_inicio),
                fecha_fin        = date.fromisoformat(fecha_fin),
                puesto           = emp.puesto,
                salario_base     = salario,
                monto_pagado     = monto,
                estatus          = 'pendiente'
            )
            db.session.add(ind)
            total += monto

        grupal.total_pagado = total
        db.session.commit()
        flash(f'Nómina grupal "{nombre}" generada con {len(ids_empleados)} empleados.', 'success')
        return redirect(url_for('nomina.detalle_grupal', id=grupal.id_nomina_grupal))

    return render_template("modulo-nomina/form-grupal.html", empleados=empleados)


@nomina_bp.route("/nomina/grupal/<int:id>")
@login_required
@gerente_or_admin_required
def detalle_grupal(id):
    grupal = NominaGrupal.query.get_or_404(id)
    return render_template("modulo-nomina/detalle-grupal.html", grupal=grupal)


@nomina_bp.route("/nomina/grupal/<int:id>/pagar-todos", methods=['POST'])
@login_required
@gerente_or_admin_required
def pagar_todos(id):
    """Marca todos los pendientes de un grupal como pagados."""
    grupal = NominaGrupal.query.get_or_404(id)
    hoy = date.today()
    for ind in grupal.individuales:
        if ind.estatus == 'pendiente':
            ind.estatus    = 'pagado'
            ind.fecha_pago = hoy
    grupal.total_pagado = sum(n.monto_pagado for n in grupal.individuales)
    db.session.commit()
    flash('Todos los empleados pendientes marcados como pagados.', 'success')
    return redirect(url_for('nomina.detalle_grupal', id=id))