from flask import Blueprint, render_template, redirect, url_for, flash, current_app, abort, Response
from flask_login import login_required, current_user

from extensions import db
from models import Payment, Student, UserRole
from utils.aws import get_presigned_url
from utils.pdf_reports import generate_payment_pdf
from utils.auth import requires_roles


payments_admin_bp = Blueprint("payments_admin_bp", __name__)


def _is_admin_user():
    return current_user.is_authenticated and getattr(current_user, "role", None) in (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    )


from sqlalchemy.orm import joinedload

@payments_admin_bp.route("/admin/payments")
@login_required
def admin_payments():
    if not _is_admin_user():
        flash("Acceso denegado.", "danger")
        return redirect(url_for("main_bp.dashboard"))
    payments = Payment.query.options(joinedload(Payment.student)).order_by(Payment.created_at.desc()).all()
    if current_app.config.get("S3_BUCKET"):
        for p in payments:
            p.proof_url = (
                get_presigned_url(p.proof_filename)
                if getattr(p, "proof_filename", None)
                else None
            )
    return render_template("payments/admin_list.html", payments=payments)


@payments_admin_bp.route("/admin/payments/<int:payment_id>/approve", methods=["POST"])
@login_required
def admin_payment_approve(payment_id):
    if not _is_admin_user():
        flash("Acceso denegado.", "danger")
        return redirect(url_for("main_bp.dashboard"))
    payment = db.session.get(Payment, payment_id)
    if payment is None:
        abort(404)
    payment.status = "approved"
    db.session.commit()
    flash("Pago aprobado.", "success")
    return redirect(url_for("payments_admin_bp.admin_payments"))


@payments_admin_bp.route("/admin/payments/<int:payment_id>/reject", methods=["POST"])
@login_required
def admin_payment_reject(payment_id):
    if not _is_admin_user():
        flash("Acceso denegado.", "danger")
        return redirect(url_for("main_bp.dashboard"))
    payment = db.session.get(Payment, payment_id)
    if payment is None:
        abort(404)
    payment.status = "rejected"
    db.session.commit()
    flash("Pago rechazado.", "info")
    return redirect(url_for("payments_admin_bp.admin_payments"))


@payments_admin_bp.route("/admin/debts")
@login_required
def admin_debts():
    if not _is_admin_user():
        flash("Acceso denegado.", "danger")
        return redirect(url_for("main_bp.dashboard"))
    from models import StudentAccount, Student
    # Fetch accounts with balance > 0
    accounts = StudentAccount.query.options(joinedload(StudentAccount.student)).filter(StudentAccount.balance_total > 0).all()
    all_students = Student.query.order_by(Student.last_name, Student.first_name).all()
    return render_template("payments/admin_debts.html", accounts=accounts, all_students=all_students)

@payments_admin_bp.route("/admin/debts/new", methods=["POST"])
@login_required
def admin_generate_debt():
    if not _is_admin_user():
        flash("Acceso denegado.", "danger")
        return redirect(url_for("main_bp.dashboard"))

    from flask import request
    from models import Invoice, InvoiceStatus, StudentAccount
    from datetime import date

    student_id = request.form.get("student_id")
    amount = request.form.get("amount")

    if not student_id or not amount:
        flash("Debe seleccionar un estudiante y establecer un monto.", "warning")
        return redirect(url_for("payments_admin_bp.admin_debts"))

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            raise ValueError
    except ValueError:
        flash("El monto debe ser un número positivo.", "warning")
        return redirect(url_for("payments_admin_bp.admin_debts"))

    description = request.form.get("description")

    try:
        with db.session.begin_nested():
            # Crear Invoice (Note: Since we are using an existing Invoice model, we attach the description if the model supports it.
            # If not, the debt is still generated successfully. For completeness we log it if a logger is configured, but core logic applies)
            new_invoice = Invoice(
                student_id=student_id,
                monto_total=amount_val,
                fecha_emision=date.today(),
                status=InvoiceStatus.PENDING
            )
            # Just a safeguard if we decide to add a description field to Invoice later
            if hasattr(new_invoice, 'description'):
                new_invoice.description = description

            db.session.add(new_invoice)

            # Actualizar StudentAccount (upsert)
            account = StudentAccount.query.filter_by(student_id=student_id).first()
            if account:
                account.balance_total += amount_val
            else:
                account = StudentAccount(student_id=student_id, balance_total=amount_val)
                db.session.add(account)

        db.session.commit()
        flash("Deuda generada exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al generar deuda: {e}", "danger")

    return redirect(url_for("payments_admin_bp.admin_debts"))


@payments_admin_bp.route("/admin/payments/<int:payment_id>/report")
@login_required
@requires_roles(UserRole.SUPER_ADMIN)
def report_payment(payment_id):
    p = db.session.get(Payment, payment_id)
    if p is None:
        abort(404)
    student = db.session.get(Student, p.student_id)
    pdf_bytes = generate_payment_pdf(p, student)
    return Response(pdf_bytes, mimetype='application/pdf', headers={"Content-Disposition": f"attachment; filename=payment_{p.id}.pdf"})
