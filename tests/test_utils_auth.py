import pytest
from flask import Flask, jsonify
from unittest.mock import patch, MagicMock
from utils.auth import requires_roles
from models import UserRole

# Define a minimal test app
@pytest.fixture
def dummy_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    # Register a dummy auth_bp.login route for url_for to work
    @app.route('/login', endpoint='auth_bp.login')
    def login():
        return "Login Page"

    # Define routes protected by requires_roles
    @app.route('/student-only')
    @requires_roles('Student')
    def student_only():
        return jsonify(message="Success")

    @app.route('/teacher-admin')
    @requires_roles('Teacher', 'Admin')
    def teacher_admin():
        return jsonify(message="Success")

    return app


@pytest.fixture
def dummy_client(dummy_app):
    return dummy_app.test_client()


def test_requires_roles_unauthenticated(dummy_client):
    """Test that an unauthenticated user is redirected to auth_bp.login."""
    with patch("utils.auth.current_user") as mock_user:
        mock_user.is_authenticated = False

        response = dummy_client.get('/student-only')

        # Check redirection
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_requires_roles_authorized(dummy_client):
    """Test that an authenticated user with the required role is allowed."""
    with patch("utils.auth.current_user") as mock_user:
        mock_user.is_authenticated = True
        mock_user.role = 'Student'

        response = dummy_client.get('/student-only')

        assert response.status_code == 200
        assert response.json == {"message": "Success"}


def test_requires_roles_unauthorized(dummy_client):
    """Test that an authenticated user without the required role gets a 403."""
    with patch("utils.auth.current_user") as mock_user:
        mock_user.is_authenticated = True
        mock_user.role = 'Student'

        # Endpoint requires Teacher or Admin
        response = dummy_client.get('/teacher-admin')

        assert response.status_code == 403


def test_requires_roles_superadmin_override(dummy_client):
    """Test that a superadmin can access any route, regardless of required roles."""
    with patch("utils.auth.current_user") as mock_user:
        mock_user.is_authenticated = True
        # super_admin check in auth.py uses UserRole.SUPER_ADMIN explicitly
        mock_user.role = UserRole.SUPER_ADMIN

        # Endpoint requires Student, but SUPER_ADMIN should be allowed
        response = dummy_client.get('/student-only')

        assert response.status_code == 200
        assert response.json == {"message": "Success"}

        # Endpoint requires Teacher or Admin, but SUPER_ADMIN should be allowed
        response2 = dummy_client.get('/teacher-admin')
        assert response2.status_code == 200
        assert response2.json == {"message": "Success"}
