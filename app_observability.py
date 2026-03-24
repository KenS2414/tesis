import logging
import os
from logging.handlers import RotatingFileHandler


def configure_observability(app):
    """Configura logging base, Sentry y logging a archivo opcional."""
    # Basic logging configuration for production-friendly output
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    )
    handler.setLevel(logging.INFO)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Initialize Sentry if configured
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration

            sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration(), sentry_logging],
                traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
                environment=os.environ.get("FLASK_ENV", "development"),
            )
            app.logger.info("Sentry initialized")
        except Exception:
            app.logger.exception("Failed to initialize Sentry")

    # Optional: also log to a rotating file if requested via env var
    if os.environ.get("LOG_TO_FILE", "0").lower() in ("1", "true", "yes"):
        log_file = os.environ.get("LOG_FILE", "logs/app.log")
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
            file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.info(f"Logging to file enabled: {log_file}")
        except Exception:
            app.logger.exception("Failed to initialize file logging")
