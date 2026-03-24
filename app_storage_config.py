import os


def configure_storage_settings(app):
    # Optional S3 settings; stored in app config to support runtime overrides in tests.
    app.config["S3_BUCKET"] = os.environ.get("S3_BUCKET")
    app.config["S3_REGION"] = os.environ.get("S3_REGION")
    app.config["S3_ENDPOINT"] = os.environ.get("S3_ENDPOINT")
