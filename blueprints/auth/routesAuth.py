# blueprints/auth/routesAuth.py

from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Usuario, Rol, Cliente   # ← Importante
from forms import LoginForm, RegisterForm
from . import auth_bp


# ---------------- LOGIN ----------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()

        print("=== DEBUG LOGIN ===")
        print("Email ingresado:", form.email.data)
        if usuario:
            print("Usuario encontrado - ID:", usuario.id_usuario)
            print("Hash guardado:", repr(usuario.password))
            print("Longitud del hash:", len(usuario.password) if usuario.password else 0)
        else:
            print("Usuario NO encontrado")

        if usuario and usuario.password and check_password_hash(usuario.password, form.password.data):
            # ... resto del código normal (2FA)
            if not usuario.activo:
                flash('Tu cuenta está inactiva.', 'danger')
                return redirect(url_for('auth.login'))

            codigo = str(random.randint(100000, 999999))
            usuario.codigo_2fa = codigo
            db.session.commit()

            session['2fa_user_id'] = usuario.id_usuario

            msg = Message('Código de verificación - Dulce Tradición', recipients=[usuario.email])
            msg.body = f'Tu código de verificación es: {codigo}'
            mail.send(msg)

            flash('Te enviamos un código a tu correo.', 'info')
            return redirect(url_for('auth.verificar_2fa'))

        flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html', form=form)


# ---------------- REGISTER (como Cliente) ----------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Ya existe una cuenta con ese correo.', 'warning')
            return redirect(url_for('auth.register'))

        rol_cliente = Rol.query.filter_by(nombre='Cliente').first()
        if not rol_cliente:
            flash('Error: No existe el rol Cliente.', 'danger')
            return redirect(url_for('auth.register'))

        nuevo_usuario = Usuario(
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            id_rol=rol_cliente.id_rol,
            activo=True
        )

        db.session.add(nuevo_usuario)
        db.session.flush()

        nuevo_cliente = Cliente(
            id_usuario=nuevo_usuario.id_usuario,
            nombre=form.nombre.data,
            estatus='activo'
        )

        db.session.add(nuevo_cliente)
        db.session.commit()

        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


# ---------------- 2FA con redirección inteligente ----------------
@auth_bp.route('/verificar-2fa', methods=['GET', 'POST'])
def verificar_2fa():
    if '2fa_user_id' not in session:
        return redirect(url_for('auth.login'))

    user = Usuario.query.get(session['2fa_user_id'])

    if request.method == 'POST':
        codigo = request.form.get('codigo')

        if codigo == user.codigo_2fa:
            login_user(user)
            user.codigo_2fa = None
            db.session.commit()
            session.pop('2fa_user_id', None)

            # Redirección según rol
            if user.rol.nombre == 'Cliente':
                return redirect(url_for('home'))
            else:
                return redirect(url_for('vistaEmpleado'))

        else:
            flash('Código incorrecto', 'danger')

    return render_template('auth/verificar_2fa.html')


# ---------------- LOGOUT ----------------
@auth_bp.route('/logout')
@login_required
def logout():
    nombre = current_user.nombre_mostrable
    logout_user()
    return redirect(url_for('auth.login'))