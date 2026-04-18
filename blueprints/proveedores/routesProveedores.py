from flask import Flask, render_template, request, redirect, url_for, flash
from models import Proveedor, db, MateriaPrima, Compra, DetalleCompra, Sucursal, MovimientoInventario, InventarioMateriaPrima, Merma
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from . import proveedores_bp
from flask import jsonify

from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message
from flask_login import login_required

from datetime import date, datetime
import forms

# ===== FUNCIONES DE CONVERSIÓN =====

def convertir_a_unidad_legible(stock, unidad):
    if not stock:
        return 0, unidad
    
    unidad = str(unidad).lower().strip()
    
    if unidad in ['g', 'gramo', 'gramos']:
        if stock >= 1000:
            return round(stock / 1000, 2), 'kg'
        else:
            return round(stock, 2), 'g'
    elif unidad in ['ml', 'mililitro', 'mililitros']:
        if stock >= 1000:
            return round(stock / 1000, 2), 'L'
        else:
            return round(stock, 2), 'ml'
    elif unidad in ['l', 'litro', 'litros']:
        return round(stock, 2), 'L'
    elif unidad in ['pza', 'pieza', 'piezas']:
        return round(stock, 2), 'pz'
    elif unidad in ['kg', 'kilogramo', 'kilogramos']:
        return round(stock, 2), 'kg'
    else:
        return round(stock, 2), unidad


@proveedores_bp.route('/proveedores')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def proveedores():
    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Proveedor.query

    if buscar and buscar.strip() != "":
        query = query.filter(
            or_(
                Proveedor.nombre.ilike(f"%{buscar}%"),
                Proveedor.telefono.ilike(f"%{buscar}%"),
                Proveedor.email.ilike(f"%{buscar}%"),
                Proveedor.contacto.ilike(f"%{buscar}%")
            )
        )

    if estatus:
        query = query.filter(Proveedor.estatus == estatus)

    if orden == "az":
        query = query.order_by(Proveedor.nombre.asc())
    elif orden == "za":
        query = query.order_by(Proveedor.nombre.desc())

    proveedores = query.all()

    return render_template(
        "modulo-proveedores/modulo-proveedores.html",
        proveedores=proveedores
    )


