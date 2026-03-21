# clientes/__init__.py
from flask import Blueprint

clientes_bp = Blueprint(
    'clientes',
    __name__,
    template_folder='templates'
)

from . import routesClientes