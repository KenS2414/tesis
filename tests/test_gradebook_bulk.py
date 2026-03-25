import json
from werkzeug.security import generate_password_hash


def test_gradebook_bulk_update_and_export(super_admin_client, app, sample_subjects, sample_students):
    from extensions import db
    from models import Grade

    subj = sample_subjects[0]
    students = sample_students
    client = super_admin_client

    payload = {
        'grades': [
            {'student_id': students[0].id, 'score': 75, 'comment': 'Needs improvement', 'term': '2021-1'},
            {'student_id': students[1].id, 'score': 88.5, 'comment': 'Good', 'term': '2021-1'},
        ]
    }
    resp = client.post(f'/teacher/gradebook/{subj.id}/bulk_update', data=json.dumps(payload), content_type='application/json')
    assert resp.status_code in (200,)
    data = resp.get_json()
    assert data.get('status') == 'ok'

    # verify grades in DB
    g1 = Grade.query.filter_by(student_id=students[0].id, subject_id=subj.id).first()
    assert g1 is not None and float(g1.score) == 75.0

    # export csv
    resp2 = client.get(f'/teacher/gradebook/{subj.id}.csv')
    assert resp2.status_code == 200
    assert resp2.headers.get('Content-Type') == 'text/csv'
    assert b'student_id' in resp2.data
