from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import db, Producto, Categoria
from blueprints.proveedores.routesProveedores import proveedores_bp
from blueprints.categorias.routesCategorias import categorias_bp
from blueprints.materiaPrima.routesMateriaPrima import materiaPrima_bp
from blueprints.productos.routesProductos import productos_bp
from blueprints.recetas.routesRecetas import recetas_bp
from blueprints.ordenProduccion.routesOrdenProduccion import ordenProduccion_bp
from blueprints.sucursales.routesSucursales import sucursales_bp
from blueprints.clientes.routesClientes import clientes_bp
from blueprints.usuarios.routesUsuarios import usuarios_bp
from blueprints.roles.routesRoles import roles_bp
from flask_migrate import Migrate
import base64

import base64


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.register_blueprint(proveedores_bp)
app.register_blueprint(materiaPrima_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(recetas_bp)
app.register_blueprint(ordenProduccion_bp)
app.register_blueprint(sucursales_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(roles_bp)

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

@app.template_filter('b64encode')
def b64encode_filter(s):
    if s:
        return base64.b64encode(s).decode('utf-8')
    return ""

@app.route("/nosotros")
def nosotros():
    return render_template("nosotros.html")

@app.route("/gestion")
def gestion():
    return render_template("vista-empleado/gestion/gestion.html")

@app.route("/", methods=['GET','POST'])
@app.route("/home")
def home():

    productos = Producto.query.filter_by(estatus="activo").limit(3).all()

    categorias = Categoria.query.filter_by(estatus="activo").all()

    print("CATEGORIAS:", categorias)  # 👈 DEBUG

    return render_template(
        "home.html",
        productos=productos,
        categorias=categorias
    )


@app.route("/catalogo")
def catalogo():

    categoria_id = request.args.get("categoria")

    categorias = Categoria.query.filter_by(estatus="activo").all()

    if categoria_id:
        productos = Producto.query.filter_by(
            id_categoria=categoria_id,
            estatus="activo"
        ).all()
    else:
        productos = Producto.query.filter_by(
            estatus="activo"
        ).all()

    return render_template(
        "catalogo.html",
        categorias=categorias,
        productos=productos
    )
@app.route("/vistaEmpleado")
def vistaEmpleado():
    return render_template("vista-empleado/vistaEmpleado.html")

@app.route("/login")
def login():
    return render_template("login.html")
    
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Usar un puerto diferente y solo localhost
    app.run(host='127.0.0.1', port=5001, debug=True)