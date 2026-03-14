from flask import Blueprint

empleados_bp=Blueprint(
    'empleados',
    __name__,
    template_folder="templates"
)
from . import routesEmpleaados