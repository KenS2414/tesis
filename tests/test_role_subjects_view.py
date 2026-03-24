import pytest
from models import User, Student, Subject, Grade, UserRole
from werkzeug.security import generate_password_hash

def test_create_student_with_subjects(admin_client, app):
    from extensions import db
    # create subjects
    s1 = Subject(name="Math", code="M1")
    s2 = Subject(name="History", code="H1")
    db.session.add_all([s1, s2])
    db.session.commit()

    # Create student with subjects s1 and s2
    data = {
        "first_name": "New",
        "last_name": "Student",
        "email": "new@student.com",
        "subjects": [s1.id, s2.id]
    }
    resp = admin_client.post("/students/new", data=data, follow_redirects=True)
    assert resp.status_code == 200

    # Verify student created
    st = Student.query.filter_by(email="new@student.com").first()
    assert st is not None

    # Verify grades created (None score)
    grades = Grade.query.filter_by(student_id=st.id).all()
    assert len(grades) == 2
    subject_ids = [g.subject_id for g in grades]
    assert s1.id in subject_ids
    assert s2.id in subject_ids
    assert grades[0].value is None


def test_create_student_with_credentials_from_admin_panel(admin_client, app):
    from extensions import db

    data = {
        "first_name": "Cred",
        "last_name": "Student",
        "email": "cred@student.com",
        "login_username": "cred@student.com",
        "login_password": "pass1234",
    }
    resp = admin_client.post("/students/new", data=data, follow_redirects=True)
    assert resp.status_code == 200

    st = Student.query.filter_by(email="cred@student.com").first()
    assert st is not None

    u = User.query.filter_by(username="cred@student.com").first()
    assert u is not None
    assert u.role == "student"

def test_teacher_dashboard_view(teacher_client, app):
    resp = teacher_client.get("/dashboard")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Check hidden sections
    # "Estudiantes" card title
    assert "Estudiantes" not in html
    # "Pagos" card title
    assert "Pagos" not in html

    # Check teacher-specific dashboard behavior
    assert "Mis Materias" not in html
    assert "No tienes materias asignadas por ahora." in html

def test_student_dashboard_view(client, app):
    from extensions import db
    # Create student user and linked student record
    u = User(username="student1", password_hash=generate_password_hash("pass"), role="student")
    s = Student(first_name="S", last_name="T", email="student1") # email matches username for linking
    db.session.add(u)
    db.session.add(s)
    db.session.commit()

    # Login
    client.post("/login", data={"username": "student1", "password": "pass"}, follow_redirects=True)

    resp = client.get("/dashboard")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Check hidden sections
    # "Estudiantes" might appear in "Estudiantes" link but we hid it.
    # The card title "Estudiantes" should be hidden.
    # Note: "Estudiantes" might be in the navbar for Admin, but we are Student.
    # The navbar link text is "Estudiantes".
    # The card title is "Estudiantes".
    # We should check that the LINK to /students is NOT present.
    assert 'href="/students"' not in html or 'href="/students/"' not in html

    # Check visible sections
    assert "Mis Materias" in html
    # Link to profile
    assert f'/students/{s.id}' in html

def test_teacher_subjects_access(teacher_client, app):
    resp = teacher_client.get("/students/teacher/subjects")
    assert resp.status_code == 200
    assert "Mis Materias" in resp.get_data(as_text=True)


def test_teacher_cannot_access_subjects_admin_list(teacher_client, app):
    resp = teacher_client.get("/students/subjects")
    assert resp.status_code == 403

def test_student_profile_access(client, app):
    from extensions import db
    u = User(username="student2", password_hash=generate_password_hash("pass"), role="student")
    s = Student(first_name="S2", last_name="T2", email="student2")
    db.session.add(u)
    db.session.add(s)
    db.session.commit()

    client.post("/login", data={"username": "student2", "password": "pass"}, follow_redirects=True)

    # Access own profile
    resp = client.get(f"/students/{s.id}")
    assert resp.status_code == 200
    assert "Materias" in resp.get_data(as_text=True)
