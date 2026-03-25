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
        from datetime import datetime
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        cedula = (request.form.get("cedula") or "").strip() or None
        dob_raw = request.form.get("dob")

        if not username or not password or not first_name or not last_name or not confirm_password or not cedula or not dob_raw:
            flash("Rellena todos los campos obligatorios.", "warning")
            return render_template("register.html")

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template("register.html")

        try:
            dob = datetime.strptime(dob_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Formato de fecha de nacimiento inválido.", "warning")
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
        student = Student(
            first_name=first_name,
            last_name=last_name,
            email=username,
            cedula=cedula,
            dob=dob
        )
        try:
            db.session.add(new_user)
            db.session.add(student)
            db.session.flush()

            photo = request.files.get("photo")
            if photo and photo.filename:
                from werkzeug.utils import secure_filename
                from utils.aws import upload_bytes_to_s3
                filename = secure_filename(photo.filename)
                key_name = f"students/{student.id}/photo_{filename}"
                upload_bytes_to_s3(photo.read(), key_name, content_type=photo.content_type)
                student.photo_filename = key_name

            db.session.commit()
            login_user(new_user)
            flash("Registro correcto. Bienvenido!", "success")
            return redirect(url_for("main_bp.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error durante el registro: {e}", "danger")
            return render_template("register.html")

    return render_template("register.html")
