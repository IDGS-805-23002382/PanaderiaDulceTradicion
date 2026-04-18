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
    estatus = db.Column(db.Enum('activo', 'inactivo'), default='activo')

    fecha_creacion = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class MateriaPrima(db.Model):
    __tablename__ = 'materias_primas'

    id_materia = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    unidad_base = db.Column(db.String(20), nullable=False)  # g, ml, pza
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'))
    estatus = db.Column(db.String(20), default="activo")

    proveedor = db.relationship('Proveedor')


class Categoria(db.Model):
    __tablename__ = 'categorias'

    id_categoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False, unique=True)
    descripcion = db.Column(db.String(200))
    imagen = db.Column(db.LargeBinary)
    estatus = db.Column(db.Enum('activo', 'inactivo'), default='activo')

    productos = db.relationship('Producto', back_populates='categoria')


class Producto(db.Model):
    __tablename__ = 'productos'

    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria'), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    costo_unitario_estimado = db.Column(db.Numeric(10, 2), default=0.00)
    imagen_url = db.Column(db.LargeBinary)
    dias_caducidad = db.Column(db.Integer, default=3)
    estatus = db.Column(db.Enum('activo', 'inactivo'), default='activo')

    # RELACIONES
    categoria = db.relationship('Categoria', back_populates='productos')
    receta = db.relationship('Receta', back_populates='producto', uselist=False)


class Receta(db.Model):
    __tablename__ = 'recetas'

    id_receta = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    rendimiento_piezas = db.Column(db.Integer, nullable=False, default=1)
    estatus = db.Column(db.Enum('activo', 'inactivo'), default='activo')

    producto = db.relationship('Producto', back_populates='receta')
    ingredientes = db.relationship('DetalleReceta', backref='receta', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Receta {self.nombre}>'


class DetalleReceta(db.Model):
    __tablename__ = 'detalle_receta'

    id_detalle = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=True)
    id_receta = db.Column(db.Integer, db.ForeignKey('recetas.id_receta'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)
    cantidad = db.Column(db.Numeric(12, 4), nullable=False)
    precio_por_unidad = db.Column(db.Numeric(12, 4), nullable=True)
    costo_total_ingrediente = db.Column(db.Numeric(12, 4), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('id_receta', 'id_materia', name='unique_receta_materia'),
    )

    materia = db.relationship('MateriaPrima', backref='usos_en_recetas')

    def __repr__(self):
        return f'<DetalleReceta {self.id_detalle}>'


class Orden(db.Model):
    __tablename__ = "ordenes"

    id_orden = db.Column(db.Integer, primary_key=True)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    fecha_produccion = db.Column(db.Date, nullable=False)
    total_unidades = db.Column(db.Integer, default=0)
    costo_total_estimado = db.Column(db.Numeric(10, 2), default=0.00)
    estatus = db.Column(db.Enum('planeada', 'preparacion', 'completada', 'cancelada'), default='planeada')
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
    costo_unitario_produccion = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal_costo = db.Column(db.Numeric(10, 2), nullable=False)

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
    detalles = db.relationship('DetalleCompra', back_populates='compra', cascade='all, delete-orphan')


class DetalleCompra(db.Model):
    __tablename__ = 'detalles_compra'

    id_detalle = db.Column(db.Integer, primary_key=True)
    id_compra = db.Column(db.Integer, db.ForeignKey('compras.id_compra'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)
    tipo_compra = db.Column(db.String(20))  # granel, empaque, caja

    # Granel
    cantidad_granel = db.Column(db.Float)
    unidad_granel = db.Column(db.String(10))

    # Empaque (bolsa, frasco, bote)
    cantidad_empaques = db.Column(db.Float)
    tipo_empaque = db.Column(db.String(20))
    contenido_empaque = db.Column(db.Float)
    unidad_contenido = db.Column(db.String(10))

    # Caja
    cantidad_cajas = db.Column(db.Float)
    piezas_por_caja = db.Column(db.Integer)
    contenido_por_pieza = db.Column(db.Float)
    unidad_contenido_caja = db.Column(db.String(10))

    # Precios
    precio_unitario_compra = db.Column(db.Float)
    subtotal = db.Column(db.Float)

    # Trazabilidad
    fecha_caducidad = db.Column(db.Date, nullable=True)
    lote = db.Column(db.String(50), nullable=True)
    fecha_fabricacion = db.Column(db.Date, nullable=True)

    materia = db.relationship('MateriaPrima')
    compra = db.relationship('Compra', back_populates='detalles')


class InventarioMateriaPrima(db.Model):
    __tablename__ = 'inventario_materia_prima'

    id_inventario = db.Column(db.Integer, primary_key=True)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)
    stock_actual = db.Column(db.Float, default=0)
    stock_minimo = db.Column(db.Float, default=0)
    lote = db.Column(db.String(50), nullable=True)
    fecha_caducidad = db.Column(db.Date, nullable=True)

    materia = db.relationship('MateriaPrima')
    sucursal = db.relationship('Sucursal')


class MovimientoInventario(db.Model):
    __tablename__ = 'movimientos_inventario'

    id_movimiento = db.Column(db.Integer, primary_key=True)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)
    tipo = db.Column(db.String(30))
    cantidad = db.Column(db.Float)
    stock_antes = db.Column(db.Float, default=0)
    stock_despues = db.Column(db.Float, default=0)
    referencia = db.Column(db.String(200))
    motivo = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    lote = db.Column(db.String(50), nullable=True)
    fecha_caducidad = db.Column(db.Date, nullable=True)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'), nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True)

    materia = db.relationship('MateriaPrima')
    sucursal = db.relationship('Sucursal')
    proveedor = db.relationship('Proveedor')
    usuario = db.relationship('Usuario')


