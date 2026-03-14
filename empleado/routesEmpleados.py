from flask import render_template
from models import Empleado
from . import empleados_bp


@empleados_bp.route("/empleados")
def index():

    empleados = Empleado.query.all()

    return render_template(
        "modulo-empleado/modulo-empleado.html",
        empleados=empleados
    )