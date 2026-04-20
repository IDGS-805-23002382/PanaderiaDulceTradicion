import datetime

from flask import app, current_app, render_template, request, redirect, url_for, flash
from models import Receta, Producto, DetalleReceta, MateriaPrima, db, DetalleReceta
from utils.calculos import obtener_costo_unitario_base
from utils.precios import calcular_y_guardar_precio_materia
from models import db, HistorialPreciosMateriaPrima, MateriaPrima, DetalleCompra
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message
from flask_login import login_required
from sqlalchemy import or_

from . import recetas_bp
import forms

def obtener_ultimo_costo_materia(id_materia):
    """
    Obtiene el costo más reciente de una materia prima desde el historial
    Retorna el costo por unidad base (g, ml, o pza)
    """
    try:
        materia = MateriaPrima.query.get(id_materia)
        if not materia:
            return 0.0
        
        # Obtener el último precio del historial
        ultimo_precio = HistorialPreciosMateriaPrima.query.filter_by(
            id_materia=id_materia
        ).order_by(HistorialPreciosMateriaPrima.fecha_compra.desc()).first()
        
        if not ultimo_precio:
            return 0.0
        
        # Retornar el precio según la unidad base de la materia
        if materia.unidad_base == 'g':
            return float(ultimo_precio.precio_por_gramo)
        elif materia.unidad_base == 'ml':
            return float(ultimo_precio.precio_por_ml)
        elif materia.unidad_base == 'pza':
            return float(ultimo_precio.precio_por_pieza)
        else:
            return 0.0
            
    except Exception as e:
        current_app.logger.error(f"Error obteniendo costo de materia {id_materia}: {e}")
        return 0.0


def obtener_detalle_ultima_compra(id_materia):
    """
    Obtiene información detallada de la última compra de una materia prima
    """
    try:
        ultimo_precio = HistorialPreciosMateriaPrima.query.filter_by(
            id_materia=id_materia
        ).order_by(HistorialPreciosMateriaPrima.fecha_compra.desc()).first()
        
        if not ultimo_precio:
            return None
        
        return {
            'fecha': ultimo_precio.fecha_compra,
            'precio_por_gramo': float(ultimo_precio.precio_por_gramo),
            'precio_por_ml': float(ultimo_precio.precio_por_ml),
            'precio_por_pieza': float(ultimo_precio.precio_por_pieza),
            'cantidad_total': float(ultimo_precio.cantidad_total_base),
            'precio_total': float(ultimo_precio.precio_total)
        }
    except Exception as e:
        current_app.logger.error(f"Error obteniendo detalle de compra: {e}")
        return None


