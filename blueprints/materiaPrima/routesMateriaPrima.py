# routes.py
from flask import render_template, request, redirect, url_for, flash
from models import MateriaPrima, Proveedor, db, Compra, DetalleCompra
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from . import materiaPrima_bp
import forms

@materiaPrima_bp.route('/materiaPrima')
def materiaPrima():
    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = MateriaPrima.query

    # BUSCAR
    if buscar and buscar.strip() != "":
        query = query.filter(
            or_(
                MateriaPrima.nombre.ilike(f"%{buscar}%"),
                MateriaPrima.unidad_medida.ilike(f"%{buscar}%")
            )
        )

    # FILTRAR POR ESTATUS
    if estatus:
        query = query.filter(MateriaPrima.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(MateriaPrima.nombre.asc())
    elif orden == "za":
        query = query.order_by(MateriaPrima.nombre.desc())

    # OBTENER DATOS
    materiaPrima = query.all()

    return render_template(
        "modulo-materiaPrima/modulo-materiaPrima.html",
        materiaPrima=materiaPrima
    )

@materiaPrima_bp.route('/agregarMateriaPrima', methods=['GET', 'POST'])
def agregarMateriaPrima():
    form = forms.MateriaPrimaForm()

  
    proveedores = Proveedor.query.all()
    form.id_proveedor.choices = [(0, 'Seleccione un proveedor')] + [
        (p.id_proveedor, p.nombre) for p in proveedores
    ]

    if form.validate_on_submit():

        metodo_precio = request.form.get('metodo_precio')
        tipo_empaque = request.form.get('tipo_empaque')
        piezas_val = int(request.form.get('piezas_por_caja') or 1)

        contenido_val = float(request.form.get('contenido_por_pieza') or 0)
        unidad_contenido = request.form.get('unidad_contenido')

        precio_input = form.precio_unitario.data
        precio_final = precio_input * piezas_val if metodo_precio == 'pieza' else precio_input

        nueva_materia = MateriaPrima(
            nombre=form.nombre.data.strip(),
            unidad_medida=form.unidad_medida.data,
            tipo_empaque=tipo_empaque,
            piezas_por_caja=piezas_val,
            peso_por_pieza=contenido_val,
            unidad_contenido=unidad_contenido,
            precio_unitario=precio_final,
            id_proveedor=form.id_proveedor.data if form.id_proveedor.data != 0 else None,
            estatus=form.estatus.data
        )

        try:
            db.session.add(nueva_materia)
            db.session.commit()
            flash('Materia prima registrada correctamente', 'success')
            return redirect(url_for('materiaPrima.materiaPrima'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'error')

    return render_template(
        'modulo-materiaPrima/agregarMateriaPrima.html',
        form=form
    )

@materiaPrima_bp.route('/detalleMateriaPrima/<int:id>')
def detalleMateriaPrima(id):
    materia = MateriaPrima.query.get_or_404(id)

    # Cargamos las compras Y sus detalles de forma anticipada
    compras = Compra.query.join(DetalleCompra).filter(
        DetalleCompra.id_materia == id,
        Compra.estado == "recibida"
    ).options(joinedload(Compra.detalles)).order_by(Compra.id_compra.desc()).all()

    return render_template(
        'modulo-materiaPrima/detallesMateriaPrima.html',
        materia=materia,
        compras=compras
    )
    

@materiaPrima_bp.route('/editarMateriaPrima/<int:id>', methods=['GET','POST'])
def modificarMateriaPrima(id):
    materiaPrima = MateriaPrima.query.get_or_404(id)
    form = forms.MateriaPrimaForm(obj=materiaPrima)
    
    # Cargar proveedores
    proveedores = Proveedor.query.all()
    form.id_proveedor.choices = [(0, 'Seleccione un proveedor')] + [(p.id_proveedor, p.nombre) for p in proveedores]
    
    if request.method == 'POST':
        # Forzamos la lectura de datos del form de WTForms
        # Si validate_on_submit() falla, revisa form.errors
        if form.validate_on_submit():
            
            # VALIDAR DUPLICADOS
            existe = MateriaPrima.query.filter(
                MateriaPrima.nombre.ilike(form.nombre.data.strip()),
                MateriaPrima.id_materia != id
            ).first()
            
            if existe:
                flash('Ya existe otra materia prima con este nombre', 'error')
                return render_template('modulo-materiaPrima/modificarMateriaPrima.html', form=form, materiaPrima=materiaPrima)

            try:
                # 🔹 CAMPOS DEL WTFORMS
                materiaPrima.nombre = form.nombre.data.strip()
                materiaPrima.unidad_medida = form.unidad_medida.data
                materiaPrima.precio_unitario = form.precio_unitario.data
                materiaPrima.id_proveedor = form.id_proveedor.data if form.id_proveedor.data != 0 else None
                materiaPrima.estatus = form.estatus.data

                # 🔹 CAMPOS MANUALES (Los que agregamos por bulto/empaque)
                materiaPrima.tipo_empaque = request.form.get('tipo_empaque')
                
                piezas = request.form.get('piezas_por_caja')
                materiaPrima.piezas_por_caja = int(piezas) if piezas and piezas.strip() else None

                contenido = request.form.get('contenido_por_pieza')
                materiaPrima.peso_por_pieza = float(contenido) if contenido and contenido.strip() else None

                materiaPrima.unidad_contenido = request.form.get('unidad_contenido')

                db.session.add(materiaPrima) # Aseguramos que el objeto esté en la sesión
                db.session.commit()
                
                flash('Materia prima actualizada exitosamente', 'success')
                return redirect(url_for('materiaPrima.materiaPrima'))

            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar: {str(e)}', 'error')
        else:
            # Si no valida, imprimimos los errores en consola para saber qué campo falla
            print(form.errors)
            flash('Error en los datos del formulario. Revisa los campos.', 'error')

    # Para GET: Preseleccionar el proveedor actual
    if request.method == 'GET':
        form.id_proveedor.data = materiaPrima.id_proveedor if materiaPrima.id_proveedor else 0

    return render_template(
        'modulo-materiaPrima/modificarMateriaPrima.html',
        form=form,
        materiaPrima=materiaPrima
    )

# DESACTIVAR
@materiaPrima_bp.route('/eliminarMateriaPrima/<int:id>', methods=['GET','POST'])
def eliminarMateriaPrima(id):
    materiaPrima = MateriaPrima.query.get_or_404(id)

    if request.method == 'POST':
        if materiaPrima.estatus == "inactivo":
            flash("Esta materia prima ya está desactivada.", "warning")
            return redirect(url_for('materiaPrima.materiaPrima'))

        materiaPrima.estatus = "inactivo"
        db.session.commit()

        flash("Materia prima desactivada correctamente.", "success")
        return redirect(url_for('materiaPrima.materiaPrima'))

    return render_template(
        'modulo-materiaPrima/eliminarMateriaPrima.html',
        materiaPrima=materiaPrima
    )