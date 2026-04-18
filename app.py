from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import Sucursal, Usuario, db, Producto, Categoria
from flask_pymongo import PyMongo
from flask_mail import Mail
from flask_migrate import Migrate
import base64
import folium
from flask_login import current_user

# Blueprints
from blueprints.empleados.routesEmpleados import empleados_bp
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
from blueprints.dashboard.routesDashboard import dashboard_bp
from blueprints.ventas.routesVentas import ventas_bp
from blueprints.bitacora.routesBitacora import bitacora_bp
from blueprints.ventasSucursal.routesVentasSucursal import ventasSucursal_bp
from blueprints.auth import auth_bp 

# Inicialización de extensiones
mail = Mail()
mongo = PyMongo() 
migrate = Migrate()
csrf = CSRFProtect()

app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config.from_object(DevelopmentConfig)

# Configuración de Flask-Mail (ACTUALIZADO)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'antimogonzalezmarina@gmail.com' 
app.config['MAIL_PASSWORD'] = 'rfdc zpfz afey ikck' 
app.config['MAIL_DEFAULT_SENDER'] = 'antimogonzalezmarina@gmail.com'
app.config['SECRET_KEY'] = 'mi_clave_super_secreta_123'

# --- REGISTRO DE BLUEPRINTS ---
app.register_blueprint(auth_bp)
app.register_blueprint(empleados_bp)
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
app.register_blueprint(dashboard_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(bitacora_bp)
app.register_blueprint(ventasSucursal_bp)

# --- INICIALIZACIÓN DE COMPONENTES ---
mongo.init_app(app) 
app.mongo = mongo
db.init_app(app)
mail.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.context_processor
def inject_user_permissions():
    def has_role(roles):
        if not current_user.is_authenticated:
            return False
        if isinstance(roles, str):
            roles = [roles]
        return current_user.rol.nombre in roles
    
    return dict(has_role=has_role)

# --- FILTROS ---
@app.template_filter('b64encode')
def b64encode_filter(s):
    if s:
        return base64.b64encode(s).decode('utf-8')
    return ""

# --- RUTAS ---
@app.route("/gestion")
def gestion():
    return render_template("vista-empleado/gestion/gestion.html")

@app.route("/vistaEmpleado")
def vistaEmpleado():
    return render_template("vista-empleado/vistaEmpleado.html")

@app.route("/inventarios")
def inventarios():
    return render_template("vista-empleado/inventarios/inventarios.html")

@app.route("/ordenProduccion")
def ordenProduccion():
    return render_template("vista-empleado/ordenProduccion/ordenProduccion.html")

@app.route("/nosotros")
def nosotros():
    return render_template("nosotros.html")

@app.route("/", methods=['GET','POST'])
@app.route("/home")
def home():
    productos = Producto.query.filter_by(estatus="activo").limit(3).all()
    categorias = Categoria.query.filter_by(estatus="activo").all()
    sucursal = Sucursal.query.filter_by(estatus='activo').first()
    
    mapa_html = ""

    if sucursal:
        if sucursal.latitud and sucursal.longitud:
            try:
                mapa_gen = folium.Map(
                    location=[float(sucursal.latitud), float(sucursal.longitud)], 
                    zoom_start=15,
                    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
                    attr='Google Maps'
                )
                folium.Marker(
                    [float(sucursal.latitud), float(sucursal.longitud)],
                    popup=f"<b>{sucursal.nombre}</b>",
                    icon=folium.Icon(color='red', icon='store', prefix='fa')
                ).add_to(mapa_gen)
                mapa_html = mapa_gen._repr_html_()
            except Exception as e:
                print(f"Error al generar el mapa: {e}")
    
    return render_template("home.html", 
                           productos=productos, 
                           categorias=categorias, 
                           mapa_home=mapa_html,
                           sucursal=sucursal,
                           foto_sucursal=sucursal.imagen_url if sucursal else None)

@app.route("/catalogo")
def catalogo():
    categoria_id = request.args.get("categoria")
    categorias = Categoria.query.filter_by(estatus="activo").all()
    if categoria_id:
        productos = Producto.query.filter_by(id_categoria=categoria_id, estatus="activo").all()
    else:
        productos = Producto.query.filter_by(estatus="activo").all()
    return render_template("catalogo.html", categorias=categorias, productos=productos)

@app.route("/login")
def login():
    return render_template("login.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# --- EJECUCIÓN ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5001, debug=True)