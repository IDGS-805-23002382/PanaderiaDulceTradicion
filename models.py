from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import datetime

db = SQLAlchemy()


class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    direccion = db.Column(db.String(200))
    contacto = db.Column(db.String(100))
    notas = db.Column(db.Text)
    estatus = db.Column(
        db.Enum('activo','inactivo'),
        default='activo')
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
class MateriaPrima(db.Model):
    __tablename__ = 'materias_primas'

    id_materia = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    unidad_medida = db.Column(db.String(30), nullable=False)
    unidad_contenido = db.Column(db.String(10))

    tipo_empaque = db.Column(db.String(20), default='unidad')
    piezas_por_caja = db.Column(db.Integer, nullable=True)
    peso_por_pieza = db.Column(db.Float, nullable=True)

    # ELIMINA O COMENTA esta línea si existe:
    # precio_unitario = db.Column(db.Numeric(10,2), default=0.00)

    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'))
    estatus = db.Column(db.Enum('activo','inactivo'), default='activo')

    proveedor = db.relationship('Proveedor')

    def get_ultimo_precio(self):
        """Obtiene el último precio de compra de esta materia prima"""
        from models import DetalleCompra
        
        # CORREGIDO: usar precio_unitario_compra en lugar de precio_unitario
        ultima_compra = DetalleCompra.query.filter_by(id_materia=self.id_materia)\
            .order_by(DetalleCompra.id_detalle.desc()).first()
        
        if ultima_compra and ultima_compra.precio_unitario_compra:
            return float(ultima_compra.precio_unitario_compra)
        return 0.0

    @property
    def precio_por_pieza(self):
        """Calcula el precio por pieza según piezas_por_caja usando el último precio de compra"""
        try:
            ultimo_precio = self.get_ultimo_precio()
            if self.piezas_por_caja and self.piezas_por_caja > 0:
                return ultimo_precio / self.piezas_por_caja
            return ultimo_precio
        except:
            return 0

    @property
    def precio_por_gramo_ml(self):
        """Calcula el precio por gramo o ml según peso_por_pieza"""
        try:
            if not self.peso_por_pieza or not self.unidad_contenido:
                return 0

            precio_pieza = self.precio_por_pieza
            unidad = self.unidad_contenido.lower().strip()

            if unidad in ['gr', 'gramos']:
                return precio_pieza / self.peso_por_pieza
            elif unidad in ['kg']:
                return precio_pieza / (self.peso_por_pieza * 1000)
            elif unidad in ['ml']:
                return precio_pieza / self.peso_por_pieza
            elif unidad in ['l', 'litros']:
                return precio_pieza / (self.peso_por_pieza * 1000)
            return 0
        except:
            return 0

    def __repr__(self):
        return f"<MateriaPrima {self.nombre}>"
    
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

    nombre = db.Column(db.String(100), nullable=False, unique=True)

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

    imagen_url = db.Column(db.LargeBinary, unique=True)

    dias_caducidad = db.Column(db.Integer, default=3)

    estatus = db.Column(
        db.Enum('activo','inactivo'),
        default='activo'
    )


    
class Receta(db.Model):

    __tablename__ = 'recetas'

    id_receta = db.Column(db.Integer, primary_key=True)

    id_producto = db.Column(
        db.Integer,
        db.ForeignKey('productos.id_producto'),
        nullable=False,
        unique=True 
    )

    nombre = db.Column(db.String(100), nullable=False)

    descripcion = db.Column(db.Text)

    rendimiento_piezas = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    estatus = db.Column(
        db.Enum('activo', 'inactivo'),
        default='activo'
    )

    # relaciones
    producto = db.relationship(
        'Producto',
        backref=db.backref('receta', uselist=False)  
    )

    ingredientes = db.relationship(
        'DetalleReceta',
        backref='receta',
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<Receta {self.nombre}>'
    
class DetalleReceta(db.Model):

    __tablename__ = 'detalle_receta'

    id_detalle = db.Column(db.Integer, primary_key=True)
    
    tipo = db.Column(db.String(10), nullable=True)

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

    cantidad = db.Column(   
        db.Numeric(12,4),
        nullable=False
    )
    
    precio_por_unidad = db.Column(db.Numeric(12,4), nullable=True)  # Precio por gramo/ml/pieza
    costo_total_ingrediente = db.Column(db.Numeric(12,4), nullable=True)  # Costo total para la rece

    
    __table_args__ = (
        db.UniqueConstraint('id_receta', 'id_materia', name='unique_receta_materia'),
    )

    # relaciones
    materia = db.relationship(
        'MateriaPrima',
        backref='usos_en_recetas'
    )

    def __repr__(self):
        return f'<DetalleReceta {self.id_detalle}>'
    
    
    
class Orden(db.Model):
    __tablename__ = "ordenes"

    id_orden = db.Column(db.Integer, primary_key=True)

    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)

    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    fecha_produccion = db.Column(db.Date, nullable=False)


    total_unidades = db.Column(db.Integer, default=0)
    costo_total_estimado = db.Column(db.Numeric(10,2), default=0.00)

    estatus = db.Column(
    db.Enum('planeada', 'preparacion', 'completada', 'cancelada'),
    default='planeada'
)

    notas = db.Column(db.Text)

    detalles = db.relationship('DetalleOrden', backref='orden', cascade="all, delete-orphan")
    
    sucursal = db.relationship('Sucursal')

