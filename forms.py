from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, EmailField, FileField, SelectField, TextAreaField, DecimalField, DateField
from wtforms import validators, PasswordField, BooleanField
from wtforms.validators import Length, Email, Optional, EqualTo, ValidationError, DataRequired


class ProveedorForm(FlaskForm):

    id_proveedor = IntegerField("ID")

    nombre = StringField("Nombre", [
        validators.InputRequired(message="El nombre es requerido"),
        validators.Length(min=3, max=100, message="El nombre debe tener entre 3 y 100 caracteres")
    ])

    telefono = StringField("Teléfono", [
        validators.InputRequired(message="El teléfono es requerido"),
        validators.Length(min=7, max=20)
    ])

    email = EmailField("Correo", [
        validators.InputRequired(message="El correo es requerido"),
        validators.Email(message="Ingrese un correo válido")
    ])

    direccion = StringField("Dirección", [
        validators.InputRequired(message="La dirección es requerida"),
        validators.Length(max=200)
    ])

    contacto = StringField("Persona de contacto", [
        validators.InputRequired(message="El contacto es requerido"),
        validators.Length(max=100)
    ])

    notas = TextAreaField("Notas")

    estatus = SelectField(
        "Estatus",
        choices=[
            ("activo", "Activo"),
            ("inactivo", "Inactivo")
        ]
    )
    
class MateriaPrimaForm(FlaskForm):

    id_materia = IntegerField("ID")

    nombre = StringField("Nombre de la materia prima", [
        validators.InputRequired(message="El nombre es requerido"),
        validators.Length(min=3, max=100)
    ])

    unidad_medida = SelectField(
    "Unidad de medida",
    choices=[
        ("kg", "Kilogramos (kg)"),
        ("g", "Gramos (g)"),
        ("l", "Litros (L)"),
        ("ml", "Mililitros (ml)"),
        ("pz", "Piezas"),
        ("bulto", "Bultos"),
        ("caja", "Cajas"),
        ("paquete", "Paquetes")
    ],
    validators=[DataRequired(message="Seleccione una unidad de medida")]
)

    stock_actual = DecimalField("Stock actual", [
        validators.InputRequired(message="El stock actual es requerido")
    ])

    stock_minimo = DecimalField("Stock mínimo", [
        validators.InputRequired(message="El stock mínimo es requerido")
    ])

    precio_unitario = DecimalField("Precio unitario", [
        validators.InputRequired(message="El precio es requerido")
    ])

    id_proveedor = SelectField(
        "Proveedor",
        coerce=int
    )

    fecha_ultima_compra = DateField(
        "Fecha última compra",
        format='%Y-%m-%d'
    )

    estatus = SelectField(
        "Estatus",
        choices=[
            ("activo", "Activo"),
            ("inactivo", "Inactivo")
        ]
    )

class CategoriaForm(FlaskForm):

    id_categoria = IntegerField("ID")

    nombre = StringField("Nombre", [
        validators.InputRequired(message="El nombre de la categoría es requerido"),
        validators.Length(min=3, max=80, message="Debe tener entre 3 y 80 caracteres")
    ])

    descripcion = TextAreaField("Descripción", [
        validators.Optional(),
        validators.Length(max=200, message="Máximo 200 caracteres")
    ])
    
    imagen = FileField("Imagen")

    estatus = SelectField(
        "Estatus",
        choices=[
            ("activo", "Activo"),
            ("inactivo", "Inactivo")
        ]
    )
    
class ProductoForm(FlaskForm):

    id_producto = IntegerField("ID")

    nombre = StringField("Nombre del producto", [
        validators.InputRequired(message="El nombre es requerido"),
        validators.Length(min=3, max=100)
    ])

    descripcion = TextAreaField("Descripción")

    id_categoria = SelectField(
        "Categoría",
        coerce=int,
        validators=[DataRequired(message="Seleccione una categoría")]
    )

    precio_venta = DecimalField("Precio de venta", [
        validators.InputRequired(message="El precio es requerido")
    ])

    costo_unitario_estimado = DecimalField("Costo estimado", [
        validators.Optional()]
    )

    imagen_url = StringField("URL de imagen")

    dias_caducidad = IntegerField("Días de caducidad", [
        validators.InputRequired(message="Indique los días de caducidad")
    ])

    estatus = SelectField(
        "Estatus",
        choices=[
            ("activo", "Activo"),
            ("inactivo", "Inactivo")
        ]
    )
    
