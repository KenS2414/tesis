from extensions import db
from models import Student, Subject, Grade


def test_student_promotes_when_passing_all_subjects_of_year(super_admin_client, app):
    student = Student(first_name='Promo', last_name='Student', email='promo@example.com', current_year_group='1er Año')
    s1 = Subject(name='Matematica I', code='MAT101', year_group='1er Año')
    s2 = Subject(name='Historia I', code='HIS101', year_group='1er Año')
    db.session.add_all([student, s1, s2])
    db.session.commit()

    resp1 = super_admin_client.post(
        f'/students/{student.id}/add-grade',
        data={'subject_id': s1.id, 'score': '16', 'term': '2026-1'},
        follow_redirects=True,
    )
    assert resp1.status_code == 200
    st1 = db.session.get(Student, student.id)
    assert st1.current_year_group == '1er Año'

    resp2 = super_admin_client.post(
        f'/students/{student.id}/add-grade',
        data={'subject_id': s2.id, 'score': '15', 'term': '2026-1'},
        follow_redirects=True,
    )
    assert resp2.status_code == 200
    st2 = db.session.get(Student, student.id)
    assert st2.current_year_group == '2do Año'


def test_student_does_not_promote_with_failing_subject(super_admin_client, app):
    student = Student(first_name='NoPromo', last_name='Student', email='nopromo@example.com', current_year_group='1er Año')
    s1 = Subject(name='Biologia I', code='BIO101', year_group='1er Año')
    s2 = Subject(name='Castellano I', code='CAS101', year_group='1er Año')
    db.session.add_all([student, s1, s2])
    db.session.commit()

    super_admin_client.post(
        f'/students/{student.id}/add-grade',
        data={'subject_id': s1.id, 'score': '16', 'term': '2026-1'},
        follow_redirects=True,
    )
    super_admin_client.post(
        f'/students/{student.id}/add-grade',
        data={'subject_id': s2.id, 'score': '8', 'term': '2026-1'},
        follow_redirects=True,
    )

    st = db.session.get(Student, student.id)
    assert st.current_year_group == '1er Año'
    assert Grade.query.filter_by(student_id=student.id).count() == 2
