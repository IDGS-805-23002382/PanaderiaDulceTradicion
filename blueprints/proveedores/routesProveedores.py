from flask import Flask, render_template, request, redirect, url_for, flash
from models import Proveedor, db, MateriaPrima, Compra, DetalleCompra, Sucursal, MovimientoInventario, InventarioMateriaPrima
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from . import proveedores_bp
from flask import jsonify

from datetime import date, datetime
import forms

# ===== FUNCIONES DE CONVERSIÓN (directamente aquí) =====

def convertir_a_unidad_legible(cantidad, unidad_origen):
    """Convierte de unidad base a unidad legible para mostrar"""
    if not cantidad:
        return 0, unidad_origen
    
    unidad = str(unidad_origen).lower().strip()
    cantidad_float = float(cantidad)
    
    if unidad in ['ml', 'mililitro', 'mililitros'] and cantidad_float >= 1000:
        return cantidad_float / 1000, 'l'
    if unidad in ['g', 'gramo', 'gramos'] and cantidad_float >= 1000:
        return cantidad_float / 1000, 'kg'
    if unidad in ['ml', 'mililitro', 'mililitros'] and cantidad_float < 1000:
        return cantidad_float, 'ml'
    if unidad in ['g', 'gramo', 'gramos'] and cantidad_float < 1000:
        return cantidad_float, 'g'
    if unidad in ['l', 'litro', 'litros']:
        return cantidad_float, 'l'
    if unidad in ['kg', 'kilogramo', 'kilogramos']:
        return cantidad_float, 'kg'
    if unidad in ['pz', 'pieza', 'piezas', 'pza']:
        return cantidad_float, 'pz'
    
    return cantidad_float, unidad_origen


