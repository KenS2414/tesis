import os
import subprocess
import sys


def test_create_app_registers_core_routes():
    from app import create_app

    factory_app = create_app()
    routes = {rule.rule for rule in factory_app.url_map.iter_rules()}

    assert "/" in routes
    assert "/login" in routes
    assert "/dashboard" in routes
    assert "/health" in routes
    assert "/students/" in routes
    assert "/payments" in routes
    assert "/admin/payments" in routes


def test_flask_cli_resolves_factory_app():
    env = os.environ.copy()
    env.setdefault("SECRET_KEY", "test-cli-secret")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")

    result = subprocess.run(
        [sys.executable, "-m", "flask", "--app", "app:create_app", "routes"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "/login" in result.stdout


def test_app_module_exposes_factory_without_legacy_contract():
    import app as app_module

    assert hasattr(app_module, "create_app")
    assert not hasattr(app_module, "__all__")
    assert not hasattr(app_module, "app")
    assert not hasattr(app_module, "db")
    assert not hasattr(app_module, "User")
    assert not hasattr(app_module, "Student")
    assert not hasattr(app_module, "Payment")
    assert not hasattr(app_module, "upload_bytes_to_s3")
    assert not hasattr(app_module, "get_presigned_url")