class RecetaForm(FlaskForm):

    id_receta = IntegerField("ID")

    id_producto = SelectField(
        "Producto",
        coerce=int,
        validators=[
            validators.InputRequired(message="Seleccione un producto")
        ]
    )

    nombre = StringField("Nombre de la receta", [
        validators.InputRequired(message="El nombre es requerido"),
        validators.Length(min=3, max=100)
    ])

    descripcion = TextAreaField("Descripción")

    rendimiento_piezas = IntegerField(
        "Rendimiento (piezas)",
        [
            validators.InputRequired(
                message="Indique el rendimiento de la receta"
            )
        ],
        default=20
    )

    estatus = SelectField(
        "Estatus",
        choices=[
            ("activo", "Activo"),
            ("inactivo", "Inactivo")
        ]
    )
    

class OrdenForm(FlaskForm):

    id_orden = IntegerField("ID")

    cliente_nombre = StringField(
        "Nombre del cliente",
        [
            validators.InputRequired(message="El nombre del cliente es requerido"),
            validators.Length(min=3, max=100, message="Debe tener entre 3 y 100 caracteres")
        ]
    )

    cliente_telefono = StringField(
        "Teléfono",
        [
            validators.InputRequired(message="El teléfono es requerido"),
            validators.Length(min=7, max=20, message="Debe tener entre 7 y 20 caracteres")
        ]
    )

    id_producto = SelectField(
        "Producto",
        coerce=int,
        validators=[
            DataRequired(message="Seleccione un producto")
        ]
    )

    cantidad = IntegerField(
        "Cantidad",
        [
            validators.InputRequired(message="La cantidad es requerida"),
            validators.NumberRange(min=1, message="Debe ser mayor a 0")
        ]
    )

class SucursalForm(FlaskForm):    
    nombre = StringField("Nombre", [validators.InputRequired()])
    direccion = StringField("Dirección", [validators.InputRequired()])
    telefono = StringField("Teléfono")
    ciudad = StringField("Ciudad")


class EmpleadoForm(FlaskForm):
    id_empleado        = IntegerField("ID")
    nombre             = StringField("Nombre", [DataRequired(), Length(min=3, max=100)])
    telefono           = StringField("Teléfono", [Optional(), Length(max=20)])
    email              = EmailField("Correo", [Optional(), Email()])
    direccion          = StringField("Dirección", [Optional(), Length(max=200)])
    puesto             = StringField("Puesto", [Optional(), Length(max=80)])
    salario            = DecimalField("Salario", [Optional()])
    fecha_nacimiento   = DateField("Fecha de nacimiento", [Optional()], format='%Y-%m-%d')
    fecha_contratacion = DateField("Fecha de contratación", [Optional()], format='%Y-%m-%d')
    id_rol             = SelectField("Rol", coerce=int)
    estatus            = SelectField("Estatus", choices=[("activo","Activo"),("inactivo","Inactivo")])


class ClienteForm(FlaskForm):
    id_cliente = IntegerField("ID")
    nombre     = StringField("Nombre", [DataRequired(), Length(min=3, max=100)])
    telefono   = StringField("Teléfono", [Optional(), Length(max=20)])
    email      = EmailField("Correo", [Optional(), Email()])
    direccion  = StringField("Dirección", [Optional(), Length(max=200)])
    estatus    = SelectField("Estatus", choices=[("activo","Activo"),("inactivo","Inactivo")])


class RolForm(FlaskForm):
    id_rol      = IntegerField("ID")
    nombre      = StringField("Nombre del rol", [DataRequired(), Length(min=2, max=50)])
    descripcion = StringField("Descripción", [Optional(), Length(max=150)])


class UsuarioForm(FlaskForm):
    id_usuario = IntegerField("ID")
    nombre     = StringField("Nombre completo", [DataRequired(), Length(min=3, max=100)])
    email      = EmailField("Correo", [DataRequired(), Email()])
    password   = PasswordField("Contraseña", [Optional(), Length(min=6)])
    id_rol     = SelectField("Rol", coerce=int)
    activo     = SelectField("Estatus", choices=[("1","Activo"),("0","Inactivo")], coerce=str)

class LoginForm(FlaskForm):
    email    = EmailField('Correo Electrónico', [DataRequired(), Email()])
    password = PasswordField('Contraseña', [DataRequired()])
    remember = BooleanField('Recordarme')


