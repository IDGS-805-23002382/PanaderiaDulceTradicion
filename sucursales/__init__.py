from flask import Blueprint

sucursales_bp = Blueprint(
    'sucursales',
    __name__
)

from . import routesSucursales