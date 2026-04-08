from flask import render_template, request, redirect, url_for, flash, Response
from models import Producto, Categoria, db, Receta, InventarioProducto, Sucursal, MovimientoInventarioProducto
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import os
from . import productos_bp

import forms
import base64


@productos_bp.app_template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ""

# LISTAR PRODUCTOS
@productos_bp.route('/productos')
def productos():

    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = Producto.query

    if buscar and buscar.strip() != "":
        query = query.filter(
            Producto.nombre.ilike(f"%{buscar}%")
        )

    if estatus:
        query = query.filter(Producto.estatus == estatus)

    if orden == "az":
        query = query.order_by(Producto.nombre.asc())
    elif orden == "za":
        query = query.order_by(Producto.nombre.desc())

    productos = query.all()

    cambios = False

    for p in productos:

        if p.receta:
            total = 0
            rendimiento = p.receta.rendimiento_piezas or 1

            for d in p.receta.ingredientes:
                materia = d.materia
                tipo = (d.tipo or '').lower().strip()
                cantidad = float(d.cantidad)

                if tipo in ['gr', 'gramos']:
                    tipo = 'g'
                elif tipo in ['pieza', 'pza']:
                    tipo = 'pz'

                if tipo in ['g', 'kg', 'ml', 'l']:
                    costo_unitario = materia.precio_por_gramo_ml
                    if tipo in ['kg', 'l']:
                        cantidad *= 1000

                elif tipo == 'pz':
                    costo_unitario = materia.precio_por_pieza
                else:
                    costo_unitario = float(materia.precio_unitario)

                total += cantidad * costo_unitario

            costo = round(total / rendimiento, 2) if rendimiento > 0 else 0

            if p.costo_unitario_estimado != costo:
                p.costo_unitario_estimado = costo
                cambios = True

            nuevo_precio = round(costo * 1.6, 2)

            if p.precio_venta != nuevo_precio:
                p.precio_venta = nuevo_precio
                cambios = True

    if cambios:
        db.session.commit()

    return render_template(
        "modulo-productos/modulo-productos.html",
        productos=productos
    )

# AGREGAR PRODUCTO - CON VALIDACIÓN DE DUPLICADO
@productos_bp.route('/agregarProducto', methods=['GET','POST'])
def agregarProducto():

    form = forms.ProductoForm()

    categorias = Categoria.query.all()
    form.id_categoria.choices = [(c.id_categoria, c.nombre) for c in categorias]

    if form.validate_on_submit():
        producto_existente = Producto.query.filter_by(
            nombre=form.nombre.data
        ).first()

        if producto_existente:
            flash(f"Ya existe un producto con el nombre '{form.nombre.data}'.", "danger")
            return render_template(
                'modulo-productos/agregarProducto.html',
                form=form
            )

        imagen = request.files.get("imagen")

        imagen_bytes = None

        if imagen and imagen.filename != "":
            imagen_bytes = imagen.read()

        nuevo_producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            id_categoria=form.id_categoria.data,
            precio_venta=form.precio_venta.data,
            costo_unitario_estimado=form.costo_unitario_estimado.data,
            imagen_url=imagen_bytes,
            dias_caducidad=form.dias_caducidad.data,
            estatus=form.estatus.data
        )

        db.session.add(nuevo_producto)
        db.session.commit()

        flash("Producto agregado correctamente", "success")

        return redirect(url_for('productos.productos'))

    return render_template(
        'modulo-productos/agregarProducto.html',
        form=form
    )

# EDITAR PRODUCTO - CON VALIDACIÓN DE DUPLICADO (excluyendo el producto actual)
@productos_bp.route('/editarProducto/<int:id>', methods=['GET','POST'])
def modificarProducto(id):

    producto = Producto.query.get_or_404(id)

    form = forms.ProductoForm(obj=producto)

    categorias = Categoria.query.all()
    form.id_categoria.choices = [(c.id_categoria, c.nombre) for c in categorias]

    if form.validate_on_submit():

       
        producto_existente = Producto.query.filter(
            Producto.nombre == form.nombre.data,
            Producto.id_producto != id  # Excluir el producto actual
        ).first()
        
        if producto_existente:
            flash(f"Ya existe otro producto con el nombre '{form.nombre.data}'.", "danger")
            return render_template(
                'modulo-productos/modificarProducto.html',
                form=form,
                producto=producto
            )

        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.id_categoria = form.id_categoria.data
        producto.precio_venta = form.precio_venta.data
        producto.costo_unitario_estimado = form.costo_unitario_estimado.data
        producto.dias_caducidad = form.dias_caducidad.data
        producto.estatus = form.estatus.data

        # Obtener imagen nueva si el usuario sube una
        imagen = request.files.get("imagen")

        if imagen and imagen.filename != "":
            producto.imagen_url = imagen.read()

        db.session.commit()

        flash("Producto actualizado correctamente", "success")

        return redirect(url_for('productos.productos'))

    return render_template(
        'modulo-productos/modificarProducto.html',
        form=form,
        producto=producto
    )

