from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()
# -----------------------------
# EMPLEADOS
# -----------------------------
class Empleado(db.Model):
    __tablename__ = 'empleados'

    id_empleado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    email = db.Column(db.String(120))
    rol = db.Column(db.String(50))
    sueldo = db.Column(db.Numeric(10,2))

    fecha_ingreso = db.Column(
        db.Date,
        default=datetime.date.today
    )

    estatus = db.Column(db.String(20), default="Activo")