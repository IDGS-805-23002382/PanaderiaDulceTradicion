# utils/calculos.py
from models import db, DetalleCompra, Compra, MateriaPrima, HistorialPreciosMateriaPrima
from flask import current_app

def obtener_costo_unitario_base(id_materia):
    """
    Calcula el costo por unidad base (gramo o mililitro) de una materia prima
    basado en el último precio de compra y su presentación.
    
    Ejemplo:
    - 1 caja de 18 piezas de 400g c/u = 7200g total
    - Precio caja: $1800
    - Costo por gramo = 1800 / 7200 = $0.25 por gramo
    """
    from models import DetalleCompra, Compra
    
    # Obtener la última compra recibida de esta materia prima
    ultimo_detalle = db.session.query(DetalleCompra)\
        .join(Compra)\
        .filter(DetalleCompra.id_materia == id_materia)\
        .filter(Compra.estado == 'recibida')\
        .order_by(Compra.fecha_entrega.desc())\
        .first()
    
    if not ultimo_detalle:
        return 0.0
    
    materia = MateriaPrima.query.get(id_materia)
    unidad_base = materia.unidad_base if materia else 'g'  # g, ml, pza
    
    # Calcular cantidad total en unidad base
    cantidad_total_base = calcular_cantidad_en_unidad_base(ultimo_detalle, unidad_base)
    
    if cantidad_total_base == 0:
        return 0.0
    
    # Obtener precio total pagado
    precio_total = float(ultimo_detalle.subtotal) if ultimo_detalle.subtotal else 0
    
    # Calcular costo por unidad base
    costo_por_unidad_base = precio_total / cantidad_total_base
    
    return round(costo_por_unidad_base, 6)


def calcular_cantidad_en_unidad_base(detalle, unidad_base):
    """
    Calcula la cantidad total en unidad base (gramos o mililitros)
    según el tipo de compra (granel, piezas, caja)
    """
    cantidad_total = 0
    
    if detalle.tipo_compra == 'granel':
        # Compra a granel: ej: 5 kg, 10 L
        cantidad = float(detalle.cantidad_granel) if detalle.cantidad_granel else 0
        unidad = (detalle.unidad_granel or '').lower()
        
        if unidad_base == 'g':
            if unidad in ['kg', 'kilogramo']:
                cantidad_total = cantidad * 1000
            elif unidad in ['g', 'gramo']:
                cantidad_total = cantidad
        elif unidad_base == 'ml':
            if unidad in ['l', 'litro']:
                cantidad_total = cantidad * 1000
            elif unidad in ['ml', 'mililitro']:
                cantidad_total = cantidad
        else:
            cantidad_total = cantidad
            
    elif detalle.tipo_compra == 'piezas':
        # Compra por piezas/empaque: ej: 24 bolsas de 900g
        cantidad_piezas = float(detalle.cantidad_piezas) if detalle.cantidad_piezas else 0
        contenido_pieza = float(detalle.contenido_pieza) if detalle.contenido_pieza else 0
        
        if unidad_base in ['g', 'ml']:
            cantidad_total = cantidad_piezas * contenido_pieza
        else:
            cantidad_total = cantidad_piezas
            
    elif detalle.tipo_compra == 'caja':
        # Compra por cajas: ej: 2 cajas de 18 piezas de 400g
        cantidad_cajas = float(detalle.cantidad_cajas) if detalle.cantidad_cajas else 0
        piezas_por_caja = float(detalle.piezas_por_caja) if detalle.piezas_por_caja else 1
        contenido_pieza = float(detalle.contenido_pieza_caja) if detalle.contenido_pieza_caja else 0
        
        if unidad_base in ['g', 'ml']:
            cantidad_total = cantidad_cajas * piezas_por_caja * contenido_pieza
        else:
            cantidad_total = cantidad_cajas * piezas_por_caja
    
    return cantidad_total


def obtener_costo_por_pieza(id_materia):
    """
    Obtiene el costo por pieza/unidad de una materia prima
    """
    from models import DetalleCompra, Compra
    
    ultimo_detalle = db.session.query(DetalleCompra)\
        .join(Compra)\
        .filter(DetalleCompra.id_materia == id_materia)\
        .filter(Compra.estado == 'recibida')\
        .order_by(Compra.fecha_entrega.desc())\
        .first()
    
    if not ultimo_detalle:
        return 0.0
    
    # Calcular cantidad de piezas
    cantidad_piezas = 0
    
    if ultimo_detalle.tipo_compra == 'granel':
        cantidad_piezas = 1  # Por defecto
    elif ultimo_detalle.tipo_compra == 'piezas':
        cantidad_piezas = float(ultimo_detalle.cantidad_piezas) if ultimo_detalle.cantidad_piezas else 0
    elif ultimo_detalle.tipo_compra == 'caja':
        cantidad_cajas = float(ultimo_detalle.cantidad_cajas) if ultimo_detalle.cantidad_cajas else 0
        piezas_por_caja = float(ultimo_detalle.piezas_por_caja) if ultimo_detalle.piezas_por_caja else 1
        cantidad_piezas = cantidad_cajas * piezas_por_caja
    
    if cantidad_piezas == 0:
        return 0.0
    
    precio_total = float(ultimo_detalle.subtotal) if ultimo_detalle.subtotal else 0
    return precio_total / cantidad_piezas


# ============================================
# NUEVAS FUNCIONES PARA EL ESCANDALLO DE COSTOS
# ============================================

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
        print(f"Error obteniendo costo de materia {id_materia}: {e}")
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
        print(f"Error obteniendo detalle de compra: {e}")
        return None