"""
Script para actualizar el historial de precios de compras existentes
Ejecutar una sola vez para migrar datos antiguos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Compra, DetalleCompra
from utils.costos_materia_prima import guardar_historial_precio

def actualizar_todas_las_compras():
    with app.app_context():
        compras = Compra.query.filter_by(estado='recibida').all()
        
        print(f" Procesando {len(compras)} compras...")
        
        total_detalles = 0
        exitos = 0
        errores = 0
        
        for compra in compras:
            detalles = DetalleCompra.query.filter_by(id_compra=compra.id_compra).all()
            total_detalles += len(detalles)
            
            for detalle in detalles:
                try:
                    historial = guardar_historial_precio(detalle)
                    if historial:
                        exitos += 1
                        print(f" Materia {detalle.id_materia} - Compra #{compra.id_compra}")
                    else:
                        errores += 1
                        print(f" Error en detalle {detalle.id_detalle}")
                except Exception as e:
                    errores += 1
                    print(f" Error: {e}")
        
        print(f"\n🎉 Procesamiento completado!")
        print(f"   Compras: {len(compras)}")
        print(f"   Detalles: {total_detalles}")
        print(f"   Exitosos: {exitos}")
        print(f"   Errores: {errores}")

if __name__ == '__main__':
    actualizar_todas_las_compras()