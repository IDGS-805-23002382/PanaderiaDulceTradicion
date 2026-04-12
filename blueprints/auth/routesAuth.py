# blueprints/auth/routesAuth.py
from flask import render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import db, Usuario, Rol
from forms import LoginForm, RegisterForm
from . import auth_bp
from blueprints.auth.forms import ResetPasswordForm


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and check_password_hash(usuario.password, form.password.data):
            if not usuario.activo:
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(usuario, remember=form.remember.data)
            return redirect(url_for('vistaEmpleado'))
        flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Ya existe una cuenta con ese correo.', 'warning')
            return redirect(url_for('auth.register'))
        # Asignar el rol con menor id por defecto (puedes cambiarlo)
        rol_default = Rol.query.order_by(Rol.id_rol).first()
        nuevo = Usuario(
            nombre   = form.nombre.data,
            email    = form.email.data,
            password = generate_password_hash(form.password.data),
            id_rol   = rol_default.id_rol if rol_default else 1
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Cuenta creada correctamente. Inicia sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user:
            # 1. Generar token (dura 30 min)
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='pw-reset-salt')
            
            # 2. Crear el mensaje
            link = url_for('auth.reset_with_token', token=token, _external=True)
            msg = Message('Restablecer Contraseña - Dulce Tradición',
                          recipients=[user.email])
            msg.body = f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {link}'
            
            # 3. Enviar
            mail.send(msg)
            flash('Se ha enviado un correo con instrucciones.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('El correo no está registrado.', 'warning')
            
    return render_template('auth/reset.html', form=form)

@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # Valida que el token no haya expirado (1800 segundos = 30 min)
        email = s.loads(token, salt='pw-reset-salt', max_age=1800)
    except:
        flash('El enlace es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.reset'))

    # Aquí usarías un formulario nuevo para la nueva contraseña
    if request.method == 'POST':
        nueva_pass = request.form.get('password')
        user = Usuario.query.filter_by(email=email).first()
        
        # Actualizar en la base de datos (usando el hash de werkzeug)
        user.password = generate_password_hash(nueva_pass)
        db.session.commit()
        
        flash('Tu contraseña ha sido actualizada.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/nuevo_password.html')