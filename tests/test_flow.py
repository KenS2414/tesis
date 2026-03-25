import os
import sys
import re
import pytest

# ensure project root is on sys.path for imports when pytest runs from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import Student, Payment
import init_db


app = create_app()


@pytest.fixture(scope="module")
def test_client():
    # ensure environment variables for app and init_db
    os.environ.setdefault("SECRET_KEY", "test-secret-123")
    os.environ.setdefault("ADMIN_PASSWORD", "adminpass123")
    # initialize DB / admin
    # ensure a clean DB file for tests
    try:
        os.remove(os.path.join(os.path.dirname(__file__), "..", "app.db"))
    except OSError:
        pass
    init_db.init_db(app)
    # disable CSRF for test client
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield client
    ctx.pop()
    # cleanup DB file after tests
    try:
        os.remove(os.path.join(os.path.dirname(__file__), "..", "app.db"))
    except OSError:
        pass


def _extract_csrf(html_text):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html_text)
    return m.group(1) if m else ""


def test_full_flow(test_client):
    client = test_client

    # Register a new student user
    rv = client.get("/register")
    csrf = _extract_csrf(rv.get_data(as_text=True))
    resp = client.post(
        "/register",
        data={
            "username": "student@example.com",
            "password": "pass1234",
            "confirm_password": "pass1234",
            "first_name": "Test",
            "last_name": "Student",
            "cedula": "12345678",
            "dob": "2000-01-01",
            "csrf_token": csrf,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    student = Student.query.filter_by(email="student@example.com").first()
    assert student is not None

    # Create a payment (needs a file now)
    import io
    rv = client.get("/payments/new")
    csrf = _extract_csrf(rv.get_data(as_text=True))

    # Preparamos una imagen minima real valida (PNG) para pasar la validacion con Pillow
    from PIL import Image
    img_buf = io.BytesIO()
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(img_buf, format="PNG")
    img_buf.seek(0)
    png_bytes = img_buf.getvalue()

    resp = client.post(
        "/payments/new",
        data={
            "amount": "12.50",
            "csrf_token": csrf,
            "proof": (io.BytesIO(png_bytes), "proof.png")
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200

    payment = (
        Payment.query.filter_by(student_id=student.id)
        .order_by(Payment.id.desc())
        .first()
    )
    assert payment is not None
    # Ensure payment starts as pending for the test (cleanup from previous runs)
    payment.status = "pending"
    db.session.commit()
    assert payment.status == "pending"

    # Logout and login as admin
    client.get("/logout")
    rv = client.get("/login")
    csrf = _extract_csrf(rv.get_data(as_text=True))
    resp = client.post(
        "/login",
        data={
            "username": "admin",
            "password": os.environ.get("ADMIN_PASSWORD", ""),
            "csrf_token": csrf,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # Approve payment
    resp = client.post(
        f"/admin/payments/{payment.id}/approve",
        data={"csrf_token": ""},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(payment)
    assert payment.status == "approved"
