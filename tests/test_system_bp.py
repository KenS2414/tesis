import pytest
from unittest.mock import patch
import os

def test_health_ok(client):
    """Test /health returns 200 when DB is ok."""
    with patch("system_bp.db.session.execute") as mock_execute:
        # Mocking the execute to return a simple result
        mock_execute.return_value = True

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json == {"status": "ok", "db": True}

def test_health_db_failure(client):
    """Test /health returns 503 when DB query fails."""
    with patch("system_bp.db.session.execute") as mock_execute:
        mock_execute.side_effect = Exception("DB connection failed")

        response = client.get("/health")

        assert response.status_code == 503
        assert response.json == {"status": "degraded", "db": False}

def test_ready_ok(client, app, monkeypatch):
    """Test /ready returns 200 when DB and S3 are ok."""
    with patch("system_bp.db.session.execute") as mock_execute, \
         patch("utils.aws.check_s3_connection") as mock_s3_check:

        # Configure app to trigger S3 check
        app.config["S3_BUCKET"] = "test-bucket"
        monkeypatch.setenv("FLASK_ENV", "production")

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json == {"status": "ready", "db": True, "s3": True}

def test_ready_db_failure(client, app):
    """Test /ready returns 503 when DB fails."""
    with patch("system_bp.db.session.execute") as mock_execute:
        mock_execute.side_effect = Exception("DB connection failed")

        # Configure app so S3 check is not configured
        app.config["S3_BUCKET"] = None

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json == {"status": "not_ready", "db": False, "s3": "not_configured"}

def test_ready_s3_failure(client, app, monkeypatch):
    """Test /ready returns 503 when S3 fails."""
    with patch("system_bp.db.session.execute") as mock_execute, \
         patch("utils.aws.check_s3_connection") as mock_s3_check:

        # Configure app to trigger S3 check
        app.config["S3_BUCKET"] = "test-bucket"
        monkeypatch.setenv("FLASK_ENV", "production")

        # S3 check fails
        mock_s3_check.side_effect = Exception("S3 connection failed")

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json == {"status": "not_ready", "db": True, "s3": False}

def test_ready_no_s3_configured(client, app):
    """Test /ready returns 200 when DB is ok and S3 is not configured."""
    with patch("system_bp.db.session.execute") as mock_execute:

        app.config["S3_BUCKET"] = None

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json == {"status": "ready", "db": True, "s3": "not_configured"}
