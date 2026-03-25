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
    resp = client.post(f'/teacher/{student.id}/add-grade', data={'subject_id': s.id, 'score': '90'}, follow_redirects=True)
    assert resp.status_code == 200

    # logout
    client.get('/logout')

    # login as student and attempt to add grade -> should be 403
    resp = client.post('/login', data={'username': 'student2@example.com', 'password': 'studpass'}, follow_redirects=True)
    assert resp.status_code == 200
    resp = client.post(f'/teacher/{student.id}/add-grade', data={'subject_id': s.id, 'score': '80'}, follow_redirects=False)
    assert resp.status_code == 403

def test_student_cannot_approve_payment(client):
    from models import Payment
    student_user = create_user('student3@example.com', 'studpass', role='student')
    student = Student(first_name='A', last_name='B', email='student3@example.com')
    db.session.add(student)
    db.session.commit()

    payment = Payment(student_id=student.id, amount=100)
    db.session.add(payment)
    db.session.commit()

    resp = client.post('/login', data={'username': 'student3@example.com', 'password': 'studpass'}, follow_redirects=True)
    assert resp.status_code == 200

    resp = client.post(f'/admin/payments/{payment.id}/approve', follow_redirects=False)
    # Admin routes redirect to dashboard if not admin with a flash message, which is a 302
    assert resp.status_code == 302
    assert '/dashboard' in resp.headers.get('Location', '')


def test_teacher_cannot_access_academic_years(client):
    teacher = create_user('teacher2@example.com', 'teachpass', role='teacher')

    resp = client.post('/login', data={'username': 'teacher2@example.com', 'password': 'teachpass'}, follow_redirects=True)
    assert resp.status_code == 200

    resp = client.get('/admin/academic-years', follow_redirects=False)
    assert resp.status_code == 403


def test_teacher_cannot_grade_unassigned_subject(client):
    teacher1 = create_user('teacher1@example.com', 'teachpass', role='teacher')
    teacher2 = create_user('teacher2@example.com', 'teachpass', role='teacher')

    student = Student(first_name='S', last_name='T', email='st@example.com')
    db.session.add(student)
    db.session.commit()

    # assign subject to teacher2
    s = Subject(name='Physics', teacher_id=teacher2.id)
    db.session.add(s)
    db.session.commit()

    # login as teacher1
    resp = client.post('/login', data={'username': 'teacher1@example.com', 'password': 'teachpass'}, follow_redirects=True)
    assert resp.status_code == 200

    # try to grade subject owned by teacher2
    resp = client.post('/teacher/grades', json={
        'student_id': student.id,
        'subject_id': s.id,
        'value': 15,
        'comment': 'Good'
    }, follow_redirects=False)

    assert resp.status_code == 403