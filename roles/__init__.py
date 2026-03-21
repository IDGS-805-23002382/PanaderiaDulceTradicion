# roles/__init__.py
from flask import Blueprint

roles_bp = Blueprint(
    'roles',
    __name__,
    template_folder='templates'
)

from . import routesRoles