from models import User


def test_admin_can_create_teacher_user(super_admin_client, app):
    resp = super_admin_client.post(
        "/students/users/new-staff",
        data={"username": "teacher_new", "password": "teacherpass123", "confirm_password": "teacherpass123", "role": "teacher"},
        follow_redirects=True,
    )

    assert resp.status_code == 200

    with app.app_context():
        created = User.query.filter_by(username="teacher_new").first()
        assert created is not None
        assert created.role == "teacher"


def test_admin_cannot_create_duplicate_teacher_user(super_admin_client, app):
    super_admin_client.post(
        "/students/users/new-staff",
        data={"username": "teacher_dup", "password": "pass1", "confirm_password": "pass1", "role": "teacher"},
        follow_redirects=True,
    )

    resp = super_admin_client.post(
        "/students/users/new-staff",
        data={"username": "teacher_dup", "password": "pass2", "confirm_password": "pass2", "role": "teacher"},
        follow_redirects=True,
    )

    assert resp.status_code == 200

    with app.app_context():
        users = User.query.filter_by(username="teacher_dup").all()
        assert len(users) == 1
