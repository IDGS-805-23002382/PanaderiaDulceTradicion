"""
utils/costos_materia_prima.py
Utilidades para calcular y gestionar costos de materias primas
"""
from models import db, HistorialPreciosMateriaPrima, MateriaPrima, DetalleCompra, Compra
from datetime import datetime
from flask import current_app

def calcular_cantidad_en_unidad_base(detalle, unidad_base):
    """
    Calcula la cantidad total en unidad base (gramos, mililitros o piezas)
    según el tipo de compra (granel, piezas, caja)
    """
    cantidad_total = 0.0
    
    try:
        if detalle.tipo_compra == 'granel':
            cantidad = float(detalle.cantidad_granel) if detalle.cantidad_granel else 0
            unidad = (detalle.unidad_granel or '').lower()
            
            if unidad_base == 'g':
                if unidad in ['kg', 'kilogramo', 'kilogramos']:
                    cantidad_total = cantidad * 1000
                elif unidad in ['g', 'gramo', 'gramos']:
                    cantidad_total = cantidad
            elif unidad_base == 'ml':
                if unidad in ['l', 'litro', 'litros']:
                    cantidad_total = cantidad * 1000
                elif unidad in ['ml', 'mililitro', 'mililitros']:
                    cantidad_total = cantidad
            else:  # piezas
                cantidad_total = cantidad
                
        elif detalle.tipo_compra == 'piezas':
            cantidad_piezas = float(detalle.cantidad_piezas) if detalle.cantidad_piezas else 0
            contenido_pieza = float(detalle.contenido_pieza) if detalle.contenido_pieza else 0
            unidad_contenido = (detalle.unidad_contenido_pieza or 'g').lower()
            
            if unidad_base in ['g', 'ml']:
                contenido_en_base = contenido_pieza
                if unidad_base == 'g' and unidad_contenido == 'kg':
                    contenido_en_base = contenido_pieza * 1000
                elif unidad_base == 'ml' and unidad_contenido == 'l':
                    contenido_en_base = contenido_pieza * 1000
                cantidad_total = cantidad_piezas * contenido_en_base
            else:  # piezas
                cantidad_total = cantidad_piezas
                
        elif detalle.tipo_compra == 'caja':
            cantidad_cajas = float(detalle.cantidad_cajas) if detalle.cantidad_cajas else 0
            piezas_por_caja = float(detalle.piezas_por_caja) if detalle.piezas_por_caja else 1
            contenido_pieza = float(detalle.contenido_pieza_caja) if detalle.contenido_pieza_caja else 0
            unidad_contenido = (detalle.unidad_contenido_caja or 'g').lower()
            
            if unidad_base in ['g', 'ml']:
                contenido_en_base = contenido_pieza
                if unidad_base == 'g' and unidad_contenido == 'kg':
                    contenido_en_base = contenido_pieza * 1000
                elif unidad_base == 'ml' and unidad_contenido == 'l':
                    contenido_en_base = contenido_pieza * 1000
                cantidad_total = cantidad_cajas * piezas_por_caja * contenido_en_base
            else:  # piezas
                cantidad_total = cantidad_cajas * piezas_por_caja
    
    except Exception as e:
        current_app.logger.error(f"Error calculando cantidad base: {e}")
        cantidad_total = 0
    
    return cantidad_total


def calcular_precios_unitarios(detalle):
    """Calcula los precios por unidad base a partir de un detalle de compra"""
    materia = MateriaPrima.query.get(detalle.id_materia)
    if not materia:
        return {
            'precio_por_gramo': 0.0,
            'precio_por_ml': 0.0,
            'precio_por_pieza': 0.0,
            'cantidad_total_base': 0
        }
    
    unidad_base = materia.unidad_base or 'g'
    precio_total = float(detalle.subtotal) if detalle.subtotal else 0
    
    resultados = {
        'precio_por_gramo': 0.0,
        'precio_por_ml': 0.0,
        'precio_por_pieza': 0.0,
        'cantidad_total_base': 0
    }
    
    cantidad_base = calcular_cantidad_en_unidad_base(detalle, unidad_base)
    resultados['cantidad_total_base'] = cantidad_base
    
    if cantidad_base > 0 and precio_total > 0:
        precio_unitario = precio_total / cantidad_base
        
        if unidad_base == 'g':
            resultados['precio_por_gramo'] = round(precio_unitario, 6)
        elif unidad_base == 'ml':
            resultados['precio_por_ml'] = round(precio_unitario, 6)
        elif unidad_base == 'pza':
            resultados['precio_por_pieza'] = round(precio_unitario, 6)
    
    return resultados


def guardar_historial_precio(detalle):
    """Guarda o actualiza el historial de precios para una materia prima"""
    try:
        precios = calcular_precios_unitarios(detalle)
        
        compra = Compra.query.get(detalle.id_compra)
        fecha_compra = compra.fecha_entrega if compra else datetime.now()
        
        existe = HistorialPreciosMateriaPrima.query.filter_by(
            id_detalle_compra=detalle.id_detalle
        ).first()
        
        if existe:
            existe.precio_por_gramo = precios['precio_por_gramo']
            existe.precio_por_ml = precios['precio_por_ml']
            existe.precio_por_pieza = precios['precio_por_pieza']
            existe.cantidad_total_base = precios['cantidad_total_base']
            existe.precio_total = detalle.subtotal
            existe.fecha_compra = fecha_compra
            historial = existe
        else:
            historial = HistorialPreciosMateriaPrima(
                id_materia=detalle.id_materia,
                id_detalle_compra=detalle.id_detalle,
                precio_por_gramo=precios['precio_por_gramo'],
                precio_por_ml=precios['precio_por_ml'],
                precio_por_pieza=precios['precio_por_pieza'],
                cantidad_total_base=precios['cantidad_total_base'],
                precio_total=detalle.subtotal,
                fecha_compra=fecha_compra
            )
            db.session.add(historial)
        
        db.session.commit()
        
        materia = MateriaPrima.query.get(detalle.id_materia)
        unidad = materia.unidad_base if materia else 'unidad'
        precio = precios[f'precio_por_{unidad}'] if unidad in ['g', 'ml', 'pza'] else 0
        
        current_app.logger.info(
            f"✅ Historial actualizado - {materia.nombre if materia else 'N/A'}: "
            f"${precio:.4f} por {unidad}"
        )
        
        return historial
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error guardando historial de precios: {e}")
        return None