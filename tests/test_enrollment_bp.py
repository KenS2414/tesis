import pytest
from datetime import date, timedelta
from flask import json
from extensions import db
from models import Student, Section, AcademicYear, Enrollment, EnrollmentStatus, AcademicYearStatus, Level

@pytest.fixture
def test_student(app):
    student = Student(first_name="Test", last_name="Student", email="teststudent@example.com")
    db.session.add(student)
    db.session.commit()
    return student

@pytest.fixture
def test_level(app):
    level = Level(nombre="Level 1", nivel_educativo="Primaria")
    db.session.add(level)
    db.session.commit()
    return level

@pytest.fixture
def test_section(app, test_level):
    section = Section(level_id=test_level.id, nombre="A", capacidad_maxima=2)
    db.session.add(section)
    db.session.commit()
    return section

@pytest.fixture
def test_academic_year(app):
    year = AcademicYear(
        nombre="2024-2025",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=365),
        status=AcademicYearStatus.OPEN
    )
    db.session.add(year)
    db.session.commit()
    return year

def test_register_enrollment_success(admin_client, test_student, test_section, test_academic_year):
    """Happy path: register a student successfully."""
    payload = {
        "student_id": test_student.id,
        "section_id": test_section.id,
        "academic_year_id": test_academic_year.id
    }

    response = admin_client.post(
        '/enrollment/register',
        json=payload
    )

    if response.status_code != 201:
        print(response.get_json())
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'enrollment_id' in data

    # Verify in DB
    enrollment = db.session.get(Enrollment, data['enrollment_id'])
    assert enrollment is not None
    assert enrollment.student_id == test_student.id
    assert enrollment.section_id == test_section.id
    assert enrollment.academic_year_id == test_academic_year.id
    assert enrollment.estado == EnrollmentStatus.ACTIVE

def test_register_enrollment_forbidden(teacher_client, test_student, test_section, test_academic_year):
    """Try to register using a user without admin or enrollment role."""
    payload = {
        "student_id": test_student.id,
        "section_id": test_section.id,
        "academic_year_id": test_academic_year.id
    }

    response = teacher_client.post(
        '/enrollment/register',
        json=payload
    )

    assert response.status_code == 403
    data = response.get_json()
    assert data['error'] == 'forbidden'

