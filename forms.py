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


from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, EmailField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, Optional, Email, Regexp, NumberRange, ValidationError
from datetime import date

class EmpleadoForm(FlaskForm):
    id_empleado = IntegerField("ID")
    nombre = StringField("Nombre", [
        DataRequired(message="El nombre es obligatorio"),
        Length(min=3, max=100, message="El nombre debe tener entre 3 y 100 caracteres"),
        Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 
               message="El nombre solo debe contener letras y espacios")
    ])

    telefono = StringField("Teléfono", [
        Optional(),
        Regexp(r'^\d{10,15}$', message="El teléfono debe tener entre 10 y 15 dígitos numéricos")
    ])
    email = EmailField("Correo", [
        DataRequired(message="El correo es necesario para el acceso"),
        Email(message="Ingresa un correo electrónico válido")
    ])

    direccion = StringField("Dirección", [Optional(), Length(max=200)])
    puesto = StringField("Puesto", [DataRequired(message="Define el puesto del empleado"), Length(max=80)])

    salario = DecimalField("Salario", [
        DataRequired(message="El salario es obligatorio"),
        NumberRange(min=0, message="El salario no puede ser un número negativo")
    ])

    fecha_nacimiento = DateField("Fecha de nacimiento", [DataRequired()], format='%Y-%m-%d')
    fecha_contratacion = DateField("Fecha de contratación", [DataRequired()], format='%Y-%m-%d')
    
    id_rol = SelectField("Rol", coerce=int)
    estatus = SelectField("Estatus", choices=[("activo","Activo"),("inactivo","Inactivo")])

    def validate_fecha_nacimiento(self, field):
        today = date.today()
        edad = today.year - field.data.year - ((today.month, today.day) < (field.data.month, field.data.day))
        if edad < 18:
            raise ValidationError("El empleado debe ser mayor de 18 años.")
    def validate_fecha_contratacion(self, field):
        if self.fecha_nacimiento.data and field.data < self.fecha_nacimiento.data:
            raise ValidationError("La fecha de contratación no puede ser anterior a la de nacimiento.")

class ClienteForm(FlaskForm):
    id_cliente = IntegerField("ID")

    nombre = StringField("Nombre", [
        DataRequired(message="El nombre del cliente es obligatorio"),
        Length(min=3, max=100, message="El nombre debe tener entre 3 y 100 caracteres"),
        Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 
               message="El nombre no puede contener números ni símbolos")
    ])
    telefono = StringField("Teléfono", [
        Optional(),
        Regexp(r'^\d{10,13}$', message="El teléfono debe tener entre 10 y 13 números")
    ])
    email = EmailField("Correo", [
        Optional(),
        Email(message="Formato de correo electrónico inválido")
    ])

    direccion = StringField("Dirección", [
        Optional(), 
        Length(max=200, message="La dirección es demasiado larga")
    ])

    estatus = SelectField("Estatus", choices=[
        ("activo","Activo"),
        ("inactivo","Inactivo")
    ])

class RolForm(FlaskForm):
    id_rol = IntegerField("ID")
    nombre = StringField("Nombre del rol", [
        DataRequired(message="El nombre del rol es obligatorio."),
        Length(min=3, max=50, message="El nombre debe tener entre 3 y 50 caracteres."),
        Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 
               message="El nombre del rol solo puede contener letras y espacios.")
    ])
    descripcion = StringField("Descripción", [
        Optional(),
        Length(max=150, message="La descripción es demasiado larga (máximo 150 caracteres).")
    ])


class UsuarioForm(FlaskForm):
    id_usuario = IntegerField("ID")

    nombre = StringField("Nombre completo", [
        DataRequired(message="El nombre es obligatorio"),
        Length(min=3, max=100),
        Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 
               message="El nombre no debe contener números ni caracteres especiales")
    ])

    email = EmailField("Correo", [
        DataRequired(message="El correo es obligatorio"),
        Email(message="Ingresa un correo electrónico válido")
    ])

    password = PasswordField("Contraseña", [
        Optional(), # Permite que sea opcional al editar
        Length(min=6, message="La contraseña debe tener al menos 6 caracteres")
    ])

    id_rol = SelectField("Rol", coerce=int, validators=[
        DataRequired(message="Debes seleccionar un rol")
    ])

    activo = SelectField("Estatus", 
                         choices=[("1","Activo"), ("0","Inactivo")], 
                         coerce=str,
                         validators=[DataRequired(message="El estatus es obligatorio")])

class LoginForm(FlaskForm):
    email    = EmailField('Correo Electrónico', [DataRequired(), Email()])
    password = PasswordField('Contraseña', [DataRequired()])
    remember = BooleanField('Recordarme')


class RegisterForm(FlaskForm):
    # 1. NOMBRE: Sin números, símbolos y con mensajes claros
    nombre = StringField('Nombre Completo', [
        DataRequired(message='Tu nombre es indispensable.'),
        Length(min=2, max=100, message='El nombre es demasiado corto o largo.'),
        Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 
               message='El nombre solo puede contener letras y espacios.')
    ])

    email = EmailField('Correo Electrónico', [
        DataRequired(message='El correo es obligatorio para crear tu cuenta.'),
        Email(message='Ingresa un formato de correo válido (ejemplo@correo.com).')
    ])

    password = PasswordField('Contraseña', [
        DataRequired(message='Debes definir una contraseña.'),
        Length(min=6, message='Por seguridad, usa al menos 6 caracteres.')
    ])

    password2 = PasswordField('Repite la Contraseña', [
        DataRequired(message='Confirma tu contraseña para continuar.'),
        EqualTo('password', message='Las contraseñas no coinciden. Inténtalo de nuevo.')
    ])


    def validate_email(self, email):
        from models import Usuario
        # Buscamos si el correo ya existe para evitar duplicados
        if Usuario.query.filter_by(email=email.data).first():
            raise ValidationError('Este correo ya está registrado. Intenta iniciar sesión.')