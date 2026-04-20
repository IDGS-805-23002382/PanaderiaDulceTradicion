from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_pymongo import PyMongo
from flask_login import LoginManager

# Solo creamos los objetos, no los vinculamos a la "app" todavía
db = SQLAlchemy()
mail = Mail()
mongo = PyMongo()
login_manager = LoginManager()