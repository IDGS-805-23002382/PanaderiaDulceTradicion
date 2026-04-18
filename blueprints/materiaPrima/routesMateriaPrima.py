from flask import render_template, request, redirect, url_for, flash
from sqlalchemy import or_, func
from . import materiaPrima_bp
from models import MateriaPrima, Proveedor, db, Bitacora
import forms
import datetime
import os
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message
from flask_login import login_required

@materiaPrima_bp.route('/backup', methods=['POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def backup_db():
    try:
        fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"backup_{fecha}.sql"

        ruta = os.path.join("backups", nombre_archivo)

        # Crear carpeta si no existe
        os.makedirs("backups", exist_ok=True)

        # Comando mysqldump
        comando = f"mysqldump -u root -proot panaderia_db4 > {ruta}"
        os.system(comando)

        flash(f"Backup creado correctamente: {nombre_archivo}", "success")

    except Exception as e:
        flash(f"Error al generar backup: {str(e)}", "error")

    return redirect(url_for('materiaPrima.materiaPrima'))

# BITÁCORA / LOG
def registrar_log(accion, tabla, descripcion, usuario_nombre="sistema"):
    try:
        ip_usuario = None
        try:
            ip_usuario = request.remote_addr
        except:
            pass
        
        log = Bitacora(
            accion=accion,
            tabla=tabla,
            descripcion=descripcion,
            fecha_hora=datetime.datetime.now(),
            usuario_nombre=usuario_nombre,  # ← CORRECTO: usuario_nombre, no usuario
            usuario_id=None,
            ip_usuario=ip_usuario
        )
        
        db.session.add(log)
        db.session.commit()
        print(f"✅ Log creado: {accion} - {tabla}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al crear log: {str(e)}")


# LISTADO
@materiaPrima_bp.route('/materiaPrima')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def materiaPrima():
    buscar = request.args.get("buscar")
    estatus = request.args.get("estatus")
    orden = request.args.get("orden")

    query = MateriaPrima.query

    # BUSCAR
    if buscar and buscar.strip():
        query = query.filter(
            or_(
                MateriaPrima.nombre.ilike(f"%{buscar}%"),
                MateriaPrima.unidad_base.ilike(f"%{buscar}%")
            )
        )

    # FILTRAR ESTATUS
    if estatus:
        query = query.filter(MateriaPrima.estatus == estatus)

    # ORDENAR
    if orden == "az":
        query = query.order_by(MateriaPrima.nombre.asc())
    elif orden == "za":
        query = query.order_by(MateriaPrima.nombre.desc())

    materias = query.all()

    return render_template(
        "modulo-materiaPrima/modulo-materiaPrima.html",
        materiaPrima=materias
    )



# AGREGAR
@materiaPrima_bp.route('/agregarMateriaPrima', methods=['GET', 'POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def agregarMateriaPrima():
    form = forms.MateriaPrimaForm()

    # 🔹 PROVEEDORES
    proveedores = Proveedor.query.all()
    form.id_proveedor.choices = [(0, 'Seleccione un proveedor')] + [
        (p.id_proveedor, p.nombre) for p in proveedores
    ]

    if form.validate_on_submit():
        try:
            nombre = form.nombre.data.strip()

            #  VALIDAR DUPLICADO
            existe = MateriaPrima.query.filter(
                func.lower(MateriaPrima.nombre) == nombre.lower()
            ).first()

            if existe:
                flash("Ya existe esta materia prima", "error")
                return render_template(
                    'modulo-materiaPrima/agregarMateriaPrima.html',
                    form=form
                )

            nueva = MateriaPrima(
                nombre=nombre,
                unidad_base=form.unidad_base.data,
                id_proveedor=form.id_proveedor.data if form.id_proveedor.data != 0 else None,
                estatus=form.estatus.data
            )

            db.session.add(nueva)

            # LOG
            registrar_log(
                accion="INSERT",
                tabla="materias_primas",
                descripcion=f"Se registró materia prima: {nombre}"
            )

            db.session.commit()

            flash("Materia prima registrada correctamente", "success")
            return redirect(url_for('materiaPrima.materiaPrima'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")

    return render_template(
        'modulo-materiaPrima/agregarMateriaPrima.html',
        form=form
    )



# DETALLE

@materiaPrima_bp.route('/detalleMateriaPrima/<int:id>')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def detalleMateriaPrima(id):
    materia = MateriaPrima.query.get_or_404(id)

    return render_template(
        'modulo-materiaPrima/detallesMateriaPrima.html',
        materia=materia
    )


#  EDITAR (AUDITORÍA)
@materiaPrima_bp.route('/editarMateriaPrima/<int:id>', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
def modificarMateriaPrima(id):
    materia = MateriaPrima.query.get_or_404(id)
    form = forms.MateriaPrimaForm(obj=materia)

    proveedores = Proveedor.query.all()
    form.id_proveedor.choices = [(0, 'Seleccione un proveedor')] + [
        (p.id_proveedor, p.nombre) for p in proveedores
    ]

    if form.validate_on_submit():
        try:
            cambios = []

            nombre_nuevo = form.nombre.data.strip()

            # VALIDAR DUPLICADO SI CAMBIA
            if materia.nombre.lower() != nombre_nuevo.lower():
                existe = MateriaPrima.query.filter(
                    func.lower(MateriaPrima.nombre) == nombre_nuevo.lower(),
                    MateriaPrima.id_materia != materia.id_materia
                ).first()

                if existe:
                    flash("Ya existe otra materia prima con ese nombre", "error")
                    return render_template(
                        'modulo-materiaPrima/modificarMateriaPrima.html',
                        form=form,
                        materiaPrima=materia
                    )

                cambios.append(f"Nombre: {materia.nombre} → {nombre_nuevo}")
                materia.nombre = nombre_nuevo

            # UNIDAD
            if materia.unidad_base != form.unidad_base.data:
                cambios.append(f"Unidad: {materia.unidad_base} → {form.unidad_base.data}")
                materia.unidad_base = form.unidad_base.data

            # ESTATUS
            if materia.estatus != form.estatus.data:
                cambios.append(f"Estatus: {materia.estatus} → {form.estatus.data}")
                materia.estatus = form.estatus.data

            # PROVEEDOR
            materia.id_proveedor = form.id_proveedor.data if form.id_proveedor.data != 0 else None

            # AUDITORÍA
            if cambios:
                registrar_log(
                    accion="UPDATE",
                    tabla="materias_primas",
                    descripcion=f"Cambios en {materia.nombre}: {', '.join(cambios)}"
                )

            db.session.commit()

            flash("Materia prima actualizada correctamente", "success")
            return redirect(url_for('materiaPrima.materiaPrima'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")

    # PARA GET
    if request.method == 'GET':
        form.id_proveedor.data = materia.id_proveedor if materia.id_proveedor else 0

    return render_template(
        'modulo-materiaPrima/modificarMateriaPrima.html',
        form=form,
        materiaPrima=materia
    )


#  DESACTIVAR (SOFT DELETE)
@materiaPrima_bp.route('/eliminarMateriaPrima/<int:id>', methods=['GET','POST'])
@login_required
@login_required_with_message
@gerente_or_admin_required
def eliminarMateriaPrima(id):
    materia = MateriaPrima.query.get_or_404(id)

    if request.method == 'POST':

        if materia.estatus == "inactivo":
            flash("Esta materia prima ya está desactivada", "warning")
            return redirect(url_for('materiaPrima.materiaPrima'))

        materia.estatus = "inactivo"

        registrar_log(
            accion="DELETE",
            tabla="materias_primas",
            descripcion=f"Se desactivó materia prima: {materia.nombre}"
        )

        db.session.commit()

        flash("Materia prima desactivada correctamente", "success")
        return redirect(url_for('materiaPrima.materiaPrima'))

    # ESTE ES EL GET (muestra la vista bonita)
    return render_template(
        'modulo-materiaPrima/eliminarMateriaPrima.html',
        materiaPrima=materia
    )

@materiaPrima_bp.route('/tabla-conversiones')
@login_required
@login_required_with_message
@gerente_or_admin_required
@empleado_required
def tablaConversiones():
    from models import InventarioMateriaPrima
    
    valor_original = request.args.get('valor', type=float)
    unidad_origen = request.args.get('from_unit', 'kg')
    unidad_destino = request.args.get('to_unit', 'g')
    resultado_conversion = None
    error_conversion = None
    
    if valor_original is not None:
        try:
            # Conversiones de masa
            conversiones_masa = {
                ('kg', 'g'): valor_original * 1000,
                ('g', 'kg'): valor_original / 1000,
                ('kg', 'mg'): valor_original * 1000000,
                ('mg', 'kg'): valor_original / 1000000,
                ('g', 'mg'): valor_original * 1000,
                ('mg', 'g'): valor_original / 1000,
            }
            
            # Conversiones de volumen
            conversiones_volumen = {
                ('l', 'ml'): valor_original * 1000,
                ('ml', 'l'): valor_original / 1000,
            }
            
            key = (unidad_origen, unidad_destino)
            if key in conversiones_masa:
                resultado_conversion = conversiones_masa[key]
            elif key in conversiones_volumen:
                resultado_conversion = conversiones_volumen[key]
            else:
                error_conversion = f"No se puede convertir de {unidad_origen} a {unidad_destino}"
        except Exception as e:
            error_conversion = str(e)
    
    # Obtener materias primas del inventario para mostrar conversiones
    inventario = InventarioMateriaPrima.query.all()
    materia_prima_conversiones = []
    
    for item in inventario:
        unidad_base = item.materia.unidad_base
        stock = item.stock_actual
        
        if unidad_base == 'g':
            materia_prima_conversiones.append({
                'nombre': item.materia.nombre,
                'stock_kg': round(stock / 1000, 2),
                'stock_g': round(stock, 2),
                'unidad_grande': 'kg',
                'unidad_pequena': 'g',
                'factor': 1000,
                'badge_class': 'badge-mass'
            })
        elif unidad_base == 'kg':
            materia_prima_conversiones.append({
                'nombre': item.materia.nombre,
                'stock_kg': round(stock, 2),
                'stock_g': round(stock * 1000, 2),
                'unidad_grande': 'kg',
                'unidad_pequena': 'g',
                'factor': 1000,
                'badge_class': 'badge-mass'
            })
        elif unidad_base == 'ml':
            materia_prima_conversiones.append({
                'nombre': item.materia.nombre,
                'stock_kg': round(stock / 1000, 2),
                'stock_g': round(stock, 2),
                'unidad_grande': 'L',
                'unidad_pequena': 'mL',
                'factor': 1000,
                'badge_class': 'badge-volume'
            })
        elif unidad_base == 'l':
            materia_prima_conversiones.append({
                'nombre': item.materia.nombre,
                'stock_kg': round(stock, 2),
                'stock_g': round(stock * 1000, 2),
                'unidad_grande': 'L',
                'unidad_pequena': 'mL',
                'factor': 1000,
                'badge_class': 'badge-volume'
            })
    
    return render_template(
        'modulo-materiaPrima/tablaConversiones.html',
        valor_original=valor_original,
        unidad_origen=unidad_origen,
        unidad_destino=unidad_destino,
        resultado_conversion=resultado_conversion,
        error_conversion=error_conversion,
        materia_prima_conversiones=materia_prima_conversiones
    )