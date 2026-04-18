from flask import request
from models import db, Bitacora
from flask_login import current_user
import json

def registrar_log(accion, tabla, registro_id=None, descripcion=None, usuario_id=None):
    try:
        # Obtener IP
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0]

        # Usuario
        if usuario_id is None:
            if current_user and current_user.is_authenticated:
                usuario_id = current_user.id_usuario
                usuario_nombre = current_user.email
            else:
                usuario_id = None
                usuario_nombre = 'Sistema'
        else:
            usuario_nombre = None

        log = Bitacora(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion=accion,
            tabla=tabla,
            registro_id=registro_id,
            descripcion=descripcion,
            ip_usuario=ip
        )

        db.session.add(log)
        db.session.commit()

    except Exception as e:
        print(f"Error al registrar log: {str(e)}")
        db.session.rollback()


def registrar_cambio(tabla, registro_id, datos_anteriores, datos_nuevos):
    descripcion = f"""
Cambio en {tabla} ID {registro_id}:
Datos anteriores: {json.dumps(datos_anteriores, default=str, ensure_ascii=False)}
Datos nuevos: {json.dumps(datos_nuevos, default=str, ensure_ascii=False)}
"""
    registrar_log('UPDATE', tabla, registro_id, descripcion.strip())


def registrar_creacion(tabla, registro_id, datos):
    descripcion = f"""
Nuevo registro en {tabla} ID {registro_id}:
Datos: {json.dumps(datos, default=str, ensure_ascii=False)}
"""
    registrar_log('CREATE', tabla, registro_id, descripcion.strip())


def registrar_eliminacion(tabla, registro_id, datos_eliminados):
    descripcion = f"""
Registro eliminado/desactivado en {tabla} ID {registro_id}:
Datos: {json.dumps(datos_eliminados, default=str, ensure_ascii=False)}
"""
    registrar_log('DELETE', tabla, registro_id, descripcion.strip())