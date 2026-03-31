# blueprints/finanzas/__init__.py
from flask import Blueprint

finanzas_bp = Blueprint(
    'finanzas',
    __name__,
    template_folder='templates'
)

from . import routesFinanzas