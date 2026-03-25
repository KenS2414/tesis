import io
import os
from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from extensions import db
from models import Payment, Student, UserRole
from utils.auth import requires_roles
from utils.aws import get_presigned_url, upload_bytes_to_s3

try:
    from PIL import Image, UnidentifiedImageError
except Exception:
    raise RuntimeError(
        "Pillow is required. Install it with 'pip install Pillow' or ensure it's in requirements.txt"
    )


payments_student_bp = Blueprint("payments_student_bp", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}


def _is_admin_user():
    return current_user.is_authenticated and getattr(current_user, "role", None) in (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    )


def _process_proof_file(proof):
    """
    Validates and saves the uploaded proof file (either to S3 or locally).
    Returns a tuple (filename, has_error).
    """
    if not proof or not proof.filename:
        return None, False

    filename_safe = secure_filename(proof.filename)
    ext = filename_safe.rsplit(".", 1)[1].lower() if "." in filename_safe else ""

    # validate extension
    if ext not in ALLOWED_EXTENSIONS:
        flash("Tipo de archivo no permitido. Solo PNG, JPG, JPEG y PDF.", "warning")
        return None, True

    # basic MIME check
    if proof.mimetype and not (
        proof.mimetype.startswith("image/") or proof.mimetype == "application/pdf"
    ):
        flash("Tipo de archivo no permitido.", "warning")
        return None, True

    # read file bytes for deeper validation
    file_bytes = proof.read()
    if ext in {"png", "jpg", "jpeg"}:
        try:
            Image.open(io.BytesIO(file_bytes)).verify()
        except (UnidentifiedImageError, Exception):
            flash("Imagen inválida o corrupta.", "warning")
            return None, True
    elif ext == "pdf":
        if not file_bytes.startswith(b"%PDF"):
            flash("PDF inválido.", "warning")
            return None, True

    # use timezone-aware now() to avoid deprecation warning
    timestamped = (
        f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{filename_safe}"
    )

    if current_app.config.get("S3_BUCKET"):
        content_type = proof.mimetype if proof.mimetype else None
        try:
            upload_bytes_to_s3(file_bytes, timestamped, content_type=content_type)
            return timestamped, False
        except Exception as e:
            flash(f"Error subiendo a S3: {e}", "danger")
            return None, True
    else:
        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        with open(os.path.join(upload_dir, timestamped), "wb") as f:
            f.write(file_bytes)
        return timestamped, False


@payments_student_bp.route("/payments")
@login_required
@requires_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STUDENT)
def payments_list():
    if _is_admin_user():
        return redirect(url_for("payments_admin_bp.admin_payments"))
    # try to find the Student record for the current_user (if any)
    student = Student.query.filter_by(email=current_user.username).first()
    if not student:
        # no linked student record; show empty
        payments = []
    else:
        payments = (
            Payment.query.filter_by(student_id=student.id)
            .order_by(Payment.created_at.desc())
            .all()
        )
    # If uploads are stored on S3, generate presigned URLs for display
    if current_app.config.get("S3_BUCKET"):
        for p in payments:
            p.proof_url = (
                get_presigned_url(p.proof_filename)
                if getattr(p, "proof_filename", None)
                else None
            )
    return render_template("payments/list.html", payments=payments)


@payments_student_bp.route("/payments/new", methods=["GET", "POST"])
@login_required
@requires_roles(UserRole.STUDENT)
def payment_create():
    # students submit payments; require linked Student
    student = Student.query.filter_by(email=current_user.username).first()
    if not student:
        flash(
            "No tienes un perfil de estudiante vinculado para enviar pagos.", "warning"
        )
        return redirect(url_for("students_bp.list_students"))
    if request.method == "POST":
        amount_raw = request.form.get("amount")
        try:
            amount = float(amount_raw)
        except (TypeError, ValueError):
            flash("Importe inválido.", "warning")
            return render_template("payments/form.html")

        proof = request.files.get("proof")

        filename, has_error = _process_proof_file(proof)
        if has_error:
            return render_template("payments/form.html")

        try:
            payment = Payment(
                student_id=student.id,
                amount=amount,
                proof_filename=filename,
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()
            flash("Pago enviado y queda pendiente de verificación.", "success")
            return redirect(url_for("payments_student_bp.payments_list"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving payment: {e}")
            flash(
                "Ocurrió un error al guardar el pago. Por favor intenta de nuevo.",
                "danger",
            )
            return render_template("payments/form.html")

    return render_template("payments/form.html")
