from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
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
    stock_actual = db.Column(db.Integer)
    stock_minimo = db.Column(db.Integer)
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
    
class Categoria(db.Model):

    __tablename__ = 'categorias'

    id_categoria = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(80), nullable=False, unique=True)

    descripcion = db.Column(db.String(200))

    imagen = db.Column(db.LargeBinary)  

    estatus = db.Column(
        db.Enum('activo', 'inactivo'),
        default='activo'
    )

    productos = db.relationship(
        'Producto',
        backref='categoria',
        lazy=True
    )
    
    

class Producto(db.Model):

    __tablename__ = 'productos'

    id_producto = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(100), nullable=False)

    descripcion = db.Column(db.Text)

    id_categoria = db.Column(
        db.Integer,
        db.ForeignKey('categorias.id_categoria'),
        nullable=False
    )

    precio_venta = db.Column(db.Numeric(10,2), nullable=False)

    costo_unitario_estimado = db.Column(
        db.Numeric(10,2),
        default=0.00
    )

    imagen_url = db.Column(db.LargeBinary)

    dias_caducidad = db.Column(db.Integer, default=3)

    estatus = db.Column(
        db.Enum('activo','inactivo'),
        default='activo'
    )


    
class Receta(db.Model):

    __tablename__ = 'recetas'

    id_receta = db.Column(
        db.Integer,
        primary_key=True
    )

    id_producto = db.Column(
        db.Integer,
        db.ForeignKey('productos.id_producto'),
        nullable=False
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.Text
    )

    rendimiento_piezas = db.Column(
        db.Integer,
        default=20
    )

    estatus = db.Column(
        db.Enum('activo', 'inactivo'),
        default='activo'
    )

    # relación con producto
    producto = db.relationship(
        'Producto',
        backref='recetas',
        lazy=True
    )

    def __repr__(self):
        return f'<Receta {self.nombre}>'
    
class DetalleReceta(db.Model):

    __tablename__ = 'detalle_receta'

    id_detalle = db.Column(
        db.Integer,
        primary_key=True
    )

    id_receta = db.Column(
        db.Integer,
        db.ForeignKey('recetas.id_receta'),
        nullable=False
    )

    id_materia = db.Column(
        db.Integer,
        db.ForeignKey('materias_primas.id_materia'),
        nullable=False
    )

    cantidad_por_pieza = db.Column(
        db.Numeric(12,4),
        nullable=False
    )

    # relaciones
    receta = db.relationship(
        'Receta',
        backref='ingredientes',
        lazy=True
    )

    materia = db.relationship(
        'MateriaPrima',
        backref='detalle_recetas',
        lazy=True
    )

    def __repr__(self):
        return f'<DetalleReceta {self.id_detalle}>'
    
    
class Orden(db.Model):

    __tablename__ = "ordenes"

    id_orden = db.Column(db.Integer, primary_key=True)

    # cliente (temporal)
    cliente_nombre = db.Column(db.String(100), nullable=False)
    cliente_telefono = db.Column(db.String(20))

    # fecha
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    

    # cajera (temporal)
    cajera = db.Column(db.String(100))

    # total
    total = db.Column(db.Numeric(10,2), default=0.00)

    estatus = db.Column(
        db.Enum('pendiente', 'completada', 'cancelada'),
        default='pendiente'
    )

    # relación
    detalles = db.relationship(
        'DetalleOrden',
        backref='orden',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<Orden {self.id_orden}>'
    
class DetalleOrden(db.Model):

    __tablename__ = "detalle_orden"

    id_detalle_orden = db.Column(db.Integer, primary_key=True)

    id_orden = db.Column(
        db.Integer,
        db.ForeignKey('ordenes.id_orden'),
        nullable=False
    )

    id_producto = db.Column(
        db.Integer,
        db.ForeignKey('productos.id_producto'),
        nullable=False
    )

    cantidad = db.Column(db.Integer, nullable=False)

    precio_unitario = db.Column(
        db.Numeric(10,2),
        nullable=False
    )

    subtotal = db.Column(
        db.Numeric(10,2),
        nullable=False
    )

    # relación
    producto = db.relationship('Producto')

    def __repr__(self):
        return f'<DetalleOrden {self.id_detalle_orden}>'
    
class Compra(db.Model):

    __tablename__ = "compras"

    id_compra = db.Column(db.Integer, primary_key=True)

    id_proveedor = db.Column(
        db.Integer,
        db.ForeignKey('proveedores.id_proveedor'),
        nullable=False
    )

    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    total = db.Column(db.Numeric(10,2), default=0.00)

    proveedor = db.relationship("Proveedor")


class DetalleCompra(db.Model):

    __tablename__ = "detalle_compra"

    id_detalle_compra = db.Column(db.Integer, primary_key=True)

    id_compra = db.Column(
        db.Integer,
        db.ForeignKey('compras.id_compra'),
        nullable=False
    )

    id_materia = db.Column(
        db.Integer,
        db.ForeignKey('materias_primas.id_materia'),
        nullable=False
    )

    cantidad = db.Column(db.Integer, nullable=False)

    precio_unitario = db.Column(db.Numeric(10,2))

    subtotal = db.Column(db.Numeric(10,2))

    materia = db.relationship("MateriaPrima")
    
class Sucursal(db.Model):
    __tablename__ = 'sucursales'

    id_sucursal = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    ciudad = db.Column(db.String(100))
    estatus = db.Column(db.Enum('activo','inactivo'), default='activo')

class Rol(db.Model):
    __tablename__ = 'roles'
    id_rol      = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(150))
    usuarios    = db.relationship('Usuario',  backref='rol', lazy=True)
    empleados   = db.relationship('Empleado', backref='rol', lazy=True)
 
 
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id_usuario     = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(100), unique=True, nullable=False)
    password       = db.Column(db.String(255), nullable=False)
    id_rol         = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)
    activo         = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
 
    def get_id(self):
        return str(self.id_usuario)
 
 
