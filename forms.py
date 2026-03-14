from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, EmailField, SelectField
from wtforms import validators
from wtforms.validators import DataRequired

class UserForm(FlaskForm):
    id = IntegerField("ID")
    
    nombre = StringField("Nombre", [
        validators.InputRequired(message="El campo es requerido"),
        validators.Length(min=4, max=10, message="El nombre debe tener entre 4 y 10 caracteres")
    ])
    
    apellidos = StringField("apellidos", [
        validators.InputRequired(message="El campo es requerido")
    ])
    
    email = EmailField("Correo", [
        validators.InputRequired(message="El campo es requerido"),
        validators.Email(message="Ingrese un correo válido")
    ])
    
    telefono = StringField("Telefono", [
        validators.InputRequired(message="El campo es requerido")
        
    ])