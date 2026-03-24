import os


def apply_config_overrides_and_validate(app):
    # Allow environment overrides for critical settings.
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.environ.get("DATABASE_URL", "sqlite:///app.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("ASSET_VERSION", os.environ.get("ASSET_VERSION", "6"))
    app.config.setdefault("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)

    # In production ensure SECRET_KEY is set.
    if os.environ.get("FLASK_ENV") == "production" and not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY environment variable not set. Set SECRET_KEY before running the app in production."
        )
