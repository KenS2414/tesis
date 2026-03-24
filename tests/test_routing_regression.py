from werkzeug.security import generate_password_hash


def test_root_redirects_to_login_when_anonymous(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")


def test_dashboard_requires_authentication(client):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")


def test_login_redirects_authenticated_user(admin_client):
    resp = admin_client.get("/login", follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard" in (resp.headers.get("Location") or "")


def test_students_canonical_redirect(admin_client):
    resp = admin_client.get("/students", follow_redirects=False)
    assert resp.status_code in (301, 302, 307, 308)
    assert "/students/" in (resp.headers.get("Location") or "")


def test_students_list_available_in_blueprint(admin_client):
    resp = admin_client.get("/students/", follow_redirects=False)
    assert resp.status_code == 200


def test_admin_payments_forbidden_for_teacher(teacher_client):
    resp = teacher_client.get("/admin/payments", follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard" in (resp.headers.get("Location") or "")


def test_admin_user_redirected_from_payments_to_admin_panel(admin_client):
    resp = admin_client.get("/payments", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/payments" in (resp.headers.get("Location") or "")


def test_student_user_can_open_payments_list(client, app):
    from extensions import db
    from models import Student, User, UserRole

    username = "student-routing@example.com"
    user = User(
        username=username,
        password_hash=generate_password_hash("pass123"),
        role=UserRole.STUDENT,
    )
    student = Student(first_name="Route", last_name="Student", email=username)
    db.session.add(user)
    db.session.add(student)
    db.session.commit()

    login = client.post(
        "/login",
        data={"username": username, "password": "pass123"},
        follow_redirects=True,
    )
    assert login.status_code == 200

    resp = client.get("/payments", follow_redirects=False)
    assert resp.status_code == 200
