from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()


class Proveedor(db.Model):

    __tablename__ = 'proveedores'

    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    direccion = db.Column(db.String(200))
    contacto = db.Column(db.String(100))
    notas = db.Column(db.Text)
    estatus = db.Column(db.Enum('activo','inactivo'), default='activo')
    
class MateriaPrima(db.Model):

    __tablename__ = 'materias_primas'

    id_materia = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    unidad_medida = db.Column(db.String(30), nullable=False)
    stock_actual = db.Column(db.Numeric(12,3), default=0.000)
    stock_minimo = db.Column(db.Numeric(12,3), default=0.000)
    precio_unitario = db.Column(db.Numeric(10,2), default=0.00)

    id_proveedor = db.Column(
        db.Integer,
        db.ForeignKey('proveedores.id_proveedor')
    )

    fecha_ultima_compra = db.Column(db.Date)

    estatus = db.Column(
        db.Enum('activo','inactivo'),
        default='activo'
    )

    proveedor = db.relationship('Proveedor')