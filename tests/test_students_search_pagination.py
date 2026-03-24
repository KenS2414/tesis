import pytest
from app import create_app
from extensions import db
from models import Student, User, Subject, Grade
from werkzeug.security import generate_password_hash


flask_app = create_app()


def test_students_search_and_pagination(tmp_path):
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.app_context():
        # reuse existing DB instance configured in app; reset schema for test
        db.drop_all()
        db.create_all()
        # create 25 students
        for i in range(25):
            s = Student(first_name=f"Name{i}", last_name=f"Last{i}", email=f"user{i}@example.com")
            db.session.add(s)
        # add a specific student to search
        s_search = Student(first_name="Carlos", last_name="Perez", email="carlos@example.com")
        db.session.add(s_search)
        db.session.commit()

        client = flask_app.test_client()
        # create and login a test user
        user = User(username='tester', password_hash=generate_password_hash('secret'), role='admin')
        db.session.add(user)
        db.session.commit()
        login_res = client.post('/login', data={'username': 'tester', 'password': 'secret'}, follow_redirects=True)
        assert login_res.status_code == 200
        # create a couple of subjects and attach grades to some students
        subj_math = Subject(name='Matemáticas', code='MATH')
        subj_hist = Subject(name='Historia', code='HIST')
        db.session.add_all([subj_math, subj_hist])
        db.session.commit()

        # assign grades for some students to Matemáticas
        # students 0..4 will have Math grades
        for i in range(5):
            g = Grade(student_id=i+1, subject_id=subj_math.id, score=75.0)
            db.session.add(g)
        db.session.commit()

        # page 1 should contain 10 items
        res = client.get('/students/?page=1')
        assert res.status_code == 200
        text = res.get_data(as_text=True)
        assert 'Página' in text or 'Pagina' in text

        # page 3 should exist (25+1 -> 26 total -> 3 pages)
        res = client.get('/students/?page=3')
        assert res.status_code == 200

        # search for 'Carlos'
        res = client.get('/students/?q=Carlos')
        assert res.status_code == 200
        assert b'Carlos' in res.data
        assert b'Perez' in res.data

        # filter by Matemáticas subject (should show students who have math grade)
        res = client.get(f'/students/?subject_id={subj_math.id}')
        assert res.status_code == 200
        text = res.get_data(as_text=True)
        # one of the students we added to math should be present
        assert 'Name0' in text or 'Name1' in text

        # combined filter: text + subject
        res = client.get(f'/students/?q=Name0&subject_id={subj_math.id}')
        assert res.status_code == 200
        text = res.get_data(as_text=True)
        assert 'Name0' in text

        # UI shows clear filters link
        assert 'Borrar filtros' in text
