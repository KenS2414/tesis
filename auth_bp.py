import os

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash

from extensions import db
from models import Student, User, UserRole


auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.dashboard"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if not username or not password:
            flash("Ingresa usuario y contraseña.", "warning")
            return render_template("login.html")
        try:
            user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
        except OperationalError as e:
            if "no such table" in str(e).lower():
                db.create_all()
                if os.environ.get("FLASK_ENV") != "production":
                    director_password = os.environ.get("DIRECTOR_PASSWORD", "admin")
                    director_user = User.query.filter_by(username="director").first()
                    if director_user is None:
                        director_user = User(
                            username="director",
                            password_hash=generate_password_hash(director_password),
                            role=UserRole.ADMIN,
                        )
                        db.session.add(director_user)
                        db.session.commit()
                user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
            else:
                raise
        if user and user.check_password(password):
            login_user(user)
            flash("Inicio de sesión correcto.", "success")
            return redirect(url_for("main_bp.dashboard"))
        flash("Credenciales inválidas.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth_bp.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.dashboard"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        if not username or not password or not first_name or not last_name:
            flash("Rellena usuario, contraseña, nombre y apellido.", "warning")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe.", "warning")
            return render_template("register.html")
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=UserRole.STUDENT,
        )
        # create linked Student so payment flow works by default
        student = Student(first_name=first_name, last_name=last_name, email=username)
        db.session.add(new_user)
        db.session.add(student)
        db.session.commit()
        login_user(new_user)
        flash("Registro correcto. Bienvenido!", "success")
        return redirect(url_for("main_bp.dashboard"))
    return render_template("register.html")
