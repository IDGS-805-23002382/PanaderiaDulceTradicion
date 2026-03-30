from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from models import Producto, Orden, db, Receta, DetalleOrden, MateriaPrima, Sucursal
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import forms
from . import ordenProduccion_bp

@ordenProduccion_bp.route('/ordenes')
def listarOrdenes():

    ordenes = Orden.query.all()

    return render_template(
        'modulo-ordenes/modulo-ordenes.html',
        ordenes=ordenes
    )

@ordenProduccion_bp.route('/agregarOrden', methods=['GET', 'POST'])
def agregarOrden():
    form = forms.OrdenForm()
    
    # Cargar selects siempre
    form.id_sucursal.choices = [(s.id_sucursal, s.nombre) for s in Sucursal.query.all()]
    productos = Producto.query.filter_by(estatus='activo').all()
    form.id_producto.choices = [(p.id_producto, p.nombre) for p in productos]

    # Variables para el resumen (se pasan al HTML)
    receta_detectada = "Seleccione un producto"
    total_venta = 0.0

    if request.method == 'POST':
        id_prod = request.form.get('id_producto')
        cant = request.form.get('cantidad', 0)
        
        if id_prod:
            producto = Producto.query.get(id_prod)
            # Buscar la receta para mostrarla en el resumen
            receta = Receta.query.filter_by(id_producto=id_prod, estatus='activo').first()
            
            if receta:
                receta_detectada = receta.nombre
                if cant:
                    total_venta = float(producto.precio_venta) * int(cant)
            else:
                receta_detectada = "Sin receta configurada"

        # SI EL USUARIO HIZO CLIC EN "CONFIRMAR" (El botón de envío final)
        if 'btn_confirmar' in request.form and form.validate_on_submit():
            # ... AQUÍ VA TU LÓGICA DE GUARDADO Y DESCUENTO DE STOCK ...
            # (La que ya tenías que valida stock y hace db.session.commit)
            flash("Orden procesada con éxito", "success")
            return redirect(url_for('ordenProduccion.agregarOrden'))

    return render_template('modulo-ordenes/agregarOrden.html', 
                           form=form, 
                           productos=productos,
                           receta_nombre=receta_detectada,
                           total_venta=total_venta)

    