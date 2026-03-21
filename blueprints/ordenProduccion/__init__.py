from flask import Blueprint

ordenProduccion_bp=Blueprint(
    'ordenProduccion',
    __name__,
    template_folder="templates"
)
from . import routesOrdenProduccion