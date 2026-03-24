import os
import sys
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, Student, Subject, Grade
import init_db

app = create_app()


@pytest.fixture
def client():
    os.environ.setdefault('SECRET_KEY', 'test-secret-crud')
    os.environ.setdefault('ADMIN_PASSWORD', 'adminpass123')
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
        db.session.commit()
        return u
    u = User(username=username, password_hash=generate_password_hash(password), role=role)
    db.session.add(u)
    db.session.commit()
    return u


def test_subject_crud_and_grade_crud(client):
    # create admin and teacher
    admin = create_user('admin2@example.com', 'adminpass', role='admin')
    teacher = create_user('teacher2@example.com', 'teachpass', role='teacher')
    # login as admin and create subject
    # include CSRF token from login form
    rv = client.get('/login')
    import re

    m = re.search(r'name="csrf_token" value="([^\"]+)"', rv.get_data(as_text=True))
    csrf = m.group(1) if m else ''
    resp = client.post('/login', data={'username': 'admin2@example.com', 'password': 'adminpass', 'csrf_token': csrf}, follow_redirects=True)
    assert resp.status_code == 200
    # now access subject create (GET to get csrf)
    rv2 = client.get('/students/subjects/new')
    m2 = re.search(r'name="csrf_token" value="([^\"]+)"', rv2.get_data(as_text=True))
    csrf2 = m2.group(1) if m2 else ''
    resp = client.post('/students/subjects/new', data={'name': 'History', 'code': 'HIS101', 'csrf_token': csrf2}, follow_redirects=True)
    assert resp.status_code == 200
    subj = Subject.query.filter_by(name='History').first()
    if subj is None:
        print('POST response:', resp.get_data(as_text=True))
        print('All subjects:', Subject.query.all())
    assert subj is not None

    # edit subject
    resp = client.post(f'/students/subjects/{subj.id}/edit', data={'name': 'World History', 'code': 'WH101'}, follow_redirects=True)
    assert resp.status_code == 200
    subj = db.session.get(Subject, subj.id)
    assert subj.name == 'World History'

    # create student record
    student = Student(first_name='Crud', last_name='Test', email='crud@example.com')
    db.session.add(student)
    db.session.commit()

    # login as teacher and add grade
    client.get('/logout')
    resp = client.post('/login', data={'username': 'teacher2@example.com', 'password': 'teachpass'}, follow_redirects=True)
    assert resp.status_code == 200
    resp = client.post(f'/students/{student.id}/add-grade', data={'subject_id': subj.id, 'score': '85', 'term': '2026-1'}, follow_redirects=True)
    assert resp.status_code == 200
    grade = Grade.query.filter_by(student_id=student.id).first()
    assert grade is not None

    # edit grade
    resp = client.post(f'/students/grades/{grade.id}/edit', data={'score': '88', 'term': '2026-1', 'comment': 'Good'}, follow_redirects=True)
    assert resp.status_code == 200
    grade = db.session.get(Grade, grade.id)
    assert float(grade.score) == 88.0

    # delete grade
    resp = client.post(f'/students/grades/{grade.id}/delete', follow_redirects=True)
    assert resp.status_code == 200
    assert db.session.get(Grade, grade.id) is None

    # delete subject (admin only)
    client.get('/logout')
    resp = client.post('/login', data={'username': 'admin2@example.com', 'password': 'adminpass'}, follow_redirects=True)
    assert resp.status_code == 200
    resp = client.post(f'/students/subjects/{subj.id}/delete', follow_redirects=True)
    assert resp.status_code == 200
    assert db.session.get(Subject, subj.id) is None
