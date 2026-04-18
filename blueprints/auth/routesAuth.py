# blueprints/auth/routesAuth.py

from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Usuario, Rol
from forms import LoginForm, RegisterForm
from . import auth_bp
from blueprints.auth.forms import ResetPasswordForm
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from extensions import mail
from flask_mail import Message
import random
from flask_wtf.csrf import CSRFProtect
from blueprints.auth.forms import ResetPasswordForm, NuevaPasswordForm 
from utils.decorators import empleado_required, gerente_or_admin_required,cocina_or_admin_required,vendedor_or_admin_required,login_required_with_message

# ---------------- LOGIN ----------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()

        if usuario and check_password_hash(usuario.password, form.password.data):

            if not usuario.activo:
                flash('Tu cuenta está inactiva.', 'danger')
                return redirect(url_for('auth.login'))

            # generar código de 6 dígitos
            codigo = str(random.randint(100000, 999999))
            usuario.codigo_2fa = codigo
            db.session.commit()

            # guardar id en sesión
            session['2fa_user_id'] = usuario.id_usuario

            # enviar correo
            msg = Message('Código de verificación - Dulce Tradición',
                          recipients=[usuario.email])
            msg.body = f'Tu código de verificación es: {codigo}'
            mail.send(msg)

            flash('Te enviamos un código a tu correo.', 'info')
            return redirect(url_for('auth.verificar_2fa'))

        flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html', form=form)


# ---------------- REGISTER ----------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Ya existe una cuenta con ese correo.', 'warning')
            return redirect(url_for('auth.register'))

        # === BUSCAR ROL CLIENTE ===
        rol_cliente = Rol.query.filter_by(nombre='Cliente').first()

        if not rol_cliente:
            flash('Error interno: Rol "Cliente" no encontrado.', 'danger')
            return redirect(url_for('auth.register'))

        # Crear el Usuario
        nuevo_usuario = Usuario(
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            id_rol=rol_cliente.id_rol,
            activo=True
        )

        db.session.add(nuevo_usuario)
        db.session.flush()   # Para obtener el id_usuario generado

        # Crear el perfil de Cliente
        nuevo_cliente = Cliente(
            id_usuario=nuevo_usuario.id_usuario,
            nombre=form.nombre.data,
            telefono=None,      # Puedes agregar campo en el form después
            direccion=None,
            estatus='activo'
        )

        db.session.add(nuevo_cliente)
        db.session.commit()

        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


# ---------------- LOGOUT ----------------
@auth_bp.route('/logout')
@login_required
def logout():
    nombre = current_user.nombre_mostrable
    logout_user()

    flash(f"Sesión cerrada correctamente: {nombre}", "success")
    return redirect(url_for('home'))


# ---------------- 2FA ----------------
@auth_bp.route('/verificar-2fa', methods=['GET', 'POST'])
def verificar_2fa():

    if '2fa_user_id' not in session:
        return redirect(url_for('auth.login'))

    user = Usuario.query.get(session['2fa_user_id'])

    if request.method == 'POST':
        codigo = request.form.get('codigo')

        if codigo == user.codigo_2fa:
            login_user(user)

            # limpiar código y sesión
            user.codigo_2fa = None
            db.session.commit()
            session.pop('2fa_user_id', None)

            return redirect(url_for('gestion'))
        else:
            flash('Código incorrecto', 'danger')

    return render_template('auth/verificar_2fa.html')


# ---------------- RESET PASSWORD ----------------


@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset():
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()

        if user:
            # generar código
            codigo = str(random.randint(100000, 999999))
            user.codigo_recuperacion = codigo
            db.session.commit()

            # guardar usuario en sesión
            session['reset_user_id'] = user.id_usuario

            # enviar correo
            msg = Message('Recuperación de contraseña',
                          recipients=[user.email])
            msg.body = f'Tu código para recuperar contraseña es: {codigo}'
            mail.send(msg)

            flash('Te enviamos un código a tu correo.', 'info')
            return redirect(url_for('auth.verificar_codigo_reset'))

        flash('Correo no registrado.', 'warning')

    return render_template('auth/reset.html', form=form)

@auth_bp.route('/verificar-reset', methods=['GET', 'POST'])
def verificar_codigo_reset():

    if 'reset_user_id' not in session:
        return redirect(url_for('auth.reset'))

    user = Usuario.query.get(session['reset_user_id'])

    if request.method == 'POST':
        codigo = request.form.get('codigo')

        if codigo == user.codigo_recuperacion:
            return redirect(url_for('auth.nueva_password'))
        else:
            flash('Código incorrecto', 'danger')

    return render_template('auth/verificar_reset.html')

@auth_bp.route('/nueva-password', methods=['GET', 'POST'])
def nueva_password():
    if 'reset_user_id' not in session:
        return redirect(url_for('auth.reset'))

    user = Usuario.query.get(session['reset_user_id'])
    form = NuevaPasswordForm()  # Usa el formulario

    if form.validate_on_submit():  # Esto valida CSRF automáticamente
        user.password = generate_password_hash(form.password.data)
        user.codigo_recuperacion = None
        db.session.commit()
        session.pop('reset_user_id', None)
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/nuevo_password.html', form=form)