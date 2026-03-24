from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models import User
import os
import secrets
import sys


def init_db(flask_app=None):
    app = flask_app or create_app()
    with app.app_context():
        # When running under pytest or test runners, ensure a fresh schema to
        # avoid leftover sqlite files/tables with outdated columns.
        if 'pytest' in sys.modules or os.environ.get('PYTEST_CURRENT_TEST'):
            try:
                db.drop_all()
            except Exception:
                pass
        db.create_all()
        admin = User.query.filter_by(username="admin").first()
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if not admin:
            if not admin_password:
                # generate a reasonably strong random password and show it once
                admin_password = secrets.token_urlsafe(10)
                print(
                    "Generada contraseña aleatoria para 'admin' (guárdala):",
                    admin_password,
                )
            admin = User(
                username="admin",
                password_hash=generate_password_hash(admin_password),
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario 'admin' creado.")
        else:
            # if ADMIN_PASSWORD provided, update existing admin password to match (useful for tests)
            if admin_password:
                admin.password_hash = generate_password_hash(admin_password)
                db.session.commit()
                print("Password del usuario 'admin' actualizado desde ADMIN_PASSWORD.")
            else:
                print("Usuario 'admin' ya existe.")


if __name__ == "__main__":
    init_db()
