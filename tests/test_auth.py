def test_logout_authenticated_user(super_admin_client):
    # The fixture logs the user in, so we should be authenticated

    # 1. Accessing a protected route should work (status 200)
    resp = super_admin_client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 200

    # 2. Call logout
    resp = super_admin_client.get("/logout", follow_redirects=False)

    # Verify the redirect to the login page
    assert resp.status_code == 302
    assert "/login" in (resp.headers.get("Location") or "")

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