def actualizar_precios_de_compras():
    """
    Actualiza los precios en el historial basado en todas las compras existentes
    """
    with app.app_context():
        detalles = DetalleCompra.query.all()
        
        for detalle in detalles:
            materia = MateriaPrima.query.get(detalle.id_materia)
            if not materia:
                continue
            
            unidad_base = materia.unidad_base
            cantidad_base = 0
            
            # Calcular cantidad base
            if detalle.tipo_compra == 'caja':
                cantidad_cajas = float(detalle.cantidad_cajas) if detalle.cantidad_cajas else 0
                piezas_por_caja = float(detalle.piezas_por_caja) if detalle.piezas_por_caja else 1
                contenido = float(detalle.contenido_pieza_caja) if detalle.contenido_pieza_caja else 0
                unidad_contenido = (detalle.unidad_contenido_caja or 'g').lower()
                
                if unidad_contenido in ['g', 'kg']:
                    cantidad_base = cantidad_cajas * piezas_por_caja * contenido
                    if unidad_contenido == 'kg':
                        cantidad_base = cantidad_base * 1000
                elif unidad_contenido in ['ml', 'l']:
                    cantidad_base = cantidad_cajas * piezas_por_caja * contenido
                    if unidad_contenido == 'l':
                        cantidad_base = cantidad_base * 1000
                        
            elif detalle.tipo_compra == 'piezas':
                cantidad_piezas = float(detalle.cantidad_piezas) if detalle.cantidad_piezas else 0
                contenido = float(detalle.contenido_pieza) if detalle.contenido_pieza else 0
                unidad_contenido = (detalle.unidad_contenido_pieza or 'g').lower()
                
                if unidad_contenido in ['g', 'kg']:
                    cantidad_base = cantidad_piezas * contenido
                    if unidad_contenido == 'kg':
                        cantidad_base = cantidad_base * 1000
                elif unidad_contenido in ['ml', 'l']:
                    cantidad_base = cantidad_piezas * contenido
                    if unidad_contenido == 'l':
                        cantidad_base = cantidad_base * 1000
                        
            elif detalle.tipo_compra == 'granel':
                cantidad = float(detalle.cantidad_granel) if detalle.cantidad_granel else 0
                unidad = (detalle.unidad_granel or 'g').lower()
                
                if unidad in ['g', 'kg']:
                    cantidad_base = cantidad
                    if unidad == 'kg':
                        cantidad_base = cantidad_base * 1000
                elif unidad in ['ml', 'l']:
                    cantidad_base = cantidad
                    if unidad == 'l':
                        cantidad_base = cantidad_base * 1000
            
            # Calcular precio por unidad base
            if cantidad_base > 0 and detalle.subtotal:
                precio_unitario = float(detalle.subtotal) / cantidad_base
            else:
                precio_unitario = 0
            
            # Verificar si ya existe en el historial
            existe = HistorialPreciosMateriaPrima.query.filter_by(
                id_detalle_compra=detalle.id_detalle
            ).first()
            
            if not existe:
                nuevo = HistorialPreciosMateriaPrima(
                    id_materia=detalle.id_materia,
                    id_detalle_compra=detalle.id_detalle,
                    precio_por_gramo=precio_unitario if unidad_base == 'g' else 0,
                    precio_por_ml=precio_unitario if unidad_base == 'ml' else 0,
                    precio_por_pieza=precio_unitario if unidad_base == 'pza' else 0,
                    fecha_compra=detalle.compra.fecha_entrega if detalle.compra else datetime.now(),
                    cantidad_total_base=cantidad_base,
                    precio_total=detalle.subtotal
                )
                db.session.add(nuevo)
                print(f"✅ {materia.nombre}: ${precio_unitario:.4f} por {unidad_base}")
        
        db.session.commit()
        print("\n🎉 Todos los precios han sido actualizados")

