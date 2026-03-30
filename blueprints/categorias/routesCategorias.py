from flask import render_template, request, redirect, url_for, flash, Response
from models import Categoria, db, Producto
from sqlalchemy import or_
from . import categorias_bp
import forms

@categorias_bp.route('/categorias')
def categorias():

    buscar = request.args.get("buscar", "")
    estatus = request.args.get("estatus", "")
    orden = request.args.get("orden", "")

    query = Categoria.query

    # BUSCAR
    if buscar.strip():
        query = query.filter(
            or_(
                Categoria.nombre.ilike(f"%{buscar}%"),
                Categoria.descripcion.ilike(f"%{buscar}%")
            )
        )

    # FILTRAR ESTATUS
    if estatus:
        query = query.filter(Categoria.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(Categoria.nombre.asc())
    elif orden == "za":
        query = query.order_by(Categoria.nombre.desc())

    categorias = query.all()

    return render_template(
        "modulo-categorias/modulo-categorias.html",
        categorias=categorias
    )

# AGREGAR
@categorias_bp.route('/registrarCategoria', methods=['GET','POST'])
def agregarCategoria():

    form = forms.CategoriaForm()

    if form.validate_on_submit():

        archivo = request.files.get("imagen")

        imagen_binaria = None
        if archivo and archivo.filename != "":
            imagen_binaria = archivo.read()

        nueva_categoria = Categoria(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            imagen=imagen_binaria,   
            estatus=form.estatus.data
        )

        db.session.add(nueva_categoria)
        db.session.commit()

        flash("Categoría registrada correctamente", "success")

        return redirect(url_for('categorias.categorias'))

    return render_template(
        'modulo-categorias/agregarCategoria.html',
        form=form
    )

# EDITAR
@categorias_bp.route('/editarCategoria/<int:id>', methods=['GET','POST'])
def modificarCategoria(id):

    categoria = Categoria.query.get_or_404(id)

    form = forms.CategoriaForm(obj=categoria)

    if form.validate_on_submit():
        
        # VALIDACIÓN: Verificar si ya existe otra categoría con el mismo nombre
        categoria_existente = Categoria.query.filter(
            Categoria.nombre == form.nombre.data,
            Categoria.id_categoria != id  # Excluir la categoría actual
        ).first()
        
        if categoria_existente:
            flash(f"Ya existe otra categoría con el nombre '{form.nombre.data}'. Por favor, use un nombre diferente.", "danger")
            # Mantener los datos del formulario para mostrarlos nuevamente
            return render_template('modulo-categorias/modificarCategoria.html', 
                                 form=form, 
                                 categoria=categoria)

        archivo = request.files.get("imagen")

        # SOLO actualizar si sube nueva imagen
        if archivo and archivo.filename != "":
            categoria.imagen = archivo.read()

        categoria.nombre = form.nombre.data
        categoria.descripcion = form.descripcion.data
        categoria.estatus = form.estatus.data

        try:
            db.session.commit()
            flash("Categoría actualizada correctamente", "success")
            return redirect(url_for('categorias.categorias'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar: {str(e)}", "danger")
            return render_template('modulo-categorias/modificarCategoria.html', 
                                 form=form, 
                                 categoria=categoria)

   
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error en {field}: {error}", "danger")
    
    return render_template(
        'modulo-categorias/modificarCategoria.html',
        form=form,
        categoria=categoria
    )

# DETALLE
@categorias_bp.route('/detalleCategoria/<int:id>')
def detallesCategoria(id):

    categoria = Categoria.query.get_or_404(id)
    
    # Obtener todos los productos relacionados con esta categoría
    productos = Producto.query.filter_by(id_categoria=id).all()
    
    # Opcional: Contar productos activos e inactivos
    productos_activos = Producto.query.filter_by(id_categoria=id, estatus='activo').count()
    productos_inactivos = Producto.query.filter_by(id_categoria=id, estatus='inactivo').count()
    total_productos = len(productos)

    return render_template(
        'modulo-categorias/detallesCategoria.html',
        categoria=categoria,
        productos=productos,
        total_productos=total_productos,
        productos_activos=productos_activos,
        productos_inactivos=productos_inactivos
    )

@categorias_bp.route('/eliminarCategoria/<int:id>', methods=['GET','POST'])
def eliminarCategoria(id):

    categoria = Categoria.query.get_or_404(id)

    if request.method == 'POST':

        if categoria.estatus == "inactivo":
            flash(f"La categoría '{categoria.nombre}' ya está desactivada.", "warning")
            return render_template(
                'modulo-categorias/eliminarCategoria.html',
                categoria=categoria
            )

        categoria.estatus = "inactivo"
        db.session.commit()

        flash(f"La categoría '{categoria.nombre}' fue desactivada correctamente.", "success")

        # 👇 IMPORTANTE: regresar a la misma vista
        return render_template(
            'modulo-categorias/eliminarCategoria.html',
            categoria=categoria
        )

    return render_template(
        'modulo-categorias/eliminarCategoria.html',
        categoria=categoria
    )

# MOSTRAR IMAGEN
@categorias_bp.route('/categoria_imagen/<int:id>')
def categoria_imagen(id):

    categoria = Categoria.query.get_or_404(id)

    if categoria.imagen:
        return Response(categoria.imagen, mimetype='image/jpeg')

    return "", 404