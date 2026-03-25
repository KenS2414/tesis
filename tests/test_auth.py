def test_logout_authenticated_user(super_admin_client):
    # The fixture logs the user in, so we should be authenticated

    # 1. Accessing a protected route should work (status 200)
    resp = super_admin_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 200

    # Verify session has the user before logout
    with super_admin_client.session_transaction() as sess:
        assert "_user_id" in sess

    # 2. Call logout
    resp = super_admin_client.get("/logout", follow_redirects=True)

    # Verify the redirect completed successfully (status code 200 after redirect)
    assert resp.status_code == 200

    # Verify flash message in response
    assert b"Sesi\xc3\xb3n cerrada." in resp.data

    # Verify session internal state has been cleared
    with super_admin_client.session_transaction() as sess:
        assert "_user_id" not in sess

    # 3. Accessing a protected route again should now redirect to login
    resp = super_admin_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")

def test_logout_unauthenticated_user(client):
    # Unauthenticated user trying to access /logout
    resp = client.get("/logout", follow_redirects=False)

    # Should be redirected to the login page due to @login_required
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")

def test_logout_teacher_user(teacher_client):
    # The fixture logs the teacher in, so we should be authenticated
    resp = teacher_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 200

    # Verify session has the user before logout
    with teacher_client.session_transaction() as sess:
        assert "_user_id" in sess

    # Call logout
    resp = teacher_client.get("/logout", follow_redirects=True)

    # Verify the redirect completed successfully (status code 200 after redirect)
    assert resp.status_code == 200

    # Verify flash message in response
    assert b"Sesi\xc3\xb3n cerrada." in resp.data

    # Verify session internal state has been cleared
    with teacher_client.session_transaction() as sess:
        assert "_user_id" not in sess

    # Accessing a protected route again should now redirect to login
    resp = teacher_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")
