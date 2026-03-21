# usuarios/__init__.py
from flask import Blueprint

usuarios_bp = Blueprint(
    'usuarios',
    __name__,
    template_folder='templates'
)

from . import routesUsuarios