
# empleado/__init__.py
from flask import Blueprint

empleados_bp=Blueprint(
    'empleados',
    __name__,
    template_folder="templates"
)
<<<<<<< HEAD

=======
from . import routesEmpleaados
>>>>>>> d9c95103a59bb805666d341ce56430d8b2ad02cd
from . import routesEmpleados
