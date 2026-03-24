import io
from werkzeug.security import generate_password_hash


def test_gradebook_report(super_admin_client, app, sample_subjects, sample_students):
    from extensions import db
    from models import Grade

    # create some grades for subject 1
    s = sample_subjects[0]
    students = sample_students
    g1 = Grade(student_id=students[0].id, subject_id=s.id, score=85.5, comment='Good')
    g2 = Grade(student_id=students[1].id, subject_id=s.id, score=90, comment='Excellent')
    db.session.add_all([g1, g2])
    db.session.commit()

    client = super_admin_client
    resp = client.get(f"/students/reports/gradebook?subject_id={s.id}")
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type') == 'application/pdf'
    assert len(resp.data) > 0


def test_payment_report(super_admin_client, app, sample_students):
    from extensions import db
    from models import Payment

    student = sample_students[0]
    p = Payment(student_id=student.id, amount=123.45, status='approved')
    db.session.add(p)
    db.session.commit()

    client = super_admin_client
    resp = client.get(f"/admin/payments/{p.id}/report")
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type') == 'application/pdf'
    assert len(resp.data) > 0
