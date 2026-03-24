from app import create_app

app = create_app()

# Expose `app` and `db` for the Flask CLI and Flask-Migrate.
# Usage examples:
#   $env:FLASK_APP = "app:create_app"; python -m flask db init
#   $env:FLASK_APP = "app:create_app"; python -m flask db migrate -m "init"
#   $env:FLASK_APP = "app:create_app"; python -m flask db upgrade
# También funciona la compatibilidad histórica con: $env:FLASK_APP = "app.py"

if __name__ == "__main__":
    app.run()