def calcular_equivalente(materia, stock_actual):
    """Calcula cuántas cajas y piezas hay en el stock"""
    try:
        if not materia:
            return 0, 0, 0
            
        piezas_por_caja = float(materia.piezas_por_caja) if materia.piezas_por_caja else 1
        peso_por_pieza = float(materia.peso_por_pieza) if materia.peso_por_pieza else 1
        
        unidad = (materia.unidad_contenido or '').lower().strip()
        
        if unidad in ['ml', 'g']:
            stock_en_piezas = stock_actual / peso_por_pieza if peso_por_pieza > 0 else 0
        elif unidad in ['l', 'kg']:
            stock_en_unidad_base = stock_actual * 1000
            stock_en_piezas = stock_en_unidad_base / peso_por_pieza if peso_por_pieza > 0 else 0
        else:
            stock_en_piezas = stock_actual
        
        if piezas_por_caja > 0:
            cajas = int(stock_en_piezas // piezas_por_caja)
            sobrantes = int(stock_en_piezas % piezas_por_caja)
        else:
            cajas = 0
            sobrantes = int(stock_en_piezas)
        
        return cajas, sobrantes, int(stock_en_piezas)
        
    except Exception as e:
        print(f"Error: {e}")
        return 0, 0, 0
    
@proveedores_bp.route('/proveedores')
def proveedores():
    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Proveedor.query

    # BUSCAR
    if buscar and buscar.strip() != "":
        query = query.filter(
            or_(
                Proveedor.nombre.ilike(f"%{buscar}%"),
                Proveedor.telefono.ilike(f"%{buscar}%"),
                Proveedor.email.ilike(f"%{buscar}%"),
                Proveedor.contacto.ilike(f"%{buscar}%")
            )
        )

    # FILTRAR POR ESTATUS
    if estatus:
        query = query.filter(Proveedor.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(Proveedor.nombre.asc())
    elif orden == "za":
        query = query.order_by(Proveedor.nombre.desc())

    proveedores = query.all()

    return render_template(
        "modulo-proveedores/modulo-proveedores.html",
        proveedores=proveedores
    )


# Agregar
@proveedores_bp.route('/registrarProveedores', methods=['GET','POST'])
def agregarProveedores():
    form = forms.ProveedorForm()

    if form.validate_on_submit():
        # Verificar duplicados
        errores = []
        
        # Verificar nombre duplicado
        proveedor_existente_nombre = Proveedor.query.filter_by(
            nombre=form.nombre.data
        ).first()
        
        if proveedor_existente_nombre:
            errores.append('Ya existe un proveedor con este nombre')
            form.nombre.errors.append('Ya existe un proveedor con este nombre')
        
        # Verificar teléfono duplicado
        proveedor_existente_telefono = Proveedor.query.filter_by(
            telefono=form.telefono.data
        ).first()
        
        if proveedor_existente_telefono:
            errores.append('Ya existe un proveedor con este teléfono')
            form.telefono.errors.append('Ya existe un proveedor con este teléfono')
        
        # Verificar email duplicado
        proveedor_existente_email = Proveedor.query.filter_by(
            email=form.email.data
        ).first()
        
        if proveedor_existente_email:
            errores.append('Ya existe un proveedor con este email')
            form.email.errors.append('Ya existe un proveedor con este email')
        
        # Si hay errores, regresar al formulario
        if errores:
            flash('No se pudo registrar el proveedor: ' + ', '.join(errores), 'error')
            return render_template('modulo-proveedores/agregarProveedores.html', form=form)
        
        # Si no hay duplicados, crear el nuevo proveedor
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
def detallesProveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    return render_template(
        'modulo-proveedores/detallesProveedor.html',
        proveedor=proveedor
    )


@proveedores_bp.route('/modificarProveedor/<int:id>', methods=['GET', 'POST'])
def modificarProveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    form = forms.ProveedorForm(obj=proveedor)
    
    if form.validate_on_submit():
        errores = []
        
        # Verificar nombre duplicado (excluyendo el proveedor actual)
        nombre_duplicado = Proveedor.query.filter(
            Proveedor.nombre == form.nombre.data,
            Proveedor.id_proveedor != id
        ).first()
        
        if nombre_duplicado:
            errores.append('Ya existe otro proveedor con este nombre')
            form.nombre.errors.append('Ya existe otro proveedor con este nombre')
        
        # Verificar teléfono duplicado
        telefono_duplicado = Proveedor.query.filter(
            Proveedor.telefono == form.telefono.data,
            Proveedor.id_proveedor != id
        ).first()
        
        if telefono_duplicado:
            errores.append('Ya existe otro proveedor con este teléfono')
            form.telefono.errors.append('Ya existe otro proveedor con este teléfono')
        
        # Verificar email duplicado
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
        
        # Actualizar datos
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
def eliminarProveedor(id):
    proveedor = Proveedor.query.get_or_404(id)

    if request.method == 'POST':
        # validar si ya esta inactivo
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
def compraProveedores():
    proveedores = Proveedor.query.filter_by(estatus="activo").all()
    sucursales = Sucursal.query.filter_by(estatus="activo").all()
    compras_pendientes = Compra.query.filter_by(estado="solicitada").all()
    
    # Valores por defecto
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

                compra = Compra(
                    id_proveedor=id_proveedor,
                    id_sucursal=id_sucursal,
                    fecha_estimada_entrega=datetime.strptime(fecha_estimada, '%Y-%m-%d').date(),
                    estado="solicitada",
                    notas=notas
                )

                db.session.add(compra)
                db.session.flush()

                for i in range(filas):
                    materia_id = request.form.get(f"materia_id_{i}")
                    cantidad = request.form.get(f"cantidad_{i}")
                    tipo = request.form.get(f"tipo_{i}")

                    if materia_id and cantidad:
                        detalle = DetalleCompra(
                            id_compra=compra.id_compra,
                            id_materia=materia_id,
                            cantidad=float(cantidad),
                            tipo_empaque=tipo
                        )
                        db.session.add(detalle)

                db.session.commit()
                flash("Orden guardada correctamente", "success")
                return redirect(url_for("proveedores.compraProveedores"))

            except Exception as e:
                db.session.rollback()
                flash(f"Error: {str(e)}", "danger")

    
    materias = []
    if proveedor_id:
        materias = MateriaPrima.query.filter_by(id_proveedor=proveedor_id, estatus="activo").all()

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
    
@proveedores_bp.route("/compras_recibidas")
def comprasRecibidas():
    compras = Compra.query.filter_by(estado="recibida").all()
    return render_template(
        "modulo-proveedores/detalleCompra.html",
        compras=compras
    )
    
@proveedores_bp.route("/detalle_compras")
def detalleCompra():
    sucursal_id = request.args.get("sucursal")

    query = Compra.query.filter(
        Compra.estado.in_(["recibida", "cancelada"])
    )

    # FILTRO POR SUCURSAL
    if sucursal_id and sucursal_id.isdigit():
        query = query.filter(Compra.id_sucursal == int(sucursal_id))

    compras = query.order_by(Compra.id_compra.desc()).all()

    # NECESARIO para el select
    sucursales = Sucursal.query.filter_by(estatus='activo').all()

    return render_template(
        "modulo-proveedores/detalleCompra.html",
        compras=compras,
        sucursales=sucursales,
        sucursal_id=sucursal_id
    )
    


@proveedores_bp.route("/detalle_compras/<int:id>")
def ver_detalle_especifico(id):
    # Cargamos la compra y sus detalles, incluyendo la relación 'materia' definida en tu modelo
    compra = Compra.query.options(
        joinedload(Compra.detalles).joinedload(DetalleCompra.materia),
        joinedload(Compra.proveedor)
    ).get_or_404(id)
    
    return render_template(
        "modulo-proveedores/verProductos.html", 
        compra=compra
    )
    
@proveedores_bp.route("/cancelar_compra/<int:id>")
def cancelar_compra(id):
    from datetime import datetime

    compra = Compra.query.get_or_404(id)

    if compra.estado == "recibida":
        flash("No puedes cancelar una compra ya recibida", "danger")
        return redirect(url_for("proveedores.compraProveedores"))

    compra.estado = "cancelada"
    compra.fecha_entrega = datetime.now()

    db.session.commit()

    flash("Compra cancelada correctamente", "warning")
    return redirect(url_for("proveedores.detalleCompra"))

def convertir_a_stock(materia, cantidad, tipo_empaque):

    piezas_por_caja = materia.piezas_por_caja or 1
    peso_por_pieza = materia.peso_por_pieza or 0

    # convertir a piezas
    if tipo_empaque == "caja":
        piezas = cantidad * piezas_por_caja
    else:
        piezas = cantidad

    # convertir a peso si aplica
    if peso_por_pieza > 0:
        return piezas * peso_por_pieza  # kg
    else:
        return piezas  # unidades

@proveedores_bp.route("/recibir_compra/<int:id>", methods=["GET", "POST"])
def recibir_compra(id):
    from datetime import datetime

    compra = Compra.query.get_or_404(id)

    if compra.estado == "recibida":
        flash("Esta compra ya fue recibida", "warning")
        return redirect(url_for("proveedores.detalleCompra"))

    if request.method == "POST":
        try:
            total = 0

            for d in compra.detalles:
                precio_str = request.form.get(f"precio_{d.id_detalle}")
                if not precio_str:
                    raise Exception("Debes ingresar todos los precios")

                precio_unitario = float(precio_str)
                if precio_unitario <= 0:
                    raise Exception("El precio debe ser mayor a 0")

                d.precio_unitario_compra = precio_unitario
                d.subtotal = precio_unitario * d.cantidad
                total += d.subtotal

                # ==========================================
                # INVENTARIO CORRECTO (AQUÍ ESTÁ LA MAGIA)
                # ==========================================
                materia = d.materia
                unidad = (materia.unidad_contenido or "").lower()

                piezas_por_caja = materia.piezas_por_caja or 1
                contenido = materia.contenido_por_unidad or 1   # CLAVE (ej: 4 litros)

                # 1. CALCULAR PIEZAS
                if d.tipo_empaque == "caja":
                    piezas = d.cantidad * piezas_por_caja
                else:
                    piezas = d.cantidad

                #  2. CONVERTIR SEGÚN TIPO

                #  LIQUIDOS → litros a ml
                if unidad in ["litros", "ml"]:
                    cantidad_stock = piezas * contenido * 1000

                # PESO
                elif materia.peso_por_pieza and materia.peso_por_pieza > 0:
                    cantidad_stock = piezas * materia.peso_por_pieza

                #  PIEZAS
                else:
                    cantidad_stock = piezas

                # ==========================================
                #  INVENTARIO DB
                # ==========================================
                inventario = InventarioMateriaPrima.query.filter_by(
                    id_materia=materia.id_materia,
                    id_sucursal=compra.id_sucursal
                ).first()

                if not inventario:
                    inventario = InventarioMateriaPrima(
                        id_materia=materia.id_materia,
                        id_sucursal=compra.id_sucursal,
                        stock_actual=0,
                        stock_minimo=0
                    )
                    db.session.add(inventario)
                    db.session.flush()

                stock_antes = inventario.stock_actual
                inventario.stock_actual += cantidad_stock
                stock_despues = inventario.stock_actual

                # ==========================================
                #  KARDEX
                # ==========================================
                movimiento = MovimientoInventario(
                    id_materia=materia.id_materia,
                    id_sucursal=compra.id_sucursal,
                    tipo="entrada",
                    cantidad=cantidad_stock,
                    stock_antes=stock_antes,
                    stock_despues=stock_despues,
                    referencia=f"Compra #{compra.id_compra} - Proveedor: {compra.proveedor.nombre}"
                )
                db.session.add(movimiento)

            # ==========================================
            #  FINALIZAR
            # ==========================================
            compra.total = total
            compra.estado = "recibida"
            compra.fecha_entrega = datetime.now()

            db.session.commit()

            flash(f"Compra recibida correctamente. Total: ${total:.2f}", "success")
            return redirect(url_for("proveedores.detalleCompra"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template("modulo-proveedores/recibir.html", compra=compra)

def calcular_equivalente(materia, stock):

    piezas_por_caja = materia.piezas_por_caja or 1
    peso_por_pieza = materia.peso_por_pieza or 0
    
    if peso_por_pieza > 0:
        piezas_totales = stock / peso_por_pieza
    else:
        piezas_totales = stock

    cajas = int(piezas_totales // piezas_por_caja)
    sobrantes = piezas_totales % piezas_por_caja

    return cajas, sobrantes, piezas_totales

@proveedores_bp.route('/completar_compra/<int:id_compra>')
def completar_compra(id_compra):
    compra = Compra.query.get_or_404(id_compra)
    
    # Supongamos que aquí validas que la compra pase a estado "recibida"
    compra.estado = "recibida"
    compra.fecha_entrega = datetime.utcnow()

    # Iteramos los productos comprados para actualizar su precio en el catálogo
    for detalle in compra.detalles:
        materia = MateriaPrima.query.get(detalle.id_materia)
        if materia and detalle.precio_unitario_compra:
            # Actualizamos el precio unitario con el de la última compra
            materia.precio_unitario = detalle.precio_unitario_compra
    
    try:
        db.session.commit()
        flash("Compra completada y precios de materia prima actualizados.")
    except Exception as e:
        db.session.rollback()
        flash("Error al actualizar: " + str(e))
        
    return redirect(url_for('proveedores.detalleCompra'))

def convertir_a_unidad_legible(stock, unidad):

    if unidad == "L":
        if stock >= 1000:
            return stock / 1000, "ml"
        else:
            return stock, "L"

    return stock, unidad

@proveedores_bp.route("/inventario_materia")
def inventarioMateria():
    sucursales = Sucursal.query.filter_by(estatus='activo').all()
    sucursal_id = request.args.get('sucursal')

    if sucursal_id:
        inventario = InventarioMateriaPrima.query.filter_by(id_sucursal=sucursal_id).all()
    else:
        inventario = InventarioMateriaPrima.query.all()

    data = []

    for i in inventario:
        #  STOCK SIEMPRE EN ML (BASE)
        stock_base = i.stock_actual  

        #  CONVERTIR A VISUAL (L o ml)
        stock_legible, unidad_legible = convertir_a_unidad_legible(
            stock_base,
            i.materia.unidad_contenido
        )

        #  CAJAS Y PIEZAS (si aplica)
        cajas, sobrantes, piezas_totales = calcular_equivalente(
            i.materia,
            stock_base
        )

        data.append({
            "id_materia": i.id_materia,
            "id_sucursal": i.id_sucursal,
            "materia": i.materia.nombre,
            "sucursal": i.sucursal.nombre,
            "stock": round(stock_legible, 2),
            "stock_real": stock_base,  #  SIEMPRE EN ML
            "unidad_legible": unidad_legible,
            "cajas": cajas,
            "sobrantes": sobrantes,
            "piezas_totales": piezas_totales,
            "tipo": i.materia.unidad_contenido,
        })

    return render_template(
        "inventarioMateria/inventarioMateria.html",
        inventario=data,
        sucursales=sucursales
    )


@proveedores_bp.route("/movimientos/<int:id_materia>/<int:id_sucursal>")
def movimientosMateria(id_materia, id_sucursal):
    # Obtener materia y sucursal
    materia = MateriaPrima.query.get_or_404(id_materia)
    sucursal = Sucursal.query.get_or_404(id_sucursal)

    # Movimientos ordenados por fecha (tipo kardex)
    movimientos = MovimientoInventario.query.filter_by(
        id_materia=id_materia,
        id_sucursal=id_sucursal
    ).order_by(MovimientoInventario.fecha.desc()).all()

    return render_template(
        "inventarioMateria/movimientos.html",
        movimientos=movimientos,
        materia=materia,
        sucursal=sucursal
    )
    
@proveedores_bp.route("/ajustar_stock/<int:id_materia>/<int:id_sucursal>", methods=["GET", "POST"])
def ajustarStock(id_materia, id_sucursal):
    from flask_login import current_user
    
    materia = MateriaPrima.query.get_or_404(id_materia)
    sucursal = Sucursal.query.get_or_404(id_sucursal)
    
    # Buscar inventario actual
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
            
            # Guardar stock antes
            stock_antes = inventario.stock_actual
            
            # Actualizar stock según tipo
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
            
            # Guardar stock después
            stock_despues = inventario.stock_actual
            
            # Registrar movimiento
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
    
    # Obtener proveedores para el select
    proveedores = Proveedor.query.filter_by(estatus='activo').all()
    
    return render_template(
        "inventarioMateria/ajustarStock.html",
        materia=materia,
        sucursal=sucursal,
        inventario=inventario,
        proveedores=proveedores
    )