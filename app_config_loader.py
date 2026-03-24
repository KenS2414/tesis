import os


def load_app_config(app):
    # Load configuration from config.py (or override via APP_CONFIG env var).
    config_name = os.environ.get("APP_CONFIG")
    if config_name:
        app.config.from_object(config_name)
    elif os.environ.get("FLASK_ENV") == "production":
        app.config.from_object("config.ProductionConfig")
    else:
        app.config.from_object("config.DevelopmentConfig")
