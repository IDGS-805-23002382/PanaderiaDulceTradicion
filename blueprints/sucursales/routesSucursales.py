from flask import render_template, request, url_for
from werkzeug.utils import redirect
from forms import SucursalForm
from models import db, Sucursal
from . import sucursales_bp
from datetime import datetime  
import folium
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message
from flask_login import login_required

@sucursales_bp.route('/sucursales/')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def sucursales():
    # Vista para el CLIENTE (Mapa estético)
    sucursales_list = Sucursal.query.filter_by(estatus='activo').all()
    mapa_gen = folium.Map(
        location=[21.1219, -101.6825], 
        zoom_start=12, 
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google Maps Satellite'
    )
    for s in sucursales_list:
        if s.latitud and s.longitud:
            folium.Marker(
                [float(s.latitud), float(s.longitud)],
                popup=f"<b>{s.nombre}</b>",
                icon=folium.Icon(color='red', icon='store', prefix='fa')
            ).add_to(mapa_gen)
    
    return render_template("modulo-sucursales/vistaMapa.html", 
                           sucursales=sucursales_list, 
                           mapa_html=mapa_gen._repr_html_())

@sucursales_bp.route('/gestion-sucursales/')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def gestion_sucursales():
    search = request.args.get('search')
    # Capturamos si el usuario quiere ver todas o solo activas
    ver_todos = request.args.get('ver_todos', '0') # '0' por defecto (solo activas)
    
    query = Sucursal.query
    
    # Lógica de filtro por estatus
    if ver_todos == '0':
        query = query.filter_by(estatus='activo')
    
    # Lógica de búsqueda
    if search:
        query = query.filter(
            (Sucursal.nombre.like(f'%{search}%')) | 
            (Sucursal.ciudad.like(f'%{search}%'))
        )
    
    sucursales_list = query.all()
    
    # Mapa decorativo para la gestión
    mapa = folium.Map(location=[21.1219, -101.6825], zoom_start=12, 
                      tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
    
    return render_template("modulo-sucursales/listaSucursales.html", 
                           sucursales=sucursales_list, 
                           mapa_html=mapa._repr_html_(),
                           ver_todos=ver_todos)

@sucursales_bp.route('/registrarSucursal', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def registrarSucursal():
    form = SucursalForm()
    if form.validate_on_submit():
        
        horario_abierto = None
        horario_cierre = None
        
        if request.form.get('horario_abierto'):
            horario_abierto = datetime.strptime(request.form.get('horario_abierto'), '%H:%M').time()
        if request.form.get('horario_cierre'):
            horario_cierre = datetime.strptime(request.form.get('horario_cierre'), '%H:%M').time()
            
        
        nueva_sucursal = Sucursal(
            nombre=form.nombre.data,
            direccion=form.direccion.data,
            telefono=form.telefono.data,
            ciudad=form.ciudad.data,
            email=form.email.data,
            codigo_postal=form.codigo_postal.data,
            estado=form.estado.data,
            imagen_url=form.imagen_url.data,
            latitud=form.latitud.data,
            longitud=form.longitud.data,
            horario_abierto=horario_abierto,
            horario_cierre=horario_cierre,
            estatus='activo'
        )
        db.session.add(nueva_sucursal)
        db.session.commit()
        return redirect(url_for('sucursales.gestion_sucursales'))
    return render_template('modulo-sucursales/formSucursales.html', form=form)

@sucursales_bp.route('/editarSucursal/<int:id>', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def editarSucursal(id):
    sucursal = Sucursal.query.get_or_404(id)
    form = SucursalForm(obj=sucursal)
    if form.validate_on_submit():
        form.populate_obj(sucursal)
        
        if request.form.get('horario_abierto'):
                    sucursal.horario_abierto = datetime.strptime(request.form.get('horario_abierto'), '%H:%M').time()
        if request.form.get('horario_cierre'):
                    sucursal.horario_cierre = datetime.strptime(request.form.get('horario_cierre'), '%H:%M').time()
                
        nuevo_estatus = request.form.get('estatus')
        if nuevo_estatus:
                    sucursal.estatus = nuevo_estatus
        db.session.commit()
        return redirect(url_for('sucursales.gestion_sucursales'))
    return render_template('modulo-sucursales/editarSucursales.html', form=form, sucursal=sucursal)

@sucursales_bp.route('/desactivarSucursal/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def desactivarSucursal(id):
    sucursal = Sucursal.query.get_or_404(id)
    # Convertimos a minúsculas para comparar y evitar errores de dedo
    estado_actual = sucursal.estatus.lower() if sucursal.estatus else 'inactivo'
    
    if estado_actual == 'activo':
        sucursal.estatus = 'inactivo'
    else:
        sucursal.estatus = 'activo'
        
    db.session.commit()
    return redirect(url_for('sucursales.gestion_sucursales'))

@sucursales_bp.route('/verMapa/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def verMapa(id):
    sucursal = Sucursal.query.get_or_404(id)
    try:
        lat = float(sucursal.latitud) if sucursal.latitud else 21.1219
        lng = float(sucursal.longitud) if sucursal.longitud else -101.6825
    except:
        lat, lng = 21.1219, -101.6825

    mapa = folium.Map(location=[lat, lng], zoom_start=18, 
                      tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
    folium.Marker([lat, lng], popup=sucursal.nombre).add_to(mapa)
    
    return render_template("modulo-sucursales/verMapa.html", 
                           sucursal=sucursal, 
                           mapa_html=mapa._repr_html_())