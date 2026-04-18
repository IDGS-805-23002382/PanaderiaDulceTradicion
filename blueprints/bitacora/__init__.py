from flask import Blueprint

bitacora_bp=Blueprint(
    'bitacora',
    __name__,
    template_folder="templates"
)
from . import routesBitacora