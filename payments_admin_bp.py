from flask import Blueprint, render_template, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user

from extensions import db
from models import Payment, UserRole
from utils.aws import get_presigned_url


payments_admin_bp = Blueprint("payments_admin_bp", __name__)


def _is_admin_user():
    return current_user.is_authenticated and getattr(current_user, "role", None) in (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    )


@payments_admin_bp.route("/admin/payments")
@login_required
def admin_payments():
    if not _is_admin_user():
        flash("Acceso denegado.", "danger")
        return redirect(url_for("main_bp.dashboard"))
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
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
    from models import StudentAccount
    # Fetch accounts with balance > 0
    accounts = StudentAccount.query.filter(StudentAccount.balance_total > 0).all()
    return render_template("payments/admin_debts.html", accounts=accounts)
