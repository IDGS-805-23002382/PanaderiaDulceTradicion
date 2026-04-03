from flask import render_template, request, redirect, url_for, flash
from models import Receta, Producto, DetalleReceta, MateriaPrima, db, DetalleReceta
from sqlalchemy import or_

from . import recetas_bp
import forms


# LISTAR RECETAS
@recetas_bp.route('/recetas')
def recetas():

    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Receta.query

    # BUSCAR
    if buscar and buscar.strip() != "":
        query = query.filter(
            Receta.nombre.ilike(f"%{buscar}%")
        )

    # FILTRAR POR ESTATUS
    if estatus:
        query = query.filter(Receta.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(Receta.nombre.asc())

    elif orden == "za":
        query = query.order_by(Receta.nombre.desc())

    recetas = query.all()

    return render_template(
        "modulo-recetas/modulo-recetas.html",
        recetas=recetas
    )


# AGREGAR RECETA
@recetas_bp.route('/agregarReceta', methods=['GET','POST'])
def agregarReceta():

    form = forms.RecetaForm()

    productos = Producto.query.all()
    materias = MateriaPrima.query.all()

    form.id_producto.choices = [(p.id_producto, p.nombre) for p in productos]

    if form.validate_on_submit():
        receta_existente = Receta.query.filter_by(
            id_producto=form.id_producto.data
        ).first()

        if receta_existente:
            flash("Este producto ya tiene una receta.", "warning")
            return redirect(url_for('recetas.agregarReceta'))

        # 🔹 CREAR RECETA
        nueva_receta = Receta(
            id_producto=form.id_producto.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            rendimiento_piezas=form.rendimiento_piezas.data,
            estatus=form.estatus.data
        )

        db.session.add(nueva_receta)
        db.session.flush()  

        # 🔹 INGREDIENTES DESDE EL FORM
        materias_ids = request.form.getlist('materia[]')
        cantidades = request.form.getlist('cantidad[]')

        for i in range(len(materias_ids)):

            if cantidades[i] == "":
                continue

            existe = DetalleReceta.query.filter_by(
                id_receta=nueva_receta.id_receta,
                id_materia=materias_ids[i]
            ).first()

            if existe:
                continue

            detalle = DetalleReceta(
                id_receta=nueva_receta.id_receta,
                id_materia=materias_ids[i],
                cantidad=cantidades[i]   
            )

            db.session.add(detalle)

        db.session.commit()

        flash("Receta agregada correctamente con ingredientes", "success")

        return redirect(url_for('recetas.recetas'))

    return render_template(
        'modulo-recetas/agregarReceta.html',
        form=form,
        materias=materias  
    )

# DETALLE RECETA (MATERIAS PRIMAS)
@recetas_bp.route('/detalleReceta/<int:id>')
def detalleReceta(id):

    receta = Receta.query.get_or_404(id)

    ingredientes = DetalleReceta.query.filter_by(
        id_receta=id
    ).all()

    return render_template(
        'modulo-recetas/detalleReceta.html',
        receta=receta,
        ingredientes=ingredientes
    )


# EDITAR RECETA
@recetas_bp.route('/editarReceta/<int:id>', methods=['GET','POST'])
def modificarReceta(id):
    receta = Receta.query.get_or_404(id)
    form = forms.RecetaForm(obj=receta)

    # Cargar catálogos
    productos = Producto.query.all()
    materias = MateriaPrima.query.all()
    
    form.id_producto.choices = [(p.id_producto, p.nombre) for p in productos]

    # Obtener los ingredientes actuales
    ingredientes_actuales = DetalleReceta.query.filter_by(id_receta=id).all()

    if form.validate_on_submit():
        # Actualizar datos básicos de la receta
        receta.id_producto = form.id_producto.data
        receta.nombre = form.nombre.data
        receta.descripcion = form.descripcion.data
        receta.rendimiento_piezas = form.rendimiento_piezas.data
        receta.estatus = form.estatus.data

        # --- GESTIÓN DE INGREDIENTES ---
        # 1. Limpiar detalles anteriores
        DetalleReceta.query.filter_by(id_receta=id).delete()

        # 2. Capturar listas del formulario (incluyendo el nuevo tipo)
        materias_ids = request.form.getlist('materia[]')
        cantidades = request.form.getlist('cantidad[]')
        tipos_unidades = request.form.getlist('tipo[]') # Captura el select manual

        for i in range(len(materias_ids)):
            id_mat = materias_ids[i]
            
            # Validamos que se haya seleccionado una materia y que haya cantidad
            if id_mat and cantidades[i]:
                try:
                    cant_val = float(cantidades[i])
                    if cant_val > 0:
                        nuevo_detalle = DetalleReceta(
                            id_receta=receta.id_receta,
                            id_materia=id_mat,
                            cantidad=cant_val,
                            tipo=tipos_unidades[i] # Guardamos la unidad elegida (g, kg, ml, etc)
                        )
                        db.session.add(nuevo_detalle)
                except ValueError:
                    continue

        try:
            db.session.commit()
            flash("Receta e ingredientes actualizados correctamente", "success")
            return redirect(url_for('recetas.recetas'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al guardar: {str(e)}", "danger")

    return render_template(
        'modulo-recetas/modificarReceta.html',
        form=form,
        receta=receta,
        materias=materias,
        ingredientes_actuales=ingredientes_actuales
    )


# DESACTIVAR RECETA
@recetas_bp.route('/eliminarReceta/<int:id>', methods=['GET','POST'])
def eliminarReceta(id):

    receta = Receta.query.get_or_404(id)

    if request.method == 'POST':

        if receta.estatus == "inactivo":
            flash("Esta receta ya está desactivada.", "warning")
            return redirect(url_for('recetas.recetas'))

        receta.estatus = "inactivo"

        db.session.commit()

        flash("Receta desactivada correctamente.", "success")

        return redirect(url_for('recetas.recetas'))

    return render_template(
        'modulo-recetas/eliminarReceta.html',
        receta=receta
    )