def test_register_enrollment_validation_error(admin_client):
    """Try to register with missing fields."""
    payload = {
        "student_id": 1
        # missing section_id and academic_year_id
    }

    response = admin_client.post(
        '/enrollment/register',
        json=payload
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'validation error'
    assert 'section_id' in data['details']
    assert 'academic_year_id' in data['details']

def test_register_enrollment_student_not_found(admin_client, test_section, test_academic_year):
    """Try to register a non-existent student."""
    payload = {
        "student_id": 9999,
        "section_id": test_section.id,
        "academic_year_id": test_academic_year.id
    }

    response = admin_client.post(
        '/enrollment/register',
        json=payload
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'student not found'

def test_register_enrollment_section_not_found(admin_client, test_student, test_academic_year):
    """Try to register to a non-existent section."""
    payload = {
        "student_id": test_student.id,
        "section_id": 9999,
        "academic_year_id": test_academic_year.id
    }

    response = admin_client.post(
        '/enrollment/register',
        json=payload
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'section not found'

def test_register_enrollment_academic_year_not_found(admin_client, test_student, test_section):
    """Try to register to a non-existent academic year."""
    payload = {
        "student_id": test_student.id,
        "section_id": test_section.id,
        "academic_year_id": 9999
    }

    response = admin_client.post(
        '/enrollment/register',
        json=payload
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'academic year not found'

def test_register_enrollment_academic_year_not_open(admin_client, test_student, test_section, test_academic_year):
    """Try to register to an academic year that is not OPEN."""
    # Change status to CLOSED
    test_academic_year.status = AcademicYearStatus.CLOSED
    db.session.commit()

    payload = {
        "student_id": test_student.id,
        "section_id": test_section.id,
        "academic_year_id": test_academic_year.id
    }

    response = admin_client.post(
        '/enrollment/register',
        json=payload
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'academic year not open for registration'

def test_register_enrollment_section_full(admin_client, test_section, test_academic_year):
    """Try to register when the section has reached its maximum capacity."""
    # test_section capacity is 2. Let's create 2 students and enroll them.
    s1 = Student(first_name="S1", last_name="L1", email="s1@example.com")
    s2 = Student(first_name="S2", last_name="L2", email="s2@example.com")
    s3 = Student(first_name="S3", last_name="L3", email="s3@example.com") # This one will fail
    db.session.add_all([s1, s2, s3])
    db.session.commit()

    en1 = Enrollment(student_id=s1.id, section_id=test_section.id, academic_year_id=test_academic_year.id, estado=EnrollmentStatus.ACTIVE)
    en2 = Enrollment(student_id=s2.id, section_id=test_section.id, academic_year_id=test_academic_year.id, estado=EnrollmentStatus.ACTIVE)
    db.session.add_all([en1, en2])
    db.session.commit()

    payload = {
        "student_id": s3.id,
        "section_id": test_section.id,
        "academic_year_id": test_academic_year.id
    }

    response = admin_client.post(
        '/enrollment/register',
        json=payload
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'section full'
    assert data['capacity'] == 2

def test_register_enrollment_duplicate(admin_client, test_student, test_section, test_academic_year):
    """Try to register a student who is already actively enrolled in the same year."""
    # Create existing enrollment
    en = Enrollment(student_id=test_student.id, section_id=test_section.id, academic_year_id=test_academic_year.id, estado=EnrollmentStatus.ACTIVE)
    db.session.add(en)
    db.session.commit()

    # Try to register again
    # Use a different section just to prove it checks academic_year + student, but we can use the same
    payload = {
        "student_id": test_student.id,
        "section_id": test_section.id,
        "academic_year_id": test_academic_year.id
    }

    response = admin_client.post(
        '/enrollment/register',
        json=payload
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'student already enrolled in this academic year'
    assert 'enrollment_id' in data

def test_section_students_success(admin_client, test_student, test_section, test_academic_year):
    """Happy path: get students enrolled in a section."""
    en = Enrollment(student_id=test_student.id, section_id=test_section.id, academic_year_id=test_academic_year.id, estado=EnrollmentStatus.ACTIVE)
    db.session.add(en)
    db.session.commit()

    response = admin_client.get(f'/enrollment/section/{test_section.id}/students')

    assert response.status_code == 200
    data = response.get_json()
    assert data['section_id'] == test_section.id
    assert len(data['students']) == 1

    student_data = data['students'][0]
    assert student_data['student_id'] == test_student.id
    assert student_data['first_name'] == test_student.first_name
    assert student_data['last_name'] == test_student.last_name
    assert student_data['enrollment_id'] == en.id

def test_section_students_with_year_filter(admin_client, test_student, test_section, test_academic_year):
    """Filter students by academic year ID."""
    en = Enrollment(student_id=test_student.id, section_id=test_section.id, academic_year_id=test_academic_year.id, estado=EnrollmentStatus.ACTIVE)
    db.session.add(en)
    db.session.commit()

    # Correct year
    response1 = admin_client.get(f'/enrollment/section/{test_section.id}/students?year_id={test_academic_year.id}')
    assert response1.status_code == 200
    assert len(response1.get_json()['students']) == 1

    # Incorrect year
    response2 = admin_client.get(f'/enrollment/section/{test_section.id}/students?year_id=9999')
    assert response2.status_code == 200
    assert len(response2.get_json()['students']) == 0

def test_section_students_section_not_found(admin_client):
    """Get students for a non-existent section."""
    response = admin_client.get('/enrollment/section/9999/students')
    assert response.status_code == 404

def test_student_history_success(admin_client, test_student, test_section, test_academic_year):
    """Happy path: get enrollment history for a student."""
    en = Enrollment(student_id=test_student.id, section_id=test_section.id, academic_year_id=test_academic_year.id, estado=EnrollmentStatus.ACTIVE)
    db.session.add(en)
    db.session.commit()

    response = admin_client.get(f'/enrollment/history/student/{test_student.id}')

    assert response.status_code == 200
    data = response.get_json()
    assert data['student_id'] == test_student.id
    assert len(data['history']) == 1

    history_data = data['history'][0]
    assert history_data['enrollment_id'] == en.id
    assert history_data['section'] == test_section.nombre
    assert history_data['level'] == test_section.level.nombre
    assert history_data['academic_year'] == test_academic_year.nombre
    assert history_data['estado'] == EnrollmentStatus.ACTIVE.name

def test_student_history_student_not_found(admin_client):
    """Get history for a non-existent student."""
    response = admin_client.get('/enrollment/history/student/9999')
    assert response.status_code == 404
