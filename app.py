from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import db
from proveedores.routesProveedores import proveedores_bp
from materiaPrima.routesMateriaPrima import materiaPrima_bp
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.register_blueprint(proveedores_bp)
app.register_blueprint(materiaPrima_bp)

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

@app.route("/", methods=['GET','POST'])
@app.route("/home")
def home():
    return render_template("home.html")
    
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Usar un puerto diferente y solo localhost
    app.run(host='127.0.0.1', port=5001, debug=True)