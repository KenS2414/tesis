from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models import User, Subject, Student, Grade


flask_app = create_app()


def test_crud_subjects_and_grades():
    # configure app for testing (disable CSRF for form POSTs)
    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test-key"})
    client = flask_app.test_client()

    with flask_app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(username="admin", role="super_admin")
        admin.password_hash = generate_password_hash("pass")
        teacher = User(username="teacher", role="teacher")
        teacher.password_hash = generate_password_hash("pass")
        db.session.add_all([admin, teacher])
        db.session.commit()

        # Admin creates a subject
        client.post("/login", data={"username": "admin", "password": "pass"})
        resp = client.post("/students/subjects/new", data={"name": "Historia", "code": "HIST101"}, follow_redirects=True)
        assert resp.status_code == 200
        subj = Subject.query.filter_by(name="Historia").first()
        assert subj is not None

        # Admin edits the subject
        resp = client.post(f"/students/subjects/{subj.id}/edit", data={"name": "Historia Moderna", "code": "HIST201"}, follow_redirects=True)
        assert resp.status_code == 200
        db.session.expire(subj)
        assert db.session.get(Subject, subj.id).name == "Historia Moderna"

        # Create a student
        stu = Student(first_name="A", last_name="B", email="s@example.com")
        db.session.add(stu)
        db.session.commit()

        # Teacher adds a grade
        client.get("/logout")
        client.post("/login", data={"username": "teacher", "password": "pass"})
        resp = client.post(f"/teacher/{stu.id}/add-grade", data={"subject_id": subj.id, "score": 15, "term": "1"}, follow_redirects=True)
        assert resp.status_code == 200
        grade = Grade.query.filter_by(student_id=stu.id, subject_id=subj.id).first()
        assert grade is not None

        # Teacher edits the grade
        resp = client.post(f"/teacher/grades/{grade.id}/edit", data={"score": 18, "term": "1"}, follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(grade)
        assert float(grade.score) == 18.0

        # Teacher deletes the grade
        resp = client.post(f"/teacher/grades/{grade.id}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(Grade, grade.id) is None

        # Admin deletes the subject
        client.get("/logout")
        client.post("/login", data={"username": "admin", "password": "pass"})
        resp = client.post(f"/students/subjects/{subj.id}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(Subject, subj.id) is None

        db.drop_all()
