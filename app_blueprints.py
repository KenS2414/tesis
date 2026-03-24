from auth_bp import auth_bp
from finance_bp import finance_bp
from main_bp import main_bp
from payments_admin_bp import payments_admin_bp
from payments_student_bp import payments_student_bp
from students_bp import students_bp
from system_bp import system_bp


def register_app_blueprints(flask_app):
    ordered_blueprints = [
        main_bp,
        system_bp,
        auth_bp,
        students_bp,
        finance_bp,
        payments_admin_bp,
        payments_student_bp,
    ]
    for bp in ordered_blueprints:
        try:
            flask_app.register_blueprint(bp)
        except Exception:
            # keep startup resilient in tests/import-order edge cases
            pass
    try:
        from enrollment_bp import enrollment_bp

        flask_app.register_blueprint(enrollment_bp)
    except Exception:
        pass
