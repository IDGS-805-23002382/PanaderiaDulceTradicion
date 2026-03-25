# blueprints/auth/routesAuth.py
from flask import render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import db, Usuario, Rol
from forms import LoginForm, RegisterForm
from . import auth_bp


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
            return redirect(url_for('home'))
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