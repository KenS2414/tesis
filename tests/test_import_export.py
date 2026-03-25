import io
from werkzeug.security import generate_password_hash


def test_import_students_malformed_dob(super_admin_client, app):
    from models import Student

    client = super_admin_client

    # Create CSV content with a malformed date
    csv_content = b"first_name,last_name,email,dob\nJohn,Doe,john.malformed@example.com,invalid-date\n"
    csv_file = io.BytesIO(csv_content)

    data = {'file': (csv_file, 'students_malformed.csv'), 'type': 'students'}
    resp = client.post('/students/import', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert resp.status_code in (200, 302)

    # Verify the student was created but dob is None
    student = Student.query.filter_by(email='john.malformed@example.com').first()
    assert student is not None
    assert student.first_name == 'John'
    assert student.last_name == 'Doe'
    assert student.dob is None


def test_import_students_and_export(super_admin_client, app):
    from extensions import db
    from models import Student

    client = super_admin_client
    # upload students CSV
    with open('tests/fixtures/students_sample.csv', 'rb') as f:
        data = {'file': (f, 'students_sample.csv'), 'type': 'students'}
        resp = client.post('/students/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert resp.status_code in (200, 302)

    # export students
    resp2 = client.get('/students/export.csv?type=students')
    assert resp2.status_code == 200
    assert resp2.headers.get('Content-Type') == 'text/csv'
    assert b'first_name' in resp2.data


def test_import_subjects_and_grades_and_export(super_admin_client, app):
    from extensions import db
    from models import Subject, Student

    client = super_admin_client
    # import subjects
    with open('tests/fixtures/subjects_sample.csv', 'rb') as f:
        data = {'file': (f, 'subjects_sample.csv'), 'type': 'subjects'}
        resp = client.post('/students/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert resp.status_code in (200, 302)

    # import students first (needed for grades)
    with open('tests/fixtures/students_sample.csv', 'rb') as f:
        data = {'file': (f, 'students_sample.csv'), 'type': 'students'}
        client.post('/students/import', data=data, content_type='multipart/form-data', follow_redirects=True)

    # import grades
    with open('tests/fixtures/grades_sample.csv', 'rb') as f:
        data = {'file': (f, 'grades_sample.csv'), 'type': 'grades'}
        resp = client.post('/students/import', data=data, content_type='multipart/form-data', follow_redirects=True)
        assert resp.status_code in (200, 302)

    # export grades
    resp2 = client.get('/students/export.csv?type=grades')
    assert resp2.status_code == 200
    assert resp2.headers.get('Content-Type') == 'text/csv'
    assert b'student_email' in resp2.data

def test_export_gradebook_happy_path(teacher_client, teacher_user, app):
    from extensions import db
    from models import Subject, Student, Grade

    client = teacher_client

    # 1. Setup a subject owned by the teacher
    subj = Subject(name="Ciencias", code="SCI101", teacher_id=teacher_user.id)
    db.session.add(subj)
    db.session.commit()

    # 2. Setup a student and grade for the subject
    student = Student(first_name="Carlos", last_name="Santana", email="carlos@example.com", cedula="12345678")
    db.session.add(student)
    db.session.commit()

    grade = Grade(student_id=student.id, subject_id=subj.id, value=15.0)
    db.session.add(grade)
    db.session.commit()

    # 3. Request gradebook export
    resp = client.get(f'/teacher/gradebook/{subj.id}.csv')

    # 4. Verify successful response and headers
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type') == 'text/csv'

    # 5. Verify CSV content matches expected output
    content = resp.data.decode('utf-8')
    assert "student_id,first_name,last_name,email,score,comment,term" in content
    assert f"{student.id},Carlos,Santana,carlos@example.com,15.00,," in content


def test_export_gradebook_access_control(client, app):
    from extensions import db
    from models import Subject, User, UserRole
    from werkzeug.security import generate_password_hash

    # 1. Create a student user and log in
    student_user = User(username="student1", password_hash=generate_password_hash("studentpass"), role=UserRole.STUDENT)
    db.session.add(student_user)
    db.session.commit()

    client.post("/login", data={"username": "student1", "password": "studentpass"}, follow_redirects=True)

    # 2. Setup a subject
    subj = Subject(name="Geografia", code="GEO101")
    db.session.add(subj)
    db.session.commit()

    # 3. Attempt to export gradebook as a student
    resp = client.get(f'/teacher/gradebook/{subj.id}.csv')

    # 4. Assert access is denied (403 Forbidden or redirect)
    assert resp.status_code in (403, 302)
