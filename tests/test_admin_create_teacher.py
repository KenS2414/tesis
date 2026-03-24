from models import User


def test_admin_can_create_teacher_user(admin_client, app):
    resp = admin_client.post(
        "/students/users/new-teacher",
        data={"username": "teacher_new", "password": "teacherpass123"},
        follow_redirects=True,
    )

    assert resp.status_code == 200

    with app.app_context():
        created = User.query.filter_by(username="teacher_new").first()
        assert created is not None
        assert created.role == "teacher"


def test_admin_cannot_create_duplicate_teacher_user(admin_client, app):
    admin_client.post(
        "/students/users/new-teacher",
        data={"username": "teacher_dup", "password": "pass1"},
        follow_redirects=True,
    )

    resp = admin_client.post(
        "/students/users/new-teacher",
        data={"username": "teacher_dup", "password": "pass2"},
        follow_redirects=True,
    )

    assert resp.status_code == 200

    with app.app_context():
        users = User.query.filter_by(username="teacher_dup").all()
        assert len(users) == 1