# DESACTIVAR PRODUCTO
@productos_bp.route('/eliminarProducto/<int:id>', methods=['GET','POST'])
def eliminarProducto(id):

    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':

        if producto.estatus == "inactivo":
            flash("Este producto ya está desactivado.", "warning")
            return redirect(url_for('productos.productos'))

        producto.estatus = "inactivo"

        db.session.commit()

        flash("Producto desactivado correctamente.", "success")

        return redirect(url_for('productos.productos'))

    return render_template(
        'modulo-productos/eliminarProducto.html',
        producto=producto
    )


@productos_bp.route('/detalleProducto/<int:id>')
def detalleProducto(id):

    producto = Producto.query.get_or_404(id)

    receta = Receta.query.filter_by(
        id_producto=id
    ).first()

    return render_template(
        'modulo-productos/detallesProducto.html',
        producto=producto,
        receta=receta
    )

# MOSTRAR IMAGEN DEL PRODUCTO
@productos_bp.route('/producto_imagen/<int:id>')
def producto_imagen(id):
    producto = Producto.query.get_or_404(id)
    
    if producto.imagen_url:
        return Response(producto.imagen_url, mimetype='image/jpeg')
    
    # Imagen por defecto si no hay imagen
    return "", 404

@productos_bp.route('/inventario')
def verInventario():
    buscar = request.args.get("buscar")
    id_sucursal = request.args.get("sucursal", type=int)
    
    query = InventarioProducto.query
    
    # Filtrar por sucursal
    if id_sucursal:
        query = query.filter_by(id_sucursal=id_sucursal)
    
    # Buscar por nombre de producto
    if buscar:
        query = query.join(Producto).filter(
            Producto.nombre.ilike(f"%{buscar}%")
        )
    
    inventarios = query.all()
    sucursales = Sucursal.query.filter_by(estatus='activo').all()
    
    return render_template(
        'inventarioProducto/inventarioProducto.html',
        inventarios=inventarios,
        sucursales=sucursales,
        sucursal_seleccionada=id_sucursal
    )

@productos_bp.route('/historialInventario/<int:id_producto>/<int:id_sucursal>')
def historialInventario(id_producto, id_sucursal):
   
    movimientos = MovimientoInventarioProducto.query.filter_by(
        id_producto=id_producto,
        id_sucursal=id_sucursal
    ).order_by(MovimientoInventarioProducto.fecha.desc()).all()
    
    producto = Producto.query.get_or_404(id_producto)
    sucursal = Sucursal.query.get_or_404(id_sucursal)
    
    return render_template(
        'inventarioProducto/historial.html',
        movimientos=movimientos,
        producto=producto,
        sucursal=sucursal
    )
    
@productos_bp.route('/ajustar_stock/<int:id_inventario>', methods=['GET', 'POST'])
def ajustarStock(id_inventario):
    inventario = InventarioProducto.query.get_or_404(id_inventario)
    
    if request.method == 'POST':
        cantidad = int(request.form.get('cantidad', 0))
        tipo = request.form.get('tipo')
        
        if tipo == 'agregar':
            inventario.stock_actual += cantidad
            mensaje = f"Se agregaron {cantidad} unidades"
        elif tipo == 'quitar':
            if inventario.stock_actual >= cantidad:
                inventario.stock_actual -= cantidad
                mensaje = f"Se quitaron {cantidad} unidades"
            else:
                flash('No hay suficiente stock', 'error')
                return redirect(url_for('productos.verInventario'))
        
        # Registrar movimiento
        
        movimiento = MovimientoInventarioProducto(
            id_producto=inventario.id_producto,
            id_sucursal=inventario.id_sucursal,
            cantidad=cantidad,
            tipo='ajuste_manual',
            referencia=f'Ajuste manual por usuario'
        )
        db.session.add(movimiento)
        db.session.commit()
        
        flash(mensaje, 'success')
        return redirect(url_for('productos.verInventario'))
    
    return render_template('inventarioProducto/ajustar_stock.html', inventario=inventario)