class InventarioProducto(db.Model):
    __tablename__ = 'inventario_producto'

    id_inventario = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)
    stock_actual = db.Column(db.Integer, default=0)
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
    stock_antes = db.Column(db.Integer, default=0)
    stock_despues = db.Column(db.Integer, default=0)
    referencia = db.Column(db.String(200))
    motivo = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True)

    producto = db.relationship('Producto')
    sucursal = db.relationship('Sucursal')
    usuario = db.relationship('Usuario')


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
    imagen = db.Column(db.Text)
    horario_abierto = db.Column(db.Time, nullable=True)
    horario_cierre = db.Column(db.Time, nullable=True)
    estatus = db.Column(db.Enum('activo', 'inactivo'), default='activo')


class Rol(db.Model):
    __tablename__ = 'roles'

    id_rol = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    usuarios = db.relationship('Usuario', back_populates='rol')

    def __repr__(self):
        return f'<Rol {self.nombre}>'


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id_usuario = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    id_rol = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    two_factor_secret = db.Column(db.String(32))
    two_factor_enabled = db.Column(db.Boolean, default=True)
    codigo_2fa = db.Column(db.String(6))
    codigo_recuperacion = db.Column(db.String(6))

    # Relaciones
    rol = db.relationship('Rol', back_populates='usuarios')
    empleado = db.relationship('Empleado', back_populates='usuario', uselist=False, cascade="all, delete-orphan")
    cliente = db.relationship('Cliente', back_populates='usuario', uselist=False, cascade="all, delete-orphan")

    def get_id(self):
        return str(self.id_usuario)

    @property
    def nombre_mostrable(self):
        """Retorna el nombre real del empleado o cliente según corresponda"""
        if self.empleado:
            return self.empleado.nombre
        if self.cliente:
            return self.cliente.nombre
        return self.email.split('@')[0] if self.email else 'Usuario'


class Empleado(db.Model):
    __tablename__ = 'empleados'

    id_empleado = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    puesto = db.Column(db.String(80))
    salario = db.Column(db.Numeric(10, 2))
    fecha_nacimiento = db.Column(db.Date)
    fecha_contratacion = db.Column(db.Date)
    estatus = db.Column(db.Enum('activo', 'inactivo'), default='activo')

    usuario = db.relationship('Usuario', back_populates='empleado')


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id_cliente = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    estatus = db.Column(db.Enum('activo', 'inactivo'), default='activo')

    usuario = db.relationship('Usuario', back_populates='cliente')


class NominaIndividual(db.Model):
    """Un registro de pago por empleado por periodo."""
    __tablename__ = 'nominas_individuales'

    id_nomina_ind = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado'), nullable=False)
    id_nomina_grupal = db.Column(db.Integer, db.ForeignKey('nominas_grupales.id_nomina_grupal'), nullable=True)
    periodo = db.Column(db.Enum('quincenal', 'mensual'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    fecha_pago = db.Column(db.Date, nullable=True)
    puesto = db.Column(db.String(80))
    salario_base = db.Column(db.Numeric(10, 2), nullable=False)
    monto_pagado = db.Column(db.Numeric(10, 2), nullable=False)
    estatus = db.Column(db.Enum('pendiente', 'pagado', 'incidencia'), default='pendiente')
    notas = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    empleado = db.relationship('Empleado')

    def __repr__(self):
        return f'<NominaIndividual emp={self.id_empleado} periodo={self.periodo}>'


class NominaGrupal(db.Model):
    """Agrupa varias NominaIndividual generadas juntas."""
    __tablename__ = 'nominas_grupales'

    id_nomina_grupal = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    periodo = db.Column(db.Enum('quincenal', 'mensual'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    total_pagado = db.Column(db.Numeric(10, 2), default=0)
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    individuales = db.relationship(
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

    id_gasto = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(150), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    categoria = db.Column(db.String(80))
    notas = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<GastoExtra {self.concepto} ${self.monto}>'


class Bitacora(db.Model):
    __tablename__ = 'bitacora'

    id_bitacora = db.Column(db.Integer, primary_key=True)
    accion = db.Column(db.String(50))
    tabla = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    fecha_hora = db.Column(db.DateTime)
    usuario_nombre = db.Column(db.String(100))
    usuario_id = db.Column(db.Integer)
    ip_usuario = db.Column(db.String(50))


class Merma(db.Model):
    __tablename__ = 'mermas'

    id_merma = db.Column(db.Integer, primary_key=True)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)
    id_sucursal = db.Column(db.Integer, db.ForeignKey('sucursales.id_sucursal'), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(20), nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    fecha_caducidad = db.Column(db.Date, nullable=True)
    registrado_por = db.Column(db.String(100), default="sistema")

    materia = db.relationship('MateriaPrima')
    sucursal = db.relationship('Sucursal')


class HistorialPreciosMateriaPrima(db.Model):
    __tablename__ = 'historial_precios_materia_prima'

    id_historial = db.Column(db.Integer, primary_key=True)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias_primas.id_materia'), nullable=False)
    id_detalle_compra = db.Column(db.Integer, nullable=True)
    precio_por_gramo = db.Column(db.Numeric(12, 6), default=0.000000)
    precio_por_ml = db.Column(db.Numeric(12, 6), default=0.000000)
    precio_por_pieza = db.Column(db.Numeric(12, 4), default=0.0000)
    fecha_compra = db.Column(db.DateTime, nullable=False)
    cantidad_total_base = db.Column(db.Numeric(12, 2), default=0)
    precio_total = db.Column(db.Numeric(12, 2), default=0)
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    materia = db.relationship('MateriaPrima', backref='historial_precios')