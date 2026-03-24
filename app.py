from flask import (
    Flask,
)
import os
from dotenv import load_dotenv

import extensions
import models
from app_auth_loader import register_login_user_loader
from app_blueprints import register_app_blueprints
from app_bootstrap import initialize_schema_and_seed
from app_config_loader import load_app_config
from app_config_overrides import apply_config_overrides_and_validate
from app_context_processors import register_context_processors
from app_extensions_setup import initialize_extensions
from app_observability import configure_observability
from app_storage_config import configure_storage_settings


# Load environment variables from a .env file when present (dev convenience)
def create_app():
    load_dotenv()
    app = Flask(__name__)
    load_app_config(app)
    apply_config_overrides_and_validate(app)

    configure_observability(app)
    register_context_processors(app)
    configure_storage_settings(app)

    initialize_extensions(
        app,
        extensions.db,
        extensions.csrf,
        extensions.migrate,
        extensions.login_manager,
    )
    register_login_user_loader(extensions.login_manager, extensions.db, models.User)

    initialize_schema_and_seed(app)
    register_app_blueprints(app)
    return app


if __name__ == "__main__":
    # Enable debug only when FLASK_ENV is set to 'development'
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app = create_app()
    app.run(host="0.0.0.0", debug=debug_mode)