class DetalleOrden(db.Model):
    __tablename__ = "detalle_orden"

    id_detalle_orden = db.Column(db.Integer, primary_key=True)

    id_orden = db.Column(db.Integer, db.ForeignKey('ordenes.id_orden'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)

    cantidad = db.Column(db.Integer, nullable=False)
    cantidad_recetas = db.Column(db.Integer, default=1) 

    costo_unitario_produccion = db.Column(db.Numeric(10,2), nullable=False)
    subtotal_costo = db.Column(db.Numeric(10,2), nullable=False)

    producto = db.relationship('Producto')
    


class Compra(db.Model):
    __tablename__ = 'compras'
    
    id_compra = db.Column(db.Integer, primary_key=True)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)

    fecha_orden = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    fecha_estimada_entrega = db.Column(db.Date, nullable=False)
    fecha_entrega = db.Column(db.DateTime, nullable=True) 

    estado = db.Column(db.String(50), default="solicitada")
    notas = db.Column(db.Text)
    total = db.Column(db.Float, default=0.0)

    proveedor = db.relationship('Proveedor')
    sucursal = db.relationship('Sucursal')
    detalles = db.relationship(
    'DetalleCompra',
    back_populates='compra',
    cascade='all, delete-orphan'
)


class DetalleCompra(db.Model):
    __tablename__ = 'detalles_compra'
    
    id_detalle = db.Column(db.Integer, primary_key=True)
    id_compra = db.Column(db.Integer, db.ForeignKey('compras.id_compra'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)

    cantidad = db.Column(db.Float, nullable=False)
    tipo_empaque = db.Column(db.String(20))

    precio_unitario_compra = db.Column(db.Float, nullable=True)
    subtotal = db.Column(db.Float, nullable=True)

    materia = db.relationship('MateriaPrima')
    
    compra = db.relationship(
    'Compra',
    back_populates='detalles'
)
class InventarioMateriaPrima(db.Model):
    __tablename__ = 'inventario_materia_prima'

    id_inventario = db.Column(db.Integer, primary_key=True)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)

    stock_actual = db.Column(db.Float, default=0)
    stock_minimo = db.Column(db.Float, default=0)

    materia = db.relationship('MateriaPrima')
    sucursal = db.relationship('Sucursal')

class MovimientoInventario(db.Model):
    __tablename__ = 'movimientos_inventario'

    id_movimiento = db.Column(db.Integer, primary_key=True)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)

    tipo = db.Column(db.String(20))
    cantidad = db.Column(db.Float)
    
    stock_antes = db.Column(db.Float, default=0)
    stock_despues = db.Column(db.Float, default=0)
    
    referencia = db.Column(db.String(100))
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relaciones
    materia = db.relationship('MateriaPrima')
    sucursal = db.relationship('Sucursal')
    
class InventarioProducto(db.Model):
    __tablename__ = 'inventario_producto'
    
    id_inventario = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)
    
    stock_actual = db.Column(db.Integer, default=0)  # Cantidad en piezas/unidades
    stock_minimo = db.Column(db.Integer, default=0)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    producto = db.relationship('Producto')
    sucursal = db.relationship('Sucursal')
    
    __table_args__ = (
        db.UniqueConstraint('id_producto', 'id_sucursal', name='unique_producto_sucursal'),
    )

class MovimientoInventarioProducto(db.Model):
    __tablename__ = 'movimientos_inventario_producto'
    
    id_movimiento = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)
    
    tipo = db.Column(db.String(30))  # entrada_produccion, salida_venta, ajuste
    cantidad = db.Column(db.Integer)
    
    referencia = db.Column(db.String(100))
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    producto = db.relationship('Producto')
    sucursal = db.relationship('Sucursal')
    
class Sucursal(db.Model):
    __tablename__ = 'sucursales'

    id_sucursal = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    ciudad = db.Column(db.String(100))
    estado = db.Column(db.String(50))
    codigo_postal = db.Column(db.String(10))
    email = db.Column(db.String(100))
    imagen_url = db.Column(db.String(255))
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
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

class Bitacora(db.Model):
    __tablename__ = 'bitacora'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)  # Cambia 'id' por 'id_usuario'
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    accion = db.Column(db.String(50), nullable=False)
    tabla = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    datos_anteriores = db.Column(db.Text)
    datos_nuevos = db.Column(db.Text)
    
    # Relación con usuario
    usuario = db.relationship('Usuario', backref='bitacora')