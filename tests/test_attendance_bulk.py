import pytest
from datetime import date
from models import Attendance, AttendanceStatus, Subject, Student, UserRole, User

from extensions import db

def test_attendance_bulk_success(client, app, teacher_user):
    resp = client.post("/login", data={"username": "teacher1", "password": "teacherpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)

    # Create test data
    student = Student(first_name="Test", last_name="Student", email="test@test.com", current_year_group="1er Grado")
    db.session.add(student)
    db.session.commit()

    subj = Subject(name="Math", code="MATH101", year_group="1er Grado", credits=3)
    db.session.add(subj)
    db.session.commit()

    payload = {
        'subject_id': subj.id,
        'date': date.today().isoformat(),
        'records': [
            {'student_id': student.id, 'status': 'PRESENT', 'remarks': 'On time'}
        ]
    }

    resp = client.post(
        '/teacher/attendance/bulk',
        json=payload,
        headers={'Content-Type': 'application/json'}
    )

    assert resp.status_code == 200
    assert resp.json == {'status': 'success'}

    # Check DB
    att = Attendance.query.filter_by(student_id=student.id, subject_id=subj.id).first()
    assert att is not None
    assert att.status == AttendanceStatus.PRESENT
    assert att.remarks == 'On time'

def test_attendance_bulk_forbidden_for_student(client, app):
    # Create a student user
    from werkzeug.security import generate_password_hash
    u = User(username="student1", password_hash=generate_password_hash("studentpass"), role=UserRole.STUDENT)
    db.session.add(u)
    db.session.commit()

    resp = client.post("/login", data={"username": "student1", "password": "studentpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)

    resp = client.post(
        '/teacher/attendance/bulk',
        json={'subject_id': 1, 'records': [{'student_id': 1, 'status': 'PRESENT'}]},
        headers={'Content-Type': 'application/json'}
    )

    # Should be forbidden for students
    assert resp.status_code == 403

def test_attendance_bulk_missing_fields(client, app, teacher_user):
    resp = client.post("/login", data={"username": "teacher1", "password": "teacherpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)

    resp = client.post(
        '/teacher/attendance/bulk',
        json={'subject_id': 1}, # Missing records
        headers={'Content-Type': 'application/json'}
    )

    assert resp.status_code == 400
    assert 'error' in resp.json

def test_attendance_bulk_upsert(client, app, teacher_user):
    resp = client.post("/login", data={"username": "teacher1", "password": "teacherpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)

    student = Student(first_name="Test2", last_name="Student2", email="test2@test.com", current_year_group="1er Grado")
    db.session.add(student)
    db.session.commit()

    subj = Subject(name="Math2", code="MATH102", year_group="1er Grado", credits=3)
    db.session.add(subj)
    db.session.commit()

    # Insert initially as ABSENT
    payload = {
        'subject_id': subj.id,
        'date': date.today().isoformat(),
        'records': [
            {'student_id': student.id, 'status': 'ABSENT', 'remarks': 'Missed first half'}
        ]
    }
    resp1 = client.post('/teacher/attendance/bulk', json=payload, headers={'Content-Type': 'application/json'})
    assert resp1.status_code == 200

    # Update to LATE
    payload['records'][0]['status'] = 'LATE'
    payload['records'][0]['remarks'] = 'Arrived late'

    resp2 = client.post('/teacher/attendance/bulk', json=payload, headers={'Content-Type': 'application/json'})
    assert resp2.status_code == 200

    # Check DB to ensure it updated rather than inserted
    atts = Attendance.query.filter_by(student_id=student.id, subject_id=subj.id).all()
    assert len(atts) == 1
    assert atts[0].status == AttendanceStatus.LATE
    assert atts[0].remarks == 'Arrived late'
