import os

from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from extensions import db
from models import User, UserRole


def initialize_schema_and_seed(app):
    """Inicializa esquema local y usuario director para desarrollo."""
    try:
        with app.app_context():
            db.create_all()
            inspector = sa_inspect(db.engine)
            if 'subject' in inspector.get_table_names():
                subject_columns = {column['name'] for column in inspector.get_columns('subject')}
                if 'year_group' not in subject_columns:
                    db.session.execute(text('ALTER TABLE subject ADD COLUMN year_group VARCHAR(100)'))
                    db.session.commit()
            if 'student' in inspector.get_table_names():
                student_columns = {column['name'] for column in inspector.get_columns('student')}
                if 'current_year_group' not in student_columns:
                    db.session.execute(text('ALTER TABLE student ADD COLUMN current_year_group VARCHAR(100)'))
                    db.session.commit()
            if os.environ.get("FLASK_ENV") != "production":
                director_password = os.environ.get("DIRECTOR_PASSWORD", "admin")
                director_user = User.query.filter_by(username="director").first()
                if director_user is None:
                    director_user = User(
                        username="director",
                        password_hash=generate_password_hash(director_password),
                        role=UserRole.ADMIN,
                    )
                    db.session.add(director_user)
                else:
                    director_user.password_hash = generate_password_hash(director_password)
                    if director_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
                        director_user.role = UserRole.ADMIN
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    director_user = User.query.filter_by(username="director").first()
                    if director_user is not None:
                        director_user.password_hash = generate_password_hash(director_password)
                        if director_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
                            director_user.role = UserRole.ADMIN
                        db.session.commit()
    except Exception as e:
        app.logger.warning("No se pudo inicializar el esquema de base de datos: %s", e)
