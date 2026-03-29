# blueprints/nomina/__init__.py
from flask import Blueprint

nomina_bp = Blueprint(
    'nomina',
    __name__,
    template_folder='templates'
)

from . import routesNomina