import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so local modules (extensions, models, etc.) can be imported
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import pytest
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, Student, Subject


def _selected_mark_expression(argv):
    """Return pytest -m expression when present."""
    for i, arg in enumerate(argv):
        if arg == "-m" and i + 1 < len(argv):
            return argv[i + 1]
    return ""


def _is_integration_only_run(argv):
    expr = (_selected_mark_expression(argv) or "").strip().lower()
    if not expr:
        return False
    return "integration" in expr and "not integration" not in expr


# Ensure minimal environment for importing the Flask app during tests
# These values are safe for test runs and only used if not already set.
os.environ.setdefault("SECRET_KEY", "test-secret")
# Protege pruebas locales de variables persistidas en la terminal.
if not _is_integration_only_run(sys.argv):
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture
def app():
    from app import create_app

    flask_app = create_app()

    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test",
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    u = User.query.filter_by(username="admin").first()
    if u:
        u.password_hash = generate_password_hash("adminpass")
        u.role = "admin"
        db.session.commit()
        return u
    u = User(username="admin", password_hash=generate_password_hash("adminpass"), role="admin")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def teacher_user(app):
    u = User.query.filter_by(username="teacher1").first()
    if u:
        u.password_hash = generate_password_hash("teacherpass")
        u.role = "teacher"
        db.session.commit()
        return u
    u = User(username="teacher1", password_hash=generate_password_hash("teacherpass"), role="teacher")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def sample_subjects(app):
    s1 = Subject(name="Matemáticas", code="MATH101")
    s2 = Subject(name="Historia", code="HIST101")
    db.session.add_all([s1, s2])
    db.session.commit()
    return [s1, s2]


@pytest.fixture
def sample_students(app):
    st1 = Student(first_name="Juan", last_name="Perez", email="juan@example.com")
    st2 = Student(first_name="Ana", last_name="Gomez", email="ana@example.com")
    db.session.add_all([st1, st2])
    db.session.commit()
    return [st1, st2]


@pytest.fixture
def super_admin_client(client, admin_user):
    # helper: logs in as admin and returns a test client with session
    resp = client.post("/login", data={"username": "admin", "password": "adminpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)
    return client


@pytest.fixture
def super_admin_user(app):
    from models import UserRole
    u = User.query.filter_by(username="superadmin").first()
    if u:
        u.password_hash = generate_password_hash("superadminpass")
        u.role = UserRole.SUPER_ADMIN
        db.session.commit()
        return u
    u = User(username="superadmin", password_hash=generate_password_hash("superadminpass"), role=UserRole.SUPER_ADMIN)
    db.session.add(u)
    db.session.commit()
    return u

@pytest.fixture
def super_admin_client(client, super_admin_user):
    resp = client.post("/login", data={"username": "superadmin", "password": "superadminpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)
    return client

@pytest.fixture
def admin_client(client, admin_user):
    resp = client.post("/login", data={"username": "admin", "password": "adminpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)
    return client


@pytest.fixture
def teacher_client(client, teacher_user):
    resp = client.post("/login", data={"username": "teacher1", "password": "teacherpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)
    return client
