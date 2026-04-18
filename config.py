import os 

from sqlalchemy import create_engine

class Config(object):
    SECRET_KEY="ClaveSecreta"
    SESSION_COOKIE_SECURE=False


class DevelopmentConfig(Config):
    DEBUG=True
    SQLALCHEMY_DATABASE_URI='mysql+pymysql://marina:Marina123$@127.0.0.1/panaderia_db4'
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    
    MONGO_URI = 'mongodb://localhost:27017/panaderia_nosql_db'

    