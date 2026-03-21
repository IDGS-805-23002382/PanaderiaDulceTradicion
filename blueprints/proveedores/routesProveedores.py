from flask import Flask, render_template, request, redirect, url_for, flash
from models import Proveedor, db, MateriaPrima, Compra, DetalleCompra
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from . import proveedores_bp
<<<<<<< HEAD
from datetime import datetime
=======
>>>>>>> d9c95103a59bb805666d341ce56430d8b2ad02cd
import forms


@proveedores_bp.route('/proveedores')
def proveedores():

    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Proveedor.query

    # BUSCAR
    if buscar and buscar.strip() != "":
        query = query.filter(
            or_(
                Proveedor.nombre.ilike(f"%{buscar}%"),
                Proveedor.telefono.ilike(f"%{buscar}%"),
                Proveedor.email.ilike(f"%{buscar}%"),
                Proveedor.contacto.ilike(f"%{buscar}%")
            )
        )

    # FILTRAR POR ESTATUS
    if estatus:
        query = query.filter(Proveedor.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(Proveedor.nombre.asc())

    elif orden == "za":
        query = query.order_by(Proveedor.nombre.desc())

    proveedores = query.all()

    return render_template(
        "modulo-proveedores/modulo-proveedores.html",
        proveedores=proveedores
    )
    
# Agregar
@proveedores_bp.route('/registrarProveedores', methods=['GET','POST'])
def agregarProveedores():

    form = forms.ProveedorForm()

    if form.validate_on_submit():

        nuevo_proveedor = Proveedor(
            nombre=form.nombre.data,
            telefono=form.telefono.data,
            email=form.email.data,
            direccion=form.direccion.data,
            contacto=form.contacto.data,
            notas=form.notas.data,
            estatus=form.estatus.data
        )

        db.session.add(nuevo_proveedor)
        db.session.commit()

        return redirect(url_for('proveedores.proveedores'))

    return render_template(
        'modulo-proveedores/agregarProveedores.html',
        form=form
    )
    
@proveedores_bp.route('/detalleProveedor/<int:id>')
def detallesProveedor(id):

    proveedor = Proveedor.query.get_or_404(id)

    return render_template(
        'modulo-proveedores/detallesProveedor.html',
        proveedor=proveedor
    )

@proveedores_bp.route('/editarProveedor/<int:id>', methods=['GET','POST'])
def modificarProveedor(id):

    proveedor = Proveedor.query.get_or_404(id)

    form = forms.ProveedorForm(obj=proveedor)

    if form.validate_on_submit():

        proveedor.nombre = form.nombre.data
        proveedor.telefono = form.telefono.data
        proveedor.email = form.email.data
        proveedor.direccion = form.direccion.data
        proveedor.contacto = form.contacto.data
        proveedor.notas = form.notas.data
        proveedor.estatus = form.estatus.data

        db.session.commit()

        return redirect(url_for('proveedores.proveedores'))

    return render_template(
        'modulo-proveedores/modificarProveedor.html',
        form=form,
        proveedor=proveedor
    )
    
@proveedores_bp.route('/eliminarProveedor/<int:id>', methods=['GET','POST'])
def eliminarProveedor(id):

    proveedor = Proveedor.query.get_or_404(id)

    if request.method == 'POST':

        # validar si ya esta inactivo
        if proveedor.estatus == "inactivo":
            flash("Este proveedor ya está desactivado.", "warning")
            return redirect(url_for('proveedores.proveedores'))

        proveedor.estatus = "inactivo"
        db.session.commit()

        flash("Proveedor desactivado correctamente.", "success")
        return redirect(url_for('proveedores.proveedores'))

    return render_template(
        'modulo-proveedores/eliminarProveedor.html',
        proveedor=proveedor
    )
    
@proveedores_bp.route("/compras", methods=["GET", "POST"])
def compraProveedores():

    proveedores = Proveedor.query.filter_by(estatus="activo").all()
    materias = MateriaPrima.query.filter_by(estatus="activo").all()

    # 👉 número de filas dinámicas (por defecto 1)
    filas = int(request.args.get("filas", 1))

    if request.method == "POST":

        id_proveedor = request.form.get("proveedor")

        compra = Compra(id_proveedor=id_proveedor)
        db.session.add(compra)
        db.session.flush()

        total = 0

        for i in range(filas):

            materia_id = request.form.get(f"materia_id_{i}")
            cantidad = request.form.get(f"cantidad_{i}")
            precio = request.form.get(f"precio_{i}")

            # validar vacío
            if not materia_id or not cantidad or not precio:
                continue

            materia = MateriaPrima.query.get(materia_id)

            cantidad = int(cantidad)
            precio = float(precio)

            subtotal = cantidad * precio
            total += subtotal

            detalle = DetalleCompra(
                id_compra=compra.id_compra,
                id_materia=materia.id_materia,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=subtotal
            )

            materia.stock_actual += cantidad
            materia.fecha_ultima_compra = datetime.utcnow()

            db.session.add(detalle)

        compra.total = total
        db.session.commit()

        return redirect(url_for("proveedores.compraProveedores"))

    return render_template(
        "modulo-proveedores/compraProveedores.html",
        proveedores=proveedores,
        materias=materias,
        filas=filas 
    )