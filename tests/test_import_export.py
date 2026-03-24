import io
from werkzeug.security import generate_password_hash


def test_import_students_and_export(auth_client, app):
    from extensions import db
    from models import Student

    client = auth_client
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


def test_import_subjects_and_grades_and_export(auth_client, app):
    from extensions import db
    from models import Subject, Student

    client = auth_client
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
