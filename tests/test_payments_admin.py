import pytest
from extensions import db
from models import Payment, Student, UserRole

def test_admin_payment_reject_success(admin_client, app):
    # Setup: Create a student and a pending payment
    with app.app_context():
        student = Student(first_name="Test", last_name="Student", email="test@example.com")
        db.session.add(student)
        db.session.commit()

        payment = Payment(student_id=student.id, amount=100.0, status="pending")
        db.session.add(payment)
        db.session.commit()
        payment_id = payment.id

    # Action: Reject the payment as admin
    response = admin_client.post(f"/admin/payments/{payment_id}/reject", follow_redirects=True)

    # Verification
    assert response.status_code == 200
    assert b"Pago rechazado." in response.data

    with app.app_context():
        updated_payment = db.session.get(Payment, payment_id)
        assert updated_payment.status == "rejected"

def test_admin_payment_reject_404(admin_client):
    # Action: Attempt to reject a non-existent payment
    response = admin_client.post("/admin/payments/9999/reject", follow_redirects=True)

    # Verification
    assert response.status_code == 404

def test_admin_payment_reject_unauthorized(client, app):
    # Setup: Create a student user and a pending payment
    with app.app_context():
        from werkzeug.security import generate_password_hash
        from models import User
        u = User(username="student_user@example.com", password_hash=generate_password_hash("pass"), role=UserRole.STUDENT)
        db.session.add(u)

        student = Student(first_name="Test", last_name="Student", email="student_user@example.com")
        db.session.add(student)
        db.session.commit()

        payment = Payment(student_id=student.id, amount=100.0, status="pending")
        db.session.add(payment)
        db.session.commit()
        payment_id = payment.id

    # Action: Log in as student
    client.post("/login", data={"username": "student_user@example.com", "password": "pass"}, follow_redirects=True)

    # Action: Attempt to reject the payment
    response = client.post(f"/admin/payments/{payment_id}/reject", follow_redirects=True)

    # Verification
    assert b"Acceso denegado." in response.data

    with app.app_context():
        payment_after = db.session.get(Payment, payment_id)
        assert payment_after.status == "pending"
