import pytest
from flask import session

from extensions import db
from models import Student, User, UserRole

def test_register_happy_path(client, app):
    # 1. Send valid registration data
    resp = client.post(
        "/register",
        data={
            "username": "newstudent@example.com",
            "password": "securepassword",
            "confirm_password": "securepassword",
            "first_name": "Nuevo",
            "last_name": "Estudiante",
            "cedula": "12345678",
            "dob": "2000-01-01",
        },
        follow_redirects=True,
    )

    # Verify the redirect completed successfully
    assert resp.status_code == 200

    # Verify success flash message
    assert b"Registro correcto. Bienvenido!" in resp.data

    # 2. Verify Database Changes
    with app.app_context():
        # Verify User creation
        new_user = User.query.filter_by(username="newstudent@example.com").first()
        assert new_user is not None
        assert new_user.role == UserRole.STUDENT

        # Verify password is hashed and not plain text
        assert new_user.password_hash != "securepassword"
        assert new_user.check_password("securepassword") is True

        # Verify linked Student creation
        new_student = Student.query.filter_by(email="newstudent@example.com").first()
        assert new_student is not None
        assert new_student.first_name == "Nuevo"
        assert new_student.last_name == "Estudiante"

    # 3. Verify user is logged in
    with client.session_transaction() as sess:
        assert "_user_id" in sess


def test_register_missing_fields(client, app):
    # Get initial count of users and students
    with app.app_context():
        initial_user_count = User.query.count()
        initial_student_count = Student.query.count()

    # Attempt to register with missing first_name
    resp = client.post(
        "/register",
        data={
            "username": "incomplete@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "first_name": "", # Missing field
            "last_name": "Estudiante",
            "cedula": "12345678",
            "dob": "2000-01-01",
        },
        follow_redirects=True,
    )

    # Should render the register page again (status 200)
    assert resp.status_code == 200

    # Verify the warning flash message
    assert b"Rellena todos los campos obligatorios." in resp.data

    # Verify no new users or students were created
    with app.app_context():
        assert User.query.count() == initial_user_count
        assert Student.query.count() == initial_student_count


def test_register_duplicate_username(client, app):
    # 1. First, create an existing user
    with app.app_context():
        existing_user = User(
            username="existing@example.com",
            password_hash="hashedpass",
            role=UserRole.STUDENT
        )
        db.session.add(existing_user)
        db.session.commit()

        initial_user_count = User.query.count()
        initial_student_count = Student.query.count()

    # 2. Attempt to register with the same username
    resp = client.post(
        "/register",
        data={
            "username": "existing@example.com",
            "password": "newpassword123",
            "confirm_password": "newpassword123",
            "first_name": "Duplicate",
            "last_name": "User",
            "cedula": "12345678",
            "dob": "2000-01-01",
        },
        follow_redirects=True,
    )

    # Should render the register page again (status 200)
    assert resp.status_code == 200

    # Verify warning flash message
    assert b"El usuario ya existe." in resp.data

    # Verify no new users or students were created
    with app.app_context():
        assert User.query.count() == initial_user_count
        assert Student.query.count() == initial_student_count


def test_register_already_authenticated_user_get(teacher_client):
    # Try to access GET /register while already authenticated
    resp = teacher_client.get("/register", follow_redirects=False)

    # Should redirect to dashboard
    assert resp.status_code == 302
    assert "/dashboard" in (resp.headers.get("Location") or "")


def test_register_already_authenticated_user_post(teacher_client, app):
    # Get initial count of users
    with app.app_context():
        initial_user_count = User.query.count()

    # Try to access POST /register while already authenticated
    resp = teacher_client.post(
        "/register",
        data={
            "username": "auth.user@example.com",
            "password": "password",
            "first_name": "Auth",
            "last_name": "User",
        },
        follow_redirects=False,
    )

    # Should redirect to dashboard
    assert resp.status_code == 302
    assert "/dashboard" in (resp.headers.get("Location") or "")

    # Verify no new user was created
    with app.app_context():
        assert User.query.count() == initial_user_count


def test_logout_authenticated_user(super_admin_client):
    # The fixture logs the user in, so we should be authenticated

    # 1. Accessing a protected route should work (status 200)
    resp = super_admin_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 200

    # Verify session has the user before logout
    with super_admin_client.session_transaction() as sess:
        assert "_user_id" in sess

    # 2. Call logout
    resp = super_admin_client.get("/logout", follow_redirects=True)

    # Verify the redirect completed successfully (status code 200 after redirect)
    assert resp.status_code == 200

    # Verify flash message in response
    assert b"Sesi\xc3\xb3n cerrada." in resp.data

    # Verify session internal state has been cleared
    with super_admin_client.session_transaction() as sess:
        assert "_user_id" not in sess

    # 3. Accessing a protected route again should now redirect to login
    resp = super_admin_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")

def test_logout_unauthenticated_user(client):
    # Unauthenticated user trying to access /logout
    resp = client.get("/logout", follow_redirects=False)

    # Should be redirected to the login page due to @login_required
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")

def test_logout_teacher_user(teacher_client):
    # The fixture logs the teacher in, so we should be authenticated
    resp = teacher_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 200

    # Verify session has the user before logout
    with teacher_client.session_transaction() as sess:
        assert "_user_id" in sess

    # Call logout
    resp = teacher_client.get("/logout", follow_redirects=True)

    # Verify the redirect completed successfully (status code 200 after redirect)
    assert resp.status_code == 200

    # Verify flash message in response
    assert b"Sesi\xc3\xb3n cerrada." in resp.data

    # Verify session internal state has been cleared
    with teacher_client.session_transaction() as sess:
        assert "_user_id" not in sess

    # Accessing a protected route again should now redirect to login
    resp = teacher_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")
