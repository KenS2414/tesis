from extensions import db
from models import Student, Subject, Grade


def test_student_promotes_when_passing_all_subjects_of_year(super_admin_client, app):
    student = Student(first_name='Promo', last_name='Student', email='promo@example.com', current_year_group='1er Año')
    s1 = Subject(name='Matematica I', code='MAT101', year_group='1er Año')
    s2 = Subject(name='Historia I', code='HIS101', year_group='1er Año')
    db.session.add_all([student, s1, s2])
    db.session.commit()

    resp1 = super_admin_client.post(
        f'/teacher/student/{student.id}/subject/{s1.id}/grades',
        data={'score_Nota 1': '16'},
        follow_redirects=True,
    )
    assert resp1.status_code == 200
    st1 = db.session.get(Student, student.id)
    assert st1.current_year_group == '1er Año'

    resp2 = super_admin_client.post(
        f'/teacher/student/{student.id}/subject/{s2.id}/grades',
        data={'score_Nota 1': '15'},
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
        f'/teacher/student/{student.id}/subject/{s1.id}/grades',
        data={'score_Nota 1': '16'},
        follow_redirects=True,
    )
    super_admin_client.post(
        f'/teacher/student/{student.id}/subject/{s2.id}/grades',
        data={'score_Nota 1': '8'},
        follow_redirects=True,
    )

    st = db.session.get(Student, student.id)
    assert st.current_year_group == '1er Año'
    # There are 8 grades because 4 grades are created per subject when updated using POST, but only 2 of them has `value != None`
    assert Grade.query.filter_by(student_id=student.id).filter(Grade.value != None).count() == 2

from teachers_bp import _promote_student_if_ready

def test_unit_promote_student_success(app):
    with app.app_context():
        student = Student(first_name='UnitPromo', last_name='Student', email='unitpromo@example.com', current_year_group='1er Año')
        s1 = Subject(name='Matematica I Unit', code='MAT101U', year_group='1er Año')
        s2 = Subject(name='Historia I Unit', code='HIS101U', year_group='1er Año')
        db.session.add_all([student, s1, s2])
        db.session.commit()

        g1 = Grade(student_id=student.id, subject_id=s1.id, term='Nota 1', value=15.0)
        g2 = Grade(student_id=student.id, subject_id=s2.id, term='Nota 1', value=12.0)
        db.session.add_all([g1, g2])
        db.session.commit()

        promoted_to = _promote_student_if_ready(student)

        assert promoted_to == '2do Año'
        assert student.current_year_group == '2do Año'

def test_unit_promote_student_final_year(app):
    with app.app_context():
        student = Student(first_name='FinalYear', last_name='Student', email='finalyear@example.com', current_year_group='5to Año')
        s1 = Subject(name='Matematica V Unit', code='MAT501U', year_group='5to Año')
        db.session.add_all([student, s1])
        db.session.commit()

        g1 = Grade(student_id=student.id, subject_id=s1.id, term='Nota 1', value=15.0)
        db.session.add(g1)
        db.session.commit()

        promoted_to = _promote_student_if_ready(student)

        assert promoted_to is None
        assert student.current_year_group == '5to Año'

def test_unit_promote_student_failing_grades(app):
    with app.app_context():
        student = Student(first_name='Failing', last_name='Student', email='failing@example.com', current_year_group='1er Año')
        s1 = Subject(name='Matematica I Fail', code='MAT101F', year_group='1er Año')
        s2 = Subject(name='Historia I Fail', code='HIS101F', year_group='1er Año')
        db.session.add_all([student, s1, s2])
        db.session.commit()

        g1 = Grade(student_id=student.id, subject_id=s1.id, term='Nota 1', value=15.0)
        g2 = Grade(student_id=student.id, subject_id=s2.id, term='Nota 1', value=9.0) # Failing grade
        db.session.add_all([g1, g2])
        db.session.commit()

        promoted_to = _promote_student_if_ready(student)

        assert promoted_to is None
        assert student.current_year_group == '1er Año'

def test_unit_promote_student_incomplete_grades(app):
    with app.app_context():
        student = Student(first_name='Incomplete', last_name='Student', email='incomplete@example.com', current_year_group='1er Año')
        s1 = Subject(name='Matematica I Inc', code='MAT101I', year_group='1er Año')
        s2 = Subject(name='Historia I Inc', code='HIS101I', year_group='1er Año')
        db.session.add_all([student, s1, s2])
        db.session.commit()

        g1 = Grade(student_id=student.id, subject_id=s1.id, term='Nota 1', value=15.0)
        # s2 is missing a grade
        db.session.add(g1)
        db.session.commit()

        promoted_to = _promote_student_if_ready(student)

        assert promoted_to is None
        assert student.current_year_group == '1er Año'
