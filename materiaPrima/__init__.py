from flask import Blueprint

materiaPrima_bp=Blueprint(
    'materiaPrima',
    __name__,
    template_folder="templates"
)
from . import routesMateriaPrima