class Empleado(db.Model):
    __tablename__ = 'empleados'
    id_empleado        = db.Column(db.Integer, primary_key=True)
    nombre             = db.Column(db.String(100), nullable=False)
    telefono           = db.Column(db.String(20))
    email              = db.Column(db.String(100), unique=True)
    direccion          = db.Column(db.String(200))
    puesto             = db.Column(db.String(80))
    salario            = db.Column(db.Numeric(10,2))
    fecha_nacimiento   = db.Column(db.Date)
    fecha_contratacion = db.Column(db.Date)
    id_rol             = db.Column(db.Integer, db.ForeignKey('roles.id_rol'))
    estatus            = db.Column(db.Enum('activo','inactivo'), default='activo')
 
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id_cliente     = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(100), nullable=False)
    telefono       = db.Column(db.String(20))
    email          = db.Column(db.String(100), unique=True)
    direccion      = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    estatus        = db.Column(db.Enum('activo','inactivo'), default='activo')


class NominaIndividual(db.Model):
    """Un registro de pago por empleado por periodo."""
    __tablename__ = 'nominas_individuales'

    id_nomina_ind      = db.Column(db.Integer, primary_key=True)
    id_empleado        = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado'), nullable=False)
    id_nomina_grupal   = db.Column(db.Integer, db.ForeignKey('nominas_grupales.id_nomina_grupal'), nullable=True)  # null = creada suelta

    periodo            = db.Column(db.Enum('quincenal', 'mensual'), nullable=False)
    fecha_inicio       = db.Column(db.Date, nullable=False)
    fecha_fin          = db.Column(db.Date, nullable=False)
    fecha_pago         = db.Column(db.Date, nullable=True)          # fecha real en que se pagó

    puesto             = db.Column(db.String(80))                   # snapshot del puesto al momento
    salario_base       = db.Column(db.Numeric(10, 2), nullable=False)
    monto_pagado       = db.Column(db.Numeric(10, 2), nullable=False)

    estatus            = db.Column(
                            db.Enum('pendiente', 'pagado', 'incidencia'),
                            default='pendiente'
                         )
    notas              = db.Column(db.Text)                         # para describir incidencias o correcciones
    fecha_registro     = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    empleado           = db.relationship('Empleado')

    def __repr__(self):
        return f'<NominaIndividual emp={self.id_empleado} periodo={self.periodo}>'


class NominaGrupal(db.Model):
    """Agrupa varias NominaIndividual generadas juntas."""
    __tablename__ = 'nominas_grupales'

    id_nomina_grupal   = db.Column(db.Integer, primary_key=True)
    nombre             = db.Column(db.String(120), nullable=False)   # ej: "Quincena 1 Marzo - Producción"
    periodo            = db.Column(db.Enum('quincenal', 'mensual'), nullable=False)
    fecha_inicio       = db.Column(db.Date, nullable=False)
    fecha_fin          = db.Column(db.Date, nullable=False)
    total_pagado       = db.Column(db.Numeric(10, 2), default=0)
    fecha_registro     = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    individuales       = db.relationship(
                            'NominaIndividual',
                            backref='grupal',
                            lazy=True,
                            foreign_keys='NominaIndividual.id_nomina_grupal'
                         )

    @property
    def estatus(self):
        """Calculado: pagada si todos pagados, incidencia si alguno tiene incidencia, sino pendiente."""
        estados = [n.estatus for n in self.individuales]
        if not estados:
            return 'pendiente'
        if 'incidencia' in estados:
            return 'incidencia'
        if all(e == 'pagado' for e in estados):
            return 'pagada'
        return 'pendiente'

    def __repr__(self):
        return f'<NominaGrupal {self.nombre}>'

class GastoExtra(db.Model):
    """Gastos que no vienen de compras ni nómina: renta, servicios, mantenimiento, etc."""
    __tablename__ = 'gastos_extra'
 
    id_gasto       = db.Column(db.Integer, primary_key=True)
    concepto       = db.Column(db.String(150), nullable=False)
    monto          = db.Column(db.Numeric(10, 2), nullable=False)
    fecha          = db.Column(db.Date, nullable=False)
    categoria      = db.Column(db.String(80))   # renta, servicios, mantenimiento, otros
    notas          = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
 
    def __repr__(self):
        return f'<GastoExtra {self.concepto} ${self.monto}>'