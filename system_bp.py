import os

from flask import Blueprint, current_app, redirect, send_from_directory, url_for
from sqlalchemy import text

from extensions import db


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
