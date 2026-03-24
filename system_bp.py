import os

from flask import Blueprint, current_app, redirect, send_from_directory, url_for
from sqlalchemy import text

from flask import render_template, request, flash
from extensions import db
from utils.auth import requires_roles
from models import AcademicYear, AcademicYearStatus, UserRole
from flask_login import login_required


system_bp = Blueprint("system_bp", __name__)


@system_bp.route('/health')
def health():
    """Health endpoint: basic DB check.

    Returns 200 if DB responds to a trivial query, otherwise 503.
    """
    db_ok = True
    try:
        # lightweight DB check
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Health check: DB query failed")
        db_ok = False
    status = {"status": "ok" if db_ok else "degraded", "db": db_ok}
    return status, (200 if db_ok else 503)


@system_bp.route('/ready')
def ready():
    """Readiness endpoint: checks DB and S3 (if configured).

    Returns 200 when DB is reachable and S3 (if configured) is accessible.
    Otherwise returns 503.
    """
    db_ok = True
    s3_ok = True
    # DB check
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Readiness check: DB query failed")
        db_ok = False

    # S3 check (optional) — only verify in production to avoid local MinIO boot-order issues
    bucket = current_app.config.get("S3_BUCKET")
    if bucket and os.environ.get("FLASK_ENV") == "production":
        try:
            from utils.aws import check_s3_connection

            check_s3_connection()
        except Exception:
            current_app.logger.exception("Readiness check: S3 bucket access failed")
            s3_ok = False

    overall_ok = db_ok and (s3_ok if bucket else True)
    status = {
        "status": "ready" if overall_ok else "not_ready",
        "db": db_ok,
        "s3": (s3_ok if bucket else "not_configured"),
    }
    return status, (200 if overall_ok else 503)


@system_bp.route('/brand-logo')
def brand_logo():
    custom_logo_dir = os.path.join(current_app.root_path, 'img')
    custom_logo_name = 'honda.jpg'
    custom_logo_path = os.path.join(custom_logo_dir, custom_logo_name)
    if os.path.exists(custom_logo_path):
        return send_from_directory(custom_logo_dir, custom_logo_name)
    return redirect(url_for('static', filename='images/logo.svg'))


@system_bp.route('/admin/academic-years')
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def list_academic_years():
    years = AcademicYear.query.order_by(AcademicYear.fecha_inicio.desc()).all()
    return render_template('system/academic_years_list.html', years=years)


@system_bp.route('/admin/academic-years/new', methods=['GET', 'POST'])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def create_academic_year():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        fecha_inicio_raw = request.form.get('fecha_inicio')
        fecha_fin_raw = request.form.get('fecha_fin')

        if not nombre or not fecha_inicio_raw or not fecha_fin_raw:
            flash('Todos los campos son obligatorios.', 'warning')
            return render_template('system/academic_year_form.html')

        try:
            from datetime import datetime
            fecha_inicio = datetime.strptime(fecha_inicio_raw, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_raw, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha inválido. Use YYYY-MM-DD.', 'warning')
            return render_template('system/academic_year_form.html')

        if fecha_fin <= fecha_inicio:
            flash('La fecha de fin debe ser posterior a la fecha de inicio.', 'warning')
            return render_template('system/academic_year_form.html')

        year = AcademicYear(
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            status=AcademicYearStatus.OPEN
        )
        db.session.add(year)
        db.session.commit()
        flash('Año académico creado.', 'success')
        return redirect(url_for('system_bp.list_academic_years'))

    return render_template('system/academic_year_form.html')


@system_bp.route('/admin/academic-years/<int:year_id>/status', methods=['POST'])
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def set_academic_year_status(year_id):
    year = db.session.get(AcademicYear, year_id)
    if not year:
        flash('Año académico no encontrado.', 'danger')
        return redirect(url_for('system_bp.list_academic_years'))

    new_status_str = request.form.get('status')
    try:
        new_status = AcademicYearStatus[new_status_str]
    except KeyError:
        flash('Estado inválido.', 'warning')
        return redirect(url_for('system_bp.list_academic_years'))

    year.status = new_status
    db.session.commit()
    flash(f'Estado actualizado a {new_status.name}.', 'success')
    return redirect(url_for('system_bp.list_academic_years'))
