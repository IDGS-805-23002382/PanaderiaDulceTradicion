# utils/precios.py
from models import db, HistorialPreciosMateriaPrima, MateriaPrima
from datetime import datetime

def calcular_y_guardar_precio_materia(id_detalle_compra, detalle_compra_obj=None):
    """
    Calcula el precio por gramo/ml/pieza de una materia prima
    basado en el detalle de compra y lo guarda en el historial
    """
    from models import DetalleCompra, MateriaPrima
    
    if detalle_compra_obj is None:
        detalle = DetalleCompra.query.get(id_detalle_compra)
    else:
        detalle = detalle_compra_obj
    
    if not detalle:
        return None
    
    materia = MateriaPrima.query.get(detalle.id_materia)
    if not materia:
        return None
    
    unidad_base = materia.unidad_base  # 'g', 'ml', 'pza'
    
    # Calcular cantidad total en unidad base
    cantidad_total_base = 0
    precio_por_gramo = 0
    precio_por_ml = 0
    precio_por_pieza = 0
    
    if detalle.tipo_compra == 'caja':
        # Ejemplo: 2 cajas × 18 piezas × 400g = 14400g
        cantidad_cajas = float(detalle.cantidad_cajas) if detalle.cantidad_cajas else 0
        piezas_por_caja = float(detalle.piezas_por_caja) if detalle.piezas_por_caja else 1
        contenido_pieza = float(detalle.contenido_pieza_caja) if detalle.contenido_pieza_caja else 0
        unidad_contenido = (detalle.unidad_contenido_caja or 'g').lower()
        
        # Convertir a gramos o ml según la unidad
        if unidad_contenido in ['g', 'kg']:
            contenido_base = contenido_pieza * 1000 if unidad_contenido == 'kg' else contenido_pieza
            cantidad_total_base = cantidad_cajas * piezas_por_caja * contenido_base
        elif unidad_contenido in ['ml', 'l']:
            contenido_base = contenido_pieza * 1000 if unidad_contenido == 'l' else contenido_pieza
            cantidad_total_base = cantidad_cajas * piezas_por_caja * contenido_base
        
        precio_por_pieza = detalle.subtotal / (cantidad_cajas * piezas_por_caja) if (cantidad_cajas * piezas_por_caja) > 0 else 0
        
    elif detalle.tipo_compra == 'piezas':
        # Ejemplo: 24 bolsas de 900g = 21600g
        cantidad_piezas = float(detalle.cantidad_piezas) if detalle.cantidad_piezas else 0
        contenido_pieza = float(detalle.contenido_pieza) if detalle.contenido_pieza else 0
        unidad_contenido = (detalle.unidad_contenido_pieza or 'g').lower()
        
        if unidad_contenido in ['g', 'kg']:
            contenido_base = contenido_pieza * 1000 if unidad_contenido == 'kg' else contenido_pieza
            cantidad_total_base = cantidad_piezas * contenido_base
        elif unidad_contenido in ['ml', 'l']:
            contenido_base = contenido_pieza * 1000 if unidad_contenido == 'l' else contenido_pieza
            cantidad_total_base = cantidad_piezas * contenido_base
        
        precio_por_pieza = detalle.subtotal / cantidad_piezas if cantidad_piezas > 0 else 0
        
    elif detalle.tipo_compra == 'granel':
        # Ejemplo: 5 kg = 5000g, 10 L = 10000ml
        cantidad = float(detalle.cantidad_granel) if detalle.cantidad_granel else 0
        unidad = (detalle.unidad_granel or 'g').lower()
        
        if unidad in ['g', 'kg']:
            cantidad_total_base = cantidad * 1000 if unidad == 'kg' else cantidad
        elif unidad in ['ml', 'l']:
            cantidad_total_base = cantidad * 1000 if unidad == 'l' else cantidad
        
        precio_por_pieza = detalle.subtotal / 1  # Para granel, consideramos 1 lote
    
    # Calcular precios por unidad base
    if cantidad_total_base > 0 and detalle.subtotal:
        if unidad_base == 'g':
            precio_por_gramo = detalle.subtotal / cantidad_total_base
        elif unidad_base == 'ml':
            precio_por_ml = detalle.subtotal / cantidad_total_base
    
    # Guardar en el historial
    nuevo_historial = HistorialPreciosMateriaPrima(
        id_materia=detalle.id_materia,
        id_detalle_compra=detalle.id_detalle,
        precio_por_gramo=round(precio_por_gramo, 6),
        precio_por_ml=round(precio_por_ml, 6),
        precio_por_pieza=round(precio_por_pieza, 4),
        fecha_compra=detalle.compra.fecha_entrega if detalle.compra else datetime.now(),
        cantidad_total_base=round(cantidad_total_base, 2),
        precio_total=detalle.subtotal
    )
    
    db.session.add(nuevo_historial)
    db.session.commit()
    
    return nuevo_historial


def obtener_precio_actual_materia(id_materia):
    """
    Obtiene el precio más reciente (última compra) de una materia prima
    """
    ultimo_precio = HistorialPreciosMateriaPrima.query.filter_by(
        id_materia=id_materia
    ).order_by(HistorialPreciosMateriaPrima.fecha_compra.desc()).first()
    
    if not ultimo_precio:
        return {'precio_por_gramo': 0, 'precio_por_ml': 0, 'precio_por_pieza': 0}
    
    return {
        'precio_por_gramo': float(ultimo_precio.precio_por_gramo),
        'precio_por_ml': float(ultimo_precio.precio_por_ml),
        'precio_por_pieza': float(ultimo_precio.precio_por_pieza),
        'fecha_compra': ultimo_precio.fecha_compra,
        'cantidad_total_base': float(ultimo_precio.cantidad_total_base),
        'precio_total': float(ultimo_precio.precio_total)
    }