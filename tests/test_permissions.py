import os
import sys
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, Student, Subject
import init_db

app = create_app()


@pytest.fixture
def client():
    os.environ.setdefault('SECRET_KEY', 'test-secret-roles')
    os.environ.setdefault('ADMIN_PASSWORD', 'adminpass123')
    # ensure clean DB
    db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app.db'))
    try:
        os.remove(db_file)
    except Exception:
        pass
    init_db.init_db(app)
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield client
    ctx.pop()
    try:
        os.remove(db_file)
    except Exception:
        pass


def create_user(username, password, role='user'):
    u = User.query.filter_by(username=username).first()
    if u:
        u.password_hash = generate_password_hash(password)
        u.role = role
    else:
        u = User(username=username, password_hash=generate_password_hash(password), role=role)
        db.session.add(u)
    db.session.commit()
    return u


def test_teacher_can_add_grade_but_student_cannot(client):
    # create teacher and student users
    teacher = create_user('teacher@example.com', 'teachpass', role='teacher')
    student_user = create_user('student2@example.com', 'studpass', role='student')
    # create a Student row and a Subject
    student = Student(first_name='S', last_name='T', email='student2@example.com')
    db.session.add(student)
    s = Subject(name='Math')
    db.session.add(s)
    db.session.commit()

    # login as teacher and add grade
    resp = client.post('/login', data={'username': 'teacher@example.com', 'password': 'teachpass'}, follow_redirects=True)
    assert resp.status_code == 200
    resp = client.post(f'/students/{student.id}/add-grade', data={'subject_id': s.id, 'score': '90'}, follow_redirects=True)
    assert resp.status_code == 200

    # logout
    client.get('/logout')

    # login as student and attempt to add grade -> should be 403
    resp = client.post('/login', data={'username': 'student2@example.com', 'password': 'studpass'}, follow_redirects=True)
    assert resp.status_code == 200
    resp = client.post(f'/students/{student.id}/add-grade', data={'subject_id': s.id, 'score': '80'}, follow_redirects=False)
    assert resp.status_code == 403