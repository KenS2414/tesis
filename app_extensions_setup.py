def initialize_extensions(app, db, csrf, migrate, login_manager):
    # Bind extensions to app in one place to keep app.py focused on composition.
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth_bp.login"
