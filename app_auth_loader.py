from sqlalchemy.exc import OperationalError


def register_login_user_loader(login_manager, db, user_model):
    @login_manager.user_loader
    def load_user(user_id):
        # use Session.get to avoid SQLAlchemy Query.get() deprecation
        try:
            return db.session.get(user_model, int(user_id))
        except OperationalError as e:
            if "no such table" in str(e).lower():
                # Auto-recover local sqlite schema if DB file was recreated while server is running.
                db.create_all()
                return db.session.get(user_model, int(user_id))
            raise

    return load_user
