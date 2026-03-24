from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models import (
    Student,
    StudentAccount,
    Invoice,
    InvoiceStatus,
    PaymentRecord,
    Scholarship,
    FeeCategory,
)
from marshmallow import Schema, fields, ValidationError
import inspect
from decimal import Decimal
from datetime import date, datetime, timedelta
from utils.aws import upload_bytes_to_s3, get_presigned_url

finance_bp = Blueprint('finance_bp', __name__, url_prefix='/finance')


class InvoiceSchema(Schema):
    student_id = fields.Int(required=True)
    monto_total = fields.Decimal(as_string=True, required=True)
    def _date_field_with_default(default_callable):
        sig = inspect.signature(fields.Date.__init__)
        if 'missing' in sig.parameters:
            return fields.Date(missing=default_callable)
        if 'load_default' in sig.parameters:
            return fields.Date(load_default=default_callable)
        return fields.Date()

    fecha_emision = _date_field_with_default(lambda: date.today())
    fecha_vencimiento = fields.Date(allow_none=True)


class PaymentRegisterSchema(Schema):
    invoice_id = fields.Int(required=True)
    monto_pagado = fields.Decimal(as_string=True, required=True)
    metodo_pago = fields.Str(required=True)
    # optional: file bytes or key
    comprobante_key = fields.Str(allow_none=True)


def _apply_scholarship(student_id, amount: Decimal) -> Decimal:
    sch = (
        db.session.query(Scholarship)
        .filter(Scholarship.student_id == student_id, Scholarship.activa == True)
        .first()
    )
    if not sch:
        return amount
    discount = (Decimal(sch.porcentaje_descuento) / Decimal(100)) * amount
    return (amount - discount).quantize(Decimal('0.01'))


@finance_bp.route('/student/<int:student_id>/status')
@login_required
def student_status(student_id):
    s = db.session.get(Student, student_id)
    if s is None:
        return (jsonify({'error': 'student not found'}), 404)
    acct = db.session.query(StudentAccount).filter_by(student_id=student_id).first()
    balance = acct.balance_total if acct else Decimal('0.00')
    invoices = [
        {
            'id': inv.id,
            'monto_total': str(inv.monto_total),
            'fecha_emision': inv.fecha_emision.isoformat(),
            'fecha_vencimiento': inv.fecha_vencimiento.isoformat() if inv.fecha_vencimiento else None,
            'status': inv.status.name,
        }
        for inv in (s.invoices or [])
    ]
    return jsonify({'student_id': student_id, 'balance_total': str(balance), 'invoices': invoices})


@finance_bp.route('/invoice/generate-monthly', methods=['POST'])
@login_required
def generate_monthly_invoices():
    # restrict to admin or treasury
    role = getattr(current_user, 'role', None)
    if role not in ('admin', 'treasury'):
        return (jsonify({'error': 'forbidden'}), 403)

    limit = request.args.get('limit', type=int, default=100)
    offset = request.args.get('offset', type=int, default=0)

    # generate invoices for all students
    students = Student.query.order_by(Student.id).limit(limit).offset(offset).all()
    created = 0
    today = date.today()
    default_due = today + timedelta(days=30)
    try:
        with db.session.begin():
            for st in students:
                # compute base amount: sum of all fee categories (simplified)
                fee_total = Decimal('0.00')
                fees = FeeCategory.query.all()
                for f in fees:
                    fee_total += Decimal(f.monto_base)
                if fee_total == Decimal('0.00'):
                    continue
                total_after_discount = _apply_scholarship(st.id, fee_total)
                inv = Invoice(student_id=st.id, monto_total=total_after_discount, fecha_emision=today, fecha_vencimiento=default_due, status=InvoiceStatus.PENDING)
                db.session.add(inv)
                # ensure student account exists
                acct = StudentAccount.query.filter_by(student_id=st.id).first()
                if not acct:
                    acct = StudentAccount(student_id=st.id, balance_total=total_after_discount)
                    db.session.add(acct)
                else:
                    acct.balance_total = (Decimal(acct.balance_total) + total_after_discount)
                created += 1
        return jsonify({'status': 'ok', 'created_invoices': created})
    except Exception as e:
        db.session.rollback()
        return (jsonify({'error': str(e)}), 500)


@finance_bp.route('/payment/register', methods=['POST'])
@login_required
def register_payment():
    # only treasury or admin or student paying own invoice
    payload = request.form.to_dict() or request.get_json() or {}
    try:
        data = PaymentRegisterSchema().load(payload)
    except ValidationError as ve:
        return (jsonify({'error': 'validation error', 'details': ve.messages}), 400)
    inv = db.session.get(Invoice, data['invoice_id'])
    if inv is None:
        return (jsonify({'error': 'invoice not found'}), 404)
    # permission: admin/treasury or student owner
    role = getattr(current_user, 'role', None)
    if role not in ('admin', 'treasury'):
        student = current_user.get_student()
        if not student or student.id != inv.student_id:
            return (jsonify({'error': 'forbidden'}), 403)
    amount = Decimal(data['monto_pagado'])
    key = data.get('comprobante_key')
    proof_url = None
    # if file uploaded as 'proof', try upload to S3/MinIO
    if 'proof' in request.files:
        f = request.files['proof']
        if f and f.filename:
            key_name = f"payments/{inv.id}/{f.filename}"
            upload_bytes_to_s3(f.read(), key_name, content_type=f.content_type)
            proof_url = get_presigned_url(key_name)
    elif key:
        # treat key as existing object key
        proof_url = get_presigned_url(key)
    try:
        with db.session.begin():
            pay = PaymentRecord(invoice_id=inv.id, monto_pagado=amount, metodo_pago=data['metodo_pago'], comprobante_url=proof_url)
            db.session.add(pay)
            # update invoice status
            total_paid = sum([Decimal(p.monto_pagado) for p in inv.payments]) + amount
            if total_paid >= Decimal(inv.monto_total):
                inv.status = InvoiceStatus.PAID
            # update student account
            acct = StudentAccount.query.filter_by(student_id=inv.student_id).first()
            if not acct:
                acct = StudentAccount(student_id=inv.student_id, balance_total=Decimal('0.00'))
                db.session.add(acct)
            acct.balance_total = Decimal(acct.balance_total) - amount
        return jsonify({'status': 'ok', 'payment_id': pay.id})
    except Exception as e:
        db.session.rollback()
        return (jsonify({'error': str(e)}), 500)