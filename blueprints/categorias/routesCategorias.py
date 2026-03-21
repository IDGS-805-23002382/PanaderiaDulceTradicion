from flask import render_template, request, redirect, url_for, flash, Response
from models import Categoria, db
from sqlalchemy import or_
from . import categorias_bp
import forms


# =========================
# LISTAR / FILTRAR
# =========================
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


# =========================
# AGREGAR
# =========================
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
            imagen=imagen_binaria,   # 👈 NUEVO
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


# =========================
# DETALLE
# =========================
@categorias_bp.route('/detalleCategoria/<int:id>')
def detallesCategoria(id):

    categoria = Categoria.query.get_or_404(id)

    return render_template(
        'modulo-categorias/detallesCategoria.html',
        categoria=categoria
    )


# =========================
# EDITAR
# =========================
@categorias_bp.route('/editarCategoria/<int:id>', methods=['GET','POST'])
def modificarCategoria(id):

    categoria = Categoria.query.get_or_404(id)

    form = forms.CategoriaForm(obj=categoria)

    if form.validate_on_submit():

        archivo = request.files.get("imagen")

        # SOLO actualizar si sube nueva imagen
        if archivo and archivo.filename != "":
            categoria.imagen = archivo.read()

        categoria.nombre = form.nombre.data
        categoria.descripcion = form.descripcion.data
        categoria.estatus = form.estatus.data

        db.session.commit()

        flash("Categoría actualizada correctamente", "success")

        return redirect(url_for('categorias.categorias'))

    return render_template(
        'modulo-categorias/modificarCategoria.html',
        form=form,
        categoria=categoria
    )


# =========================
# ELIMINAR (SOFT DELETE)
# =========================
@categorias_bp.route('/eliminarCategoria/<int:id>', methods=['GET','POST'])
def eliminarCategoria(id):

    categoria = Categoria.query.get_or_404(id)

    if request.method == 'POST':

        if categoria.estatus == "inactivo":
            flash("Esta categoría ya está desactivada.", "warning")
            return redirect(url_for('categorias.categorias'))

        categoria.estatus = "inactivo"
        db.session.commit()

        flash("Categoría desactivada correctamente.", "success")
        return redirect(url_for('categorias.categorias'))

    return render_template(
        'modulo-categorias/eliminarCategoria.html',
        categoria=categoria
    )


# =========================
# MOSTRAR IMAGEN
# =========================
@categorias_bp.route('/categoria_imagen/<int:id>')
def categoria_imagen(id):

    categoria = Categoria.query.get_or_404(id)

    if categoria.imagen:
        return Response(categoria.imagen, mimetype='image/jpeg')

    return "", 404