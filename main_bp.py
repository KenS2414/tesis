from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from models import Subject, UserRole


main_bp = Blueprint("main_bp", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.dashboard"))
    return redirect(url_for("auth_bp.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    teacher_subjects = []
    if current_user.role == UserRole.TEACHER:
        teacher_subjects = (
            Subject.query.filter_by(teacher_id=current_user.id)
            .order_by(Subject.name)
            .all()
        )
    return render_template(
        "dashboard.html",
        user=current_user,
        teacher_subjects=teacher_subjects,
    )
