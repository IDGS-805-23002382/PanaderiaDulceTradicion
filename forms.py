from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, EmailField, SelectField, TextAreaField, DecimalField, DateField
from wtforms import validators
from wtforms.validators import DataRequired

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

    unidad_medida = StringField("Unidad de medida", [
        validators.InputRequired(message="La unidad de medida es requerida"),
        validators.Length(max=30)
    ])

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