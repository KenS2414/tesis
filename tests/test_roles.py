import pytest
from werkzeug.security import generate_password_hash


def test_admin_can_change_role(super_admin_client, app):
    from extensions import db
    from models import User

    # create a regular user to change
    u = User(username="target_user", password_hash=generate_password_hash("pwd"), role="user")
    db.session.add(u)
    db.session.commit()

    client = super_admin_client
    resp = client.post(f"/students/users/{u.id}/role", data={"role": "teacher"}, follow_redirects=True)
    assert resp.status_code in (200, 302)

    u2 = db.session.get(User, u.id)
    assert u2.role == "teacher"


def test_teacher_cannot_change_role(client, teacher_user, app):
    from extensions import db
    from models import User

    # create a regular user to attempt to change
    u = User(username="target2", password_hash=generate_password_hash("pwd"), role="user")
    db.session.add(u)
    db.session.commit()

    # login as teacher
    resp = client.post("/login", data={"username": "teacher1", "password": "teacherpass"}, follow_redirects=True)
    assert resp.status_code in (200, 302)

    # attempt to change role -> should be forbidden (403)
    resp2 = client.post(f"/students/users/{u.id}/role", data={"role": "admin"})
    assert resp2.status_code == 403
