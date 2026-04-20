import os 
from sqlalchemy import create_engine

class Config(object):
    SECRET_KEY="ClaveSecreta"
    SESSION_COOKIE_SECURE=False


class DevelopmentConfig(Config):
    DEBUG=True
    # Contraseña correcta: 'root' (sin $)
    SQLALCHEMY_DATABASE_URI='mysql+pymysql://root:root@localhost/panaderia_db4'
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    
    MONGO_URI = 'mongodb://localhost:27017/panaderia_nosql_db'