# LISTAR RECETAS
@recetas_bp.route('/recetas')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def recetas():

    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Receta.query

    # BUSCAR
    if buscar and buscar.strip() != "":
        query = query.filter(
            Receta.nombre.ilike(f"%{buscar}%")
        )

    # FILTRAR POR ESTATUS
    if estatus:
        query = query.filter(Receta.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(Receta.nombre.asc())

    elif orden == "za":
        query = query.order_by(Receta.nombre.desc())

    recetas = query.all()

    return render_template(
        "modulo-recetas/modulo-recetas.html",
        recetas=recetas
    )


# AGREGAR RECETA
@recetas_bp.route('/agregarReceta', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def agregarReceta():

    form = forms.RecetaForm()
    productos = Producto.query.all()
    materias = MateriaPrima.query.all()

    form.id_producto.choices = [(p.id_producto, p.nombre) for p in productos]

    if form.validate_on_submit():

        receta_existente = Receta.query.filter_by(
            id_producto=form.id_producto.data
        ).first()

        if receta_existente:
            flash("Este producto ya tiene una receta.", "warning")
            return redirect(url_for('recetas.agregarReceta'))

        nueva_receta = Receta(
            id_producto=form.id_producto.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            rendimiento_piezas=form.rendimiento_piezas.data,
            estatus=form.estatus.data
        )

        db.session.add(nueva_receta)
        db.session.flush()

        # NUEVA FORMA
        materias_ids = request.form.getlist('materia[]')

        for id_materia in materias_ids:
            cantidad = request.form.get(f'cantidad_{id_materia}')
            tipo = request.form.get(f'tipo_{id_materia}')

            if cantidad:
                try:
                    cant = float(cantidad)
                    if cant > 0:
                        detalle = DetalleReceta(
                            id_receta=nueva_receta.id_receta,
                            id_materia=id_materia,
                            cantidad=cant,
                            tipo=tipo
                        )
                        db.session.add(detalle)
                except:
                    continue

        db.session.flush()

        # COSTO
        costo = calcular_costo_receta(nueva_receta)
        producto = Producto.query.get(nueva_receta.id_producto)
        producto.costo_unitario_estimado = round(costo, 2)

        db.session.commit()

        flash("Receta agregada correctamente", "success")
        return redirect(url_for('recetas.recetas'))

    return render_template(
        'modulo-recetas/agregarReceta.html',
        form=form,
        materias=materias
    )
    
def calcular_costo_receta(nueva_receta):
    """
    Calcula el costo total de la receta sumando el costo de cada ingrediente.
    """
    total_costo = 0.0
    # Asumiendo que nueva_receta tiene una relación o lista de detalles
    if hasattr(nueva_receta, 'detalles'):
        for detalle in nueva_receta.detalles:
            # Aquí multiplicas cantidad por el costo unitario de la materia prima
            # Esto es un ejemplo, ajústalo a tus nombres de campos
            costo_materia = obtener_ultimo_costo_materia(detalle.id_materia)
            total_costo += (detalle.cantidad * costo_materia)
    return total_costo
    
@recetas_bp.route('/detalleReceta/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def detalleReceta(id):
    from models import DetalleCompra, Compra
    
    receta = Receta.query.get_or_404(id)
    rendimiento = receta.rendimiento_piezas or 20

    ingredientes = []
    total_costo = 0

    for detalle in receta.ingredientes:
        materia = detalle.materia
        tipo = (detalle.tipo or '').lower().strip()
        cantidad = float(detalle.cantidad)
        
        # Obtener el último precio de compra
        ultima_compra = db.session.query(DetalleCompra.precio_unitario_compra)\
            .join(Compra)\
            .filter(DetalleCompra.id_materia == materia.id_materia)\
            .filter(Compra.estado == 'recibida')\
            .order_by(Compra.fecha_entrega.desc())\
            .first()
        
        costo_unitario = float(ultima_compra[0]) if ultima_compra and ultima_compra[0] else 0
        
        # Normalizar tipo
        if tipo in ['gr', 'gramos']:
            tipo = 'g'
        elif tipo in ['pieza', 'pza']:
            tipo = 'pz'
        
        # Convertir cantidad a unidad base y determinar unidad de visualización
        if tipo in ['g', 'gramo']:
            cantidad_base = cantidad
            unidad = 'g'
            unidad_visual = 'g'
        elif tipo in ['kg', 'kilogramo']:
            cantidad_base = cantidad * 1000
            unidad = 'g'
            unidad_visual = 'kg'
        elif tipo in ['ml', 'mililitro']:
            cantidad_base = cantidad
            unidad = 'ml'
            unidad_visual = 'ml'
        elif tipo in ['l', 'litro']:
            cantidad_base = cantidad * 1000
            unidad = 'ml'
            unidad_visual = 'L'
        elif tipo in ['pz', 'pieza']:
            cantidad_base = cantidad
            unidad = 'pz'
            unidad_visual = 'pz'
        else:
            cantidad_base = cantidad
            unidad = materia.unidad_base or 'unidad'
            unidad_visual = unidad
        
        # Calcular subtotal usando la cantidad en unidad base
        subtotal = cantidad_base * costo_unitario
        total_costo += subtotal
        
        # Determinar costo unitario por unidad base
        costo_por_unidad_base = costo_unitario
        
        ingredientes.append({
            "nombre": materia.nombre,
            "cantidad": round(cantidad, 2),
            "unidad": unidad_visual,
            "costo_unitario": round(costo_por_unidad_base, 6),
            "subtotal": round(subtotal, 2)
        })

    costo_por_pieza = total_costo / rendimiento if rendimiento > 0 else 0

    return render_template(
        'modulo-recetas/detalleReceta.html',
        receta=receta,
        ingredientes=ingredientes,
        total_costo=round(total_costo, 2),
        costo_por_pieza=round(costo_por_pieza, 2),
        rendimiento=rendimiento
    )

# EDITAR RECETA
@recetas_bp.route('/modificarReceta/<int:id>', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def modificarReceta(id):
    receta = Receta.query.get_or_404(id)
    form = forms.RecetaForm(obj=receta)
    
    # Cargar materias primas activas
    materias = MateriaPrima.query.filter_by(estatus='activo').all()
    form.id_producto.choices = [(0, 'Seleccione un producto')] + [(p.id_producto, p.nombre) for p in Producto.query.filter_by(estatus='activo').all()]
    
    # Convertir ingredientes actuales a diccionario
    ingredientes_actuales = {}
    for detalle in receta.ingredientes:
        ingredientes_actuales[detalle.id_materia] = {
            'id_materia': detalle.id_materia,
            'cantidad': detalle.cantidad,
            'tipo': detalle.tipo
        }
    
    if form.validate_on_submit():
        try:
            print("🔧 Iniciando actualización de receta...")
            
            # Actualizar datos básicos de la receta
            receta.nombre = form.nombre.data
            receta.id_producto = form.id_producto.data if form.id_producto.data != 0 else None
            receta.descripcion = form.descripcion.data
            receta.rendimiento_piezas = form.rendimiento_piezas.data
            receta.estatus = form.estatus.data
            
            # ELIMINAR ingredientes existentes
            for detalle in receta.ingredientes:
                db.session.delete(detalle)
            db.session.flush()
            print(f"✅ Eliminados {len(receta.ingredientes)} ingredientes antiguos")
            
            # OBTENER lista de materias seleccionadas
            materias_seleccionadas = request.form.getlist('materia_seleccionada[]')
            print(f"📋 Materias seleccionadas: {materias_seleccionadas}")
            
            # AGREGAR nuevos ingredientes
            ingredientes_agregados = 0
            for id_materia_str in materias_seleccionadas:
                id_materia = int(id_materia_str)
                cantidad = request.form.get(f'cantidad_{id_materia}', '')
                tipo = request.form.get(f'tipo_{id_materia}', 'g')
                
                print(f"  - Procesando materia {id_materia}: cantidad='{cantidad}', tipo='{tipo}'")
                
                if cantidad and cantidad.strip():
                    try:
                        cantidad_float = float(cantidad)
                        if cantidad_float > 0:
                            nuevo_detalle = DetalleReceta(
                                id_receta=receta.id_receta,
                                id_materia=id_materia,
                                cantidad=cantidad_float,
                                tipo=tipo
                            )
                            db.session.add(nuevo_detalle)
                            ingredientes_agregados += 1
                            print(f"    ✅ Agregado: cantidad={cantidad_float}, tipo={tipo}")
                    except ValueError as ve:
                        print(f"    ❌ Error convirtiendo cantidad: {ve}")
                        continue
            
            print(f"✅ Agregados {ingredientes_agregados} nuevos ingredientes")
            
            db.session.commit()
            print("💾 Cambios guardados en la base de datos")
            
            # Recalcular costo del producto
            if receta.id_producto:
                from blueprints.productos.routesProductos import calcular_valores_producto
                calcular_valores_producto(receta.id_producto)
            
            flash('Receta actualizada correctamente', 'success')
            return redirect(url_for('recetas.recetas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()
    
    return render_template(
        'modulo-recetas/modificarReceta.html',
        form=form,
        receta=receta,
        materias=materias,
        ingredientes_actuales=ingredientes_actuales
    )


# DESACTIVAR RECETA
@recetas_bp.route('/eliminarReceta/<int:id>', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def eliminarReceta(id):

    receta = Receta.query.get_or_404(id)

    if request.method == 'POST':

        if receta.estatus == "inactivo":
            flash("Esta receta ya está desactivada.", "warning")
            return redirect(url_for('recetas.recetas'))

        receta.estatus = "inactivo"

        db.session.commit()

        flash("Receta desactivada correctamente.", "success")

        return redirect(url_for('recetas.recetas'))

    return render_template(
        'modulo-recetas/eliminarReceta.html',
        receta=receta
    )
@recetas_bp.route('/escandallo/<int:id_producto>', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@cocina_or_admin_required
def escandallo_costos(id_producto):
    from models import HistorialPreciosMateriaPrima, DetalleCompra, Compra
    from utils.calculos import obtener_ultimo_costo_materia, obtener_detalle_ultima_compra
    from datetime import datetime
    
    producto = Producto.query.get_or_404(id_producto)
    
    if not producto.receta:
        flash('Este producto no tiene una receta asociada', 'warning')
        return redirect(url_for('recetas.recetas'))
    
    receta = producto.receta
    rendimiento = receta.rendimiento_piezas or 1
    
    ingredientes = []
    total_costo_receta = 0
    total_sin_iva = 0
    costo_total_con_iva = 0
    
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
            factor_conversion = 1
        elif tipo in ['kg', 'kilogramo', 'kilogramos']:
            cantidad_base = cantidad * 1000
            unidad_visual = 'kg'
            factor_conversion = 1000
        elif tipo in ['ml', 'mililitro', 'mililitros']:
            cantidad_base = cantidad
            unidad_visual = 'ml'
            factor_conversion = 1
        elif tipo in ['l', 'litro', 'litros']:
            cantidad_base = cantidad * 1000
            unidad_visual = 'L'
            factor_conversion = 1000
        elif tipo in ['pz', 'pieza', 'piezas']:
            cantidad_base = cantidad
            unidad_visual = 'pz'
            factor_conversion = 1
        else:
            cantidad_base = cantidad
            unidad_visual = tipo
            factor_conversion = 1
        
        # Calcular subtotal
        subtotal = cantidad_base * costo_unitario
        total_costo_receta += subtotal
        
        # Calcular IVA (16% por defecto)
        iva = subtotal * 0.16
        subtotal_con_iva = subtotal + iva
        total_sin_iva += subtotal
        costo_total_con_iva += subtotal_con_iva
        
        # Formatear costo unitario para mostrar
        if costo_unitario == 0:
            costo_mostrar = 0
            warning_precio = "⚠️ Sin precio registrado"
        elif costo_unitario < 0.01:
            costo_mostrar = costo_unitario
            warning_precio = None
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
    
    # Obtener valores POST o usar defaults
    if request.method == 'POST':
        mano_obra = float(request.form.get('mano_obra', 0))
        gastos = float(request.form.get('gastos', 0))
        rendimiento = int(request.form.get('rendimiento', rendimiento))
        margen_ganancia = float(request.form.get('margen_ganancia', 60))
        iva_porcentaje = float(request.form.get('iva_porcentaje', 16))
    else:
        mano_obra = 80.00
        gastos = 50.00
        margen_ganancia = 60
        iva_porcentaje = 16
    
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
    
    # Obtener resumen del último mes (para contexto)
    from datetime import timedelta
    fecha_hace_mes = datetime.now() - timedelta(days=30)
    
    # Total compras del último mes
    total_compras_mes = db.session.query(db.func.sum(Compra.total))\
        .filter(Compra.estado == 'recibida')\
        .filter(Compra.fecha_entrega >= fecha_hace_mes)\
        .scalar() or 0
    
    # Total movimientos de inventario del último mes
    from models import MovimientoInventario
    total_movimientos_mes = db.session.query(db.func.sum(MovimientoInventario.cantidad))\
        .filter(MovimientoInventario.tipo == 'entrada')\
        .filter(MovimientoInventario.fecha >= fecha_hace_mes)\
        .scalar() or 0
    
    return render_template(
        'modulo-recetas/escandallo_costos.html',
        producto=producto,
        receta=receta,
        rendimiento=rendimiento,
        ingredientes=ingredientes,
        total_costo_receta=round(total_costo_receta, 2),
        total_sin_iva=round(total_sin_iva, 2),
        costo_total_con_iva=round(costo_total_con_iva, 2),
        mano_obra=round(mano_obra, 2),
        gastos=round(gastos, 2),
        costo_lote_total=round(costo_lote_total, 2),
        costo_por_pieza=round(costo_por_pieza, 2),
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