@proveedores_bp.route('/registrarProveedores', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def agregarProveedores():
    form = forms.ProveedorForm()

    if form.validate_on_submit():
        errores = []
        
        proveedor_existente_nombre = Proveedor.query.filter_by(
            nombre=form.nombre.data
        ).first()
        
        if proveedor_existente_nombre:
            errores.append('Ya existe un proveedor con este nombre')
            form.nombre.errors.append('Ya existe un proveedor con este nombre')
        
        proveedor_existente_telefono = Proveedor.query.filter_by(
            telefono=form.telefono.data
        ).first()
        
        if proveedor_existente_telefono:
            errores.append('Ya existe un proveedor con este teléfono')
            form.telefono.errors.append('Ya existe un proveedor con este teléfono')
        
        proveedor_existente_email = Proveedor.query.filter_by(
            email=form.email.data
        ).first()
        
        if proveedor_existente_email:
            errores.append('Ya existe un proveedor con este email')
            form.email.errors.append('Ya existe un proveedor con este email')
        
        if errores:
            flash('No se pudo registrar el proveedor: ' + ', '.join(errores), 'error')
            return render_template('modulo-proveedores/agregarProveedores.html', form=form)
        
        nuevo_proveedor = Proveedor(
            nombre=form.nombre.data,
            telefono=form.telefono.data,
            email=form.email.data,
            direccion=form.direccion.data,
            contacto=form.contacto.data,
            notas=form.notas.data,
            estatus=form.estatus.data
        )
        
        db.session.add(nuevo_proveedor)
        db.session.commit()
        
        flash('Proveedor registrado exitosamente', 'success')
        return redirect(url_for('proveedores.proveedores'))
    
    return render_template(
        'modulo-proveedores/agregarProveedores.html',
        form=form
    )


@proveedores_bp.route('/detalleProveedor/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def detallesProveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    return render_template(
        'modulo-proveedores/detallesProveedor.html',
        proveedor=proveedor
    )


@proveedores_bp.route('/modificarProveedor/<int:id>', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def modificarProveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    form = forms.ProveedorForm(obj=proveedor)
    
    if form.validate_on_submit():
        errores = []
        
        nombre_duplicado = Proveedor.query.filter(
            Proveedor.nombre == form.nombre.data,
            Proveedor.id_proveedor != id
        ).first()
        
        if nombre_duplicado:
            errores.append('Ya existe otro proveedor con este nombre')
            form.nombre.errors.append('Ya existe otro proveedor con este nombre')
        
        telefono_duplicado = Proveedor.query.filter(
            Proveedor.telefono == form.telefono.data,
            Proveedor.id_proveedor != id
        ).first()
        
        if telefono_duplicado:
            errores.append('Ya existe otro proveedor con este teléfono')
            form.telefono.errors.append('Ya existe otro proveedor con este teléfono')
        
        email_duplicado = Proveedor.query.filter(
            Proveedor.email == form.email.data,
            Proveedor.id_proveedor != id
        ).first()
        
        if email_duplicado:
            errores.append('Ya existe otro proveedor con este email')
            form.email.errors.append('Ya existe otro proveedor con este email')
        
        if errores:
            flash('No se pudo actualizar el proveedor: ' + ', '.join(errores), 'error')
            return render_template('modulo-proveedores/editarProveedor.html', form=form, proveedor=proveedor)
        
        proveedor.nombre = form.nombre.data
        proveedor.telefono = form.telefono.data
        proveedor.email = form.email.data
        proveedor.direccion = form.direccion.data
        proveedor.contacto = form.contacto.data
        proveedor.notas = form.notas.data
        proveedor.estatus = form.estatus.data
        
        db.session.commit()
        
        flash('Proveedor actualizado exitosamente', 'success')
        return redirect(url_for('proveedores.proveedores'))
    
    return render_template('modulo-proveedores/modificarProveedor.html', form=form, proveedor=proveedor)


@proveedores_bp.route('/eliminarProveedor/<int:id>', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
def eliminarProveedor(id):
    proveedor = Proveedor.query.get_or_404(id)

    if request.method == 'POST':
        if proveedor.estatus == "inactivo":
            flash("Este proveedor ya está desactivado.", "warning")
            return redirect(url_for('proveedores.proveedores'))

        proveedor.estatus = "inactivo"
        db.session.commit()

        flash("Proveedor desactivado correctamente.", "success")
        return redirect(url_for('proveedores.proveedores'))

    return render_template(
        'modulo-proveedores/eliminarProveedor.html',
        proveedor=proveedor
    )


@proveedores_bp.route("/compras", methods=["GET", "POST"])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def compraProveedores():
    proveedores = Proveedor.query.filter_by(estatus="activo").all()
    sucursales = Sucursal.query.filter_by(estatus="activo").all()
    compras_pendientes = Compra.query.filter_by(estado="solicitada").all()
    
    filas = 1
    proveedor_id = request.form.get("proveedor") or request.args.get("proveedor")
    datos_form = {}

    if request.method == "POST":
        accion = request.form.get("accion")
        datos_form = request.form.to_dict()
        filas = int(request.form.get("num_filas", 1))

        if accion == "agregar_fila":
            filas += 1
           
        elif accion == "guardar":
            try:
                id_proveedor = request.form.get("proveedor")
                id_sucursal = request.form.get("sucursal")
                fecha_estimada = request.form.get("fecha_estimada_entrega")
                notas = request.form.get("notas")

                if not id_proveedor or not id_sucursal or not fecha_estimada:
                    flash("Faltan datos obligatorios", "danger")
                    return redirect(url_for("proveedores.compraProveedores"))

                compra = Compra(
                    id_proveedor=id_proveedor,
                    id_sucursal=id_sucursal,
                    fecha_estimada_entrega=datetime.strptime(fecha_estimada, '%Y-%m-%d').date(),
                    estado="solicitada",
                    notas=notas,
                    total=0.0
                )

                db.session.add(compra)
                db.session.flush()

                for i in range(filas):
                    materia_id = request.form.get(f"materia_id_{i}")
                    tipo_compra = request.form.get(f"tipo_compra_{i}")
                    
                    if not materia_id or not tipo_compra:
                        continue
                    
                    detalle = DetalleCompra(
                        id_compra=compra.id_compra,
                        id_materia=materia_id,
                        tipo_compra=tipo_compra
                    )

                    # ===== GRANEL =====
                    if tipo_compra == 'granel':
                        cantidad = request.form.get(f"cantidad_granel_{i}")
                        unidad = request.form.get(f"unidad_granel_{i}")

                        if cantidad:
                            detalle.cantidad_granel = float(cantidad)
                            detalle.unidad_granel = unidad

                    # ===== PIEZAS (CORREGIDO) =====
                    elif tipo_compra == 'piezas':
                        cantidad = request.form.get(f"cantidad_piezas_{i}")
                        tipo_empaque = request.form.get(f"tipo_empaque_piezas_{i}")
                        contenido = request.form.get(f"contenido_pieza_{i}")
                        unidad_contenido = request.form.get(f"unidad_contenido_pieza_{i}")

                        if cantidad and cantidad.strip():
                            detalle.cantidad_empaques = float(cantidad)
                            detalle.tipo_empaque = tipo_empaque or "bolsa"
                            detalle.contenido_empaque = float(contenido) if contenido else 1
                            detalle.unidad_contenido = unidad_contenido or "pza"
                        else:
                            flash(f"La cantidad es obligatoria para el producto #{i+1}", "danger")
                            return redirect(url_for("proveedores.compraProveedores"))

                    # ===== CAJA (CORREGIDO) =====
                    elif tipo_compra == 'caja':
                        cantidad_cajas = request.form.get(f"cantidad_cajas_{i}")
                        piezas_por_caja = request.form.get(f"piezas_por_caja_{i}")
                        contenido = request.form.get(f"contenido_pieza_caja_{i}")
                        unidad_contenido = request.form.get(f"unidad_contenido_caja_{i}")

                        if cantidad_cajas:
                            detalle.cantidad_cajas = float(cantidad_cajas)
                            detalle.piezas_por_caja = int(piezas_por_caja) if piezas_por_caja else 1
                            detalle.contenido_por_pieza = float(contenido) if contenido else 0
                            detalle.unidad_contenido_caja = unidad_contenido or "g"

                    db.session.add(detalle)

                db.session.commit()
                flash("Orden guardada correctamente", "success")
                return redirect(url_for("proveedores.compraProveedores"))

            except Exception as e:
                db.session.rollback()
                flash(f"Error al guardar: {str(e)}", "danger")

    materias = []
    if proveedor_id:
        materias = MateriaPrima.query.filter_by(
            id_proveedor=proveedor_id,
            estatus="activo"
        ).all()

    return render_template(
        "modulo-proveedores/compraProveedores.html",
        proveedores=proveedores,
        sucursales=sucursales,
        materias=materias,
        proveedor_id=proveedor_id,
        filas=filas,
        today=date.today(),
        compras_pendientes=compras_pendientes,
        datos_form=datos_form
    )


@proveedores_bp.route("/detalle_compras")
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def detalleCompra():
    sucursal_id = request.args.get("sucursal")

    query = Compra.query.filter(
        Compra.estado.in_(["recibida", "cancelada"])
    )

    if sucursal_id and sucursal_id.isdigit():
        query = query.filter(Compra.id_sucursal == int(sucursal_id))

    compras = query.order_by(Compra.id_compra.desc()).all()
    sucursales = Sucursal.query.filter_by(estatus='activo').all()

    return render_template(
        "modulo-proveedores/detalleCompra.html",
        compras=compras,
        sucursales=sucursales,
        sucursal_id=sucursal_id
    )


@proveedores_bp.route("/detalle_compras/<int:id>")
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def ver_detalle_especifico(id):
    compra = Compra.query.options(
        joinedload(Compra.detalles).joinedload(DetalleCompra.materia),
        joinedload(Compra.proveedor)
    ).get_or_404(id)
    
    return render_template(
        "modulo-proveedores/verProductos.html", 
        compra=compra
    )


@proveedores_bp.route("/cancelar_compra/<int:id>")
@login_required
@login_required_with_message
@gerente_or_admin_required
def cancelar_compra(id):
    compra = Compra.query.get_or_404(id)

    if compra.estado == "recibida":
        flash("No puedes cancelar una compra ya recibida", "danger")
        return redirect(url_for("proveedores.compraProveedores"))

    compra.estado = "cancelada"
    compra.fecha_entrega = datetime.now()

    db.session.commit()

    flash("Compra cancelada correctamente", "warning")
    return redirect(url_for("proveedores.detalleCompra"))


@proveedores_bp.route("/recibir_compra/<int:id>", methods=["GET", "POST"])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def recibir_compra(id):
    from datetime import datetime
    from flask_login import current_user
    from models import HistorialPreciosMateriaPrima

    compra = Compra.query.options(
        joinedload(Compra.detalles).joinedload(DetalleCompra.materia),
        joinedload(Compra.proveedor),
        joinedload(Compra.sucursal)
    ).get_or_404(id)

    if compra.estado == "recibida":
        flash("Esta compra ya fue recibida", "warning")
        return redirect(url_for("proveedores.detalleCompra"))

    if request.method == "POST":
        try:
            total = 0

            if not compra.detalles:
                raise Exception("La compra no tiene detalles")

            for d in compra.detalles:

                precio_str = request.form.get(f"precio_{d.id_detalle}")
                fecha_caducidad_str = request.form.get(f"fecha_caducidad_{d.id_detalle}")

                if not precio_str:
                    raise Exception(f"Falta el precio en el producto ID {d.id_detalle}")

                precio_unitario = float(precio_str)

                if precio_unitario <= 0:
                    raise Exception("El precio debe ser mayor a 0")

                d.precio_unitario_compra = precio_unitario

                # ===== LOTE =====
                fecha_str = datetime.now().strftime('%Y%m%d')

                if d.tipo_compra == 'granel':
                    prefijo = 'GRL'
                elif d.tipo_compra == 'piezas':
                    prefijo = 'EMP'
                elif d.tipo_compra == 'caja':
                    prefijo = 'CAJ'
                else:
                    prefijo = 'LOT'

                d.lote = f"{prefijo}-{fecha_str}-{str(d.id_detalle).zfill(4)}"

                # ===== FECHA CADUCIDAD =====
                d.fecha_caducidad = datetime.strptime(
                    fecha_caducidad_str, '%Y-%m-%d'
                ).date() if fecha_caducidad_str else None

                # ===== CALCULAR STOCK (CORREGIDO) =====
                if d.tipo_compra == 'granel':
                    cantidad_stock = d.cantidad_granel or 0
                    if d.unidad_granel in ['kg', 'l']:
                        cantidad_stock *= 1000
                    cantidad = d.cantidad_granel or 0

                elif d.tipo_compra == 'piezas':
                    cantidad_stock = (d.cantidad_empaques or 0) * (d.contenido_empaque or 0)

                    if d.unidad_contenido in ['kg', 'l']:
                        cantidad_stock *= 1000

                    cantidad = d.cantidad_empaques or 0

                else:  # caja
                    piezas_totales = (d.cantidad_cajas or 0) * (d.piezas_por_caja or 0)
                    cantidad_stock = piezas_totales * (d.contenido_por_pieza or 0)

                    if d.unidad_contenido_caja in ['kg', 'l']:
                        cantidad_stock *= 1000

                    cantidad = d.cantidad_cajas or 0

                d.subtotal = precio_unitario * cantidad
                total += d.subtotal

                # ===== INVENTARIO =====
                inventario = InventarioMateriaPrima.query.filter_by(
                    id_materia=d.id_materia,
                    id_sucursal=compra.id_sucursal
                ).first()

                if not inventario:
                    inventario = InventarioMateriaPrima(
                        id_materia=d.id_materia,
                        id_sucursal=compra.id_sucursal,
                        stock_actual=0,
                        stock_minimo=0
                    )
                    db.session.add(inventario)
                    db.session.flush()

                stock_antes = inventario.stock_actual
                inventario.stock_actual += cantidad_stock
                inventario.lote = d.lote
                inventario.fecha_caducidad = d.fecha_caducidad

                # ===== MOVIMIENTO =====
                movimiento = MovimientoInventario(
                    id_materia=d.id_materia,
                    id_sucursal=compra.id_sucursal,
                    tipo="entrada",
                    cantidad=cantidad_stock,
                    stock_antes=stock_antes,
                    stock_despues=inventario.stock_actual,
                    referencia=f"Compra #{compra.id_compra}",
                    lote=d.lote,
                    fecha_caducidad=d.fecha_caducidad,
                    id_usuario=current_user.id_usuario if current_user.is_authenticated else None
                )
                db.session.add(movimiento)

            compra.total = total
            compra.estado = "recibida"
            compra.fecha_entrega = datetime.now()

            db.session.commit()

            flash(f"Compra recibida correctamente. Total: ${total:.2f}", "success")
            return redirect(url_for("proveedores.detalleCompra"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template(
        "modulo-proveedores/recibir.html",
        compra=compra,
        today=date.today()
    )


@proveedores_bp.route('/completar_compra/<int:id_compra>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def completar_compra(id_compra):
    from utils.costos_materia_prima import guardar_historial_precio
    
    compra = Compra.query.get_or_404(id_compra)
    
    compra.estado = "recibida"
    compra.fecha_entrega = datetime.utcnow()

    for detalle in compra.detalles:
        materia = MateriaPrima.query.get(detalle.id_materia)
        if materia and detalle.precio_unitario_compra:
            materia.precio_unitario = detalle.precio_unitario_compra
        
        guardar_historial_precio(detalle)
    
    try:
        db.session.commit()
        flash("Compra completada y precios de materia prima actualizados.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error al actualizar: " + str(e), "danger")
        
    return redirect(url_for('proveedores.detalleCompra'))


@proveedores_bp.route("/inventario_materia")
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def inventarioMateria():
    from datetime import date
    from utils.calculos import obtener_ultimo_costo_materia
    from models import HistorialPreciosMateriaPrima
    
    sucursales = Sucursal.query.filter_by(estatus='activo').all()
    sucursal_id = request.args.get('sucursal')

    if sucursal_id:
        inventario = InventarioMateriaPrima.query.filter_by(id_sucursal=sucursal_id).all()
    else:
        inventario = InventarioMateriaPrima.query.all()

    data = []
    materias_con_precio = 0
    valor_total_inventario = 0

    for i in inventario:
        unidad_base = i.materia.unidad_base if i.materia.unidad_base else 'unidad'
        stock_actual = i.stock_actual
        stock_minimo = i.stock_minimo or 0
        
        precio_unitario = obtener_ultimo_costo_materia(i.id_materia)
        tiene_precio = precio_unitario > 0
        
        if tiene_precio:
            materias_con_precio += 1
            valor_total_inventario += stock_actual * precio_unitario
        
        ultima_compra = HistorialPreciosMateriaPrima.query.filter_by(
            id_materia=i.id_materia
        ).order_by(HistorialPreciosMateriaPrima.fecha_compra.desc()).first()
        
        fecha_ultima_compra = ultima_compra.fecha_compra.strftime('%d/%m/%Y') if ultima_compra else None
        
        if unidad_base == 'g' and stock_actual >= 1000:
            stock_legible = stock_actual / 1000
            unidad_legible = 'kg'
            stock_minimo_legible = stock_minimo / 1000 if stock_minimo >= 1000 else stock_minimo
        elif unidad_base == 'ml' and stock_actual >= 1000:
            stock_legible = stock_actual / 1000
            unidad_legible = 'l'
            stock_minimo_legible = stock_minimo / 1000 if stock_minimo >= 1000 else stock_minimo
        else:
            stock_legible = stock_actual
            unidad_legible = unidad_base
            stock_minimo_legible = stock_minimo

        data.append({
            "id_materia": i.id_materia,
            "id_sucursal": i.id_sucursal,
            "id_proveedor": i.materia.id_proveedor if i.materia else None,
            "materia": i.materia.nombre,
            "sucursal": i.sucursal.nombre,
            "stock": round(stock_legible, 2),
            "stock_real": stock_actual,
            "stock_minimo": round(stock_minimo_legible, 2),
            "unidad_legible": unidad_legible,
            "tipo": unidad_base,
            "precio_unitario": precio_unitario,
            "tiene_precio": tiene_precio,
            "fecha_ultima_compra": fecha_ultima_compra
        })

    return render_template(
        "inventarioMateria/inventarioMateria.html",
        inventario=data,
        sucursales=sucursales,
        materias_con_precio=materias_con_precio,
        total_materias=len(data),
        valor_total_inventario=valor_total_inventario
    )


@proveedores_bp.route("/movimientos/<int:id_materia>/<int:id_sucursal>")
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def movimientosMateria(id_materia, id_sucursal):
    from datetime import date
    
    materia = MateriaPrima.query.get_or_404(id_materia)
    sucursal = Sucursal.query.get_or_404(id_sucursal)

    movimientos = MovimientoInventario.query.filter_by(
        id_materia=id_materia,
        id_sucursal=id_sucursal
    ).order_by(MovimientoInventario.fecha.desc()).all()

    hoy = date.today()

    return render_template(
        "inventarioMateria/movimientos.html",
        movimientos=movimientos,
        materia=materia,
        sucursal=sucursal,
        hoy=hoy
    )


@proveedores_bp.route("/ajustar_stock/<int:id_materia>/<int:id_sucursal>", methods=["GET", "POST"])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def ajustarStock(id_materia, id_sucursal):
    from flask_login import current_user
    
    materia = MateriaPrima.query.get_or_404(id_materia)
    sucursal = Sucursal.query.get_or_404(id_sucursal)
    
    inventario = InventarioMateriaPrima.query.filter_by(
        id_materia=id_materia,
        id_sucursal=id_sucursal
    ).first()
    
    if not inventario:
        inventario = InventarioMateriaPrima(
            id_materia=id_materia,
            id_sucursal=id_sucursal,
            stock_actual=0,
            stock_minimo=0
        )
        db.session.add(inventario)
        db.session.commit()
    
    if request.method == "POST":
        try:
            tipo = request.form.get("tipo")
            cantidad = float(request.form.get("cantidad"))
            id_proveedor = request.form.get("id_proveedor")
            motivo = request.form.get("motivo")
            
            if cantidad <= 0:
                raise Exception("La cantidad debe ser mayor a 0")
            
            stock_antes = inventario.stock_actual
            
            if tipo == "entrada":
                inventario.stock_actual += cantidad
                cantidad_movimiento = cantidad
            elif tipo == "salida":
                if inventario.stock_actual < cantidad:
                    raise Exception(f"Stock insuficiente. Stock actual: {stock_antes}")
                inventario.stock_actual -= cantidad
                cantidad_movimiento = -cantidad
            else:
                raise Exception("Tipo de movimiento inválido")
            
            stock_despues = inventario.stock_actual
            
            movimiento = MovimientoInventario(
                id_materia=id_materia,
                id_sucursal=id_sucursal,
                tipo=tipo,
                cantidad=cantidad,
                stock_antes=stock_antes,
                stock_despues=stock_despues,
                id_proveedor=int(id_proveedor) if id_proveedor and id_proveedor.isdigit() else None,
                id_usuario=current_user.id_usuario if current_user.is_authenticated else None,
                motivo=motivo,
                referencia=f"Ajuste manual desde inventario"
            )
            db.session.add(movimiento)
            db.session.commit()
            
            flash(f"Movimiento registrado: {tipo} de {cantidad} unidades. Stock: {stock_antes} → {stock_despues}", "success")
            return redirect(url_for("proveedores.movimientosMateria", id_materia=id_materia, id_sucursal=id_sucursal))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    
    proveedores = Proveedor.query.filter_by(estatus='activo').all()
    
    return render_template(
        "inventarioMateria/ajustarStock.html",
        materia=materia,
        sucursal=sucursal,
        inventario=inventario,
        proveedores=proveedores
    )


@proveedores_bp.route("/mermas")
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def listar_mermas():
    sucursal_id = request.args.get('sucursal')
    materia_id = request.args.get('materia')
    
    query = Merma.query
    
    if sucursal_id and sucursal_id.isdigit():
        query = query.filter(Merma.id_sucursal == int(sucursal_id))
    
    if materia_id and materia_id.isdigit():
        query = query.filter(Merma.id_materia == int(materia_id))
    
    mermas = query.order_by(Merma.fecha_registro.desc()).all()
    sucursales = Sucursal.query.filter_by(estatus='activo').all()
    materias = MateriaPrima.query.filter_by(estatus='activo').all()
    
    return render_template(
        "inventarioMateria/mermas.html",
        mermas=mermas,
        sucursales=sucursales,
        materias=materias,
        sucursal_id=sucursal_id,
        materia_id=materia_id
    )


@proveedores_bp.route("/registrar_merma/<int:id_materia>/<int:id_sucursal>", methods=["GET", "POST"])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def registrar_merma(id_materia, id_sucursal):
    from flask_login import current_user
    from datetime import date, datetime
    
    materia = MateriaPrima.query.get_or_404(id_materia)
    sucursal = Sucursal.query.get_or_404(id_sucursal)
    
    inventario = InventarioMateriaPrima.query.filter_by(
        id_materia=id_materia,
        id_sucursal=id_sucursal
    ).first()
    
    if not inventario:
        inventario = InventarioMateriaPrima(
            id_materia=id_materia,
            id_sucursal=id_sucursal,
            stock_actual=0,
            stock_minimo=0
        )
        db.session.add(inventario)
        db.session.commit()
    
    lotes = {}
    movimientos_con_lote = MovimientoInventario.query.filter_by(
        id_materia=id_materia,
        id_sucursal=id_sucursal
    ).filter(
        MovimientoInventario.lote.isnot(None),
        MovimientoInventario.stock_despues > 0
    ).order_by(MovimientoInventario.fecha_caducidad.asc()).all()
    
    for movimiento in movimientos_con_lote:
        if movimiento.lote and movimiento.lote not in lotes:
            lotes[movimiento.lote] = {
                'lote': movimiento.lote,
                'fecha_caducidad': movimiento.fecha_caducidad,
                'stock': movimiento.stock_despues
            }
    
    if request.method == "POST":
        try:
            cantidad = float(request.form.get("cantidad"))
            motivo = request.form.get("motivo")
            lote_seleccionado = request.form.get("lote")
            fecha_caducidad = request.form.get("fecha_caducidad")
            
            if cantidad <= 0:
                raise Exception("La cantidad debe ser mayor a 0")
            
            if inventario.stock_actual < cantidad:
                raise Exception(f"Stock insuficiente. Stock actual: {inventario.stock_actual}")
            
            stock_antes = inventario.stock_actual
            inventario.stock_actual -= cantidad
            stock_despues = inventario.stock_actual
            
            merma = Merma(
                id_materia=id_materia,
                id_sucursal=id_sucursal,
                cantidad=cantidad,
                unidad=materia.unidad_base,
                motivo=motivo,
                fecha_caducidad=datetime.strptime(fecha_caducidad, '%Y-%m-%d').date() if fecha_caducidad else None,
                registrado_por=current_user.email if current_user.is_authenticated else "sistema"
            )
            db.session.add(merma)
            db.session.flush()
            
            movimiento = MovimientoInventario(
                id_materia=id_materia,
                id_sucursal=id_sucursal,
                tipo="merma",
                cantidad=cantidad,
                stock_antes=stock_antes,
                stock_despues=stock_despues,
                motivo=motivo,
                lote=lote_seleccionado,
                fecha_caducidad=datetime.strptime(fecha_caducidad, '%Y-%m-%d').date() if fecha_caducidad else None,
                referencia=f"Merma #{merma.id_merma} - {motivo[:50]}",
                id_usuario=current_user.id_usuario if current_user.is_authenticated else None
            )
            db.session.add(movimiento)
            db.session.commit()
            
            flash(f"Merma registrada: {cantidad} {materia.unidad_base} - {motivo}", "success")
            return redirect(url_for("proveedores.movimientosMateria", id_materia=id_materia, id_sucursal=id_sucursal))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template(
        "inventarioMateria/registrar_merma.html",
        materia=materia,
        sucursal=sucursal,
        inventario=inventario,
        lotes=lotes,
        today=date.today()
    )


@proveedores_bp.route("/proximos_vencer")
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
@empleado_required
def proximos_vencer():
    from datetime import date, timedelta
    
    sucursal_id = request.args.get('sucursal')
    dias = request.args.get('dias', 7, type=int)
    
    fecha_limite = date.today() + timedelta(days=dias)
    
    query = InventarioMateriaPrima.query.filter(
        InventarioMateriaPrima.fecha_caducidad <= fecha_limite,
        InventarioMateriaPrima.fecha_caducidad >= date.today(),
        InventarioMateriaPrima.stock_actual > 0
    )
    
    if sucursal_id:
        query = query.filter(InventarioMateriaPrima.id_sucursal == sucursal_id)
    
    productos = query.order_by(InventarioMateriaPrima.fecha_caducidad).all()
    sucursales = Sucursal.query.filter_by(estatus='activo').all()
    
    data = []
    for p in productos:
        data.append({
            "id_materia": p.id_materia,
            "id_sucursal": p.id_sucursal,
            "materia": p.materia.nombre,
            "sucursal": p.sucursal.nombre,
            "stock": p.stock_actual,
            "lote": p.lote,
            "fecha_caducidad": p.fecha_caducidad,
            "dias_restantes": (p.fecha_caducidad - date.today()).days
        })
    
    return render_template(
        "inventarioMateria/proximos_vencer.html",
        productos=data,
        sucursales=sucursales,
        dias=dias,
        sucursal_id=sucursal_id,
        today=date.today()
    )