import re
import io
from PIL import Image

from app import create_app
from models import db, User, Subject, Student, Grade
from werkzeug.security import generate_password_hash


flask_app = create_app()


def get_csrf_token(client, url):
    resp = client.get(url)
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.get_data(as_text=True))
    return match.group(1) if match else None


def make_png_bytes():
    b = io.BytesIO()
    Image.new("RGBA", (10, 10), (255, 0, 0, 255)).save(b, format="PNG")
    return b.getvalue()


def test_edit_delete_permissions(tmp_path, monkeypatch):
    # configure the imported app for testing
    # disable CSRF for this functional test to simplify form POSTs
    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test-key"})
    app = flask_app
    client = app.test_client()

    with app.app_context():
        # ensure a clean database state for the test
        db.drop_all()
        db.create_all()

        admin = User(username="admin", role="super_admin")
        admin.password_hash = generate_password_hash("pass")
        teacher = User(username="teacher", role="teacher")
        teacher.password_hash = generate_password_hash("pass")
        student_user = User(username="student", role="student")
        student_user.password_hash = generate_password_hash("pass")

        db.session.add_all([admin, teacher, student_user])
        db.session.commit()

        stu = Student(first_name="Test", last_name="Student", email="test@student.local")
        db.session.add(stu)
        subj = Subject(name="Matemáticas")
        db.session.add(subj)
        db.session.commit()

        # Teacher adds a grade (form is on the student detail page)
        client.post("/login", data={"username": "teacher", "password": "pass"})
        csrf = get_csrf_token(client, f"/students/{stu.id}")
        resp = client.post(f"/teacher/student/{stu.id}/subject/{subj.id}/grades", data={
            "score_Nota 1": 8,
            "csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200

        grade = Grade.query.filter_by(student_id=stu.id, subject_id=subj.id).first()
        assert grade is not None

        # Student should NOT be able to edit the grade
        client.get("/logout")
        client.post("/login", data={"username": "student", "password": "pass"})
        csrf = get_csrf_token(client, f"/teacher/student/{stu.id}/subject/{subj.id}/grades")
        resp = client.post(f"/teacher/student/{stu.id}/subject/{subj.id}/grades", data={
            "score_Nota 1": 10,
            "csrf_token": csrf,
        }, follow_redirects=True)
        # student must not be allowed to edit: accept 403 or localized flash
        assert resp.status_code == 403 or b"Access denied" in resp.data or b"No tiene permisos" in resp.data

        # Teacher can edit
        client.get("/logout")
        client.post("/login", data={"username": "teacher", "password": "pass"})
        csrf = get_csrf_token(client, f"/teacher/student/{stu.id}/subject/{subj.id}/grades")
        resp = client.post(f"/teacher/student/{stu.id}/subject/{subj.id}/grades", data={
            "score_Nota 1": 9,
            "csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(grade)
        assert grade.score == 9

        # Only admin can delete subject
        client.get("/logout")
        client.post("/login", data={"username": "teacher", "password": "pass"})
        csrf = get_csrf_token(client, f"/students/subjects/{subj.id}/edit")
        # teachers should not be able to delete subjects; delete form is on subject edit/list views
        resp = client.post(f"/students/subjects/{subj.id}/delete", data={"csrf_token": csrf}, follow_redirects=True)
        # teacher should be denied (403) or show localized message
        assert resp.status_code == 403 or b"Access denied" in resp.data or b"No tiene permisos" in resp.data

        client.get("/logout")
        client.post("/login", data={"username": "admin", "password": "pass"})
        csrf = get_csrf_token(client, f"/students/subjects/{subj.id}/edit")
        resp = client.post(f"/students/subjects/{subj.id}/delete", data={"csrf_token": csrf}, follow_redirects=True)
        assert resp.status_code == 200
        # ensure subject removed
        db.session.expire_all()
        assert db.session.get(Subject, subj.id) is None

        db.drop_all()
