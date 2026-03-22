# app/utils/decorators.py
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user



def gerente_or_admin_required(f):
    """Gerentes y administradores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.rol.nombre not in ['Administrador', 'Gerente']:
            flash('Acceso denegado. Se requieren permisos de Gerente o Administrador.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def cocina_or_admin_required(f):
    """Encargado de cocina, Gerente y Administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.rol.nombre not in ['Administrador', 'Gerente', 'Encargado cocina']:
            flash('Acceso denegado. Solo personal de cocina puede acceder.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def vendedor_or_admin_required(f):
    """Vendedor, Gerente y Administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.rol.nombre not in ['Administrador', 'Gerente', 'Vendedor']:
            flash('Acceso denegado. Solo vendedores pueden acceder.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def marketing_or_admin_required(f):
    """Marketing, Gerente y Administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.rol.nombre not in ['Administrador', 'Gerente', 'Marketing']:
            flash('Acceso denegado. Solo personal de marketing puede acceder.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_with_message(f):
    """Login requerido con mensaje personalizado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para ver esta página', 'info')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Solo administradores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.rol.nombre != 'Administrador':
            flash('Acceso denegado. Se requieren permisos de Administrador.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def empleado_required(f):
    """Solo empleados (NO clientes)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.rol.nombre == 'Cliente':
            flash('Acceso denegado. Esta área es solo para empleados.', 'error')
            return redirect(url_for('public.catalogo'))
        return f(*args, **kwargs)
    return decorated_function