from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from models import UserRole


def requires_roles(*roles):
    """Decorator to require user roles. If the user is not authenticated or
    doesn't have one of the required roles, abort with 403.
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth_bp.login'))
            current_role = getattr(current_user, 'role', None)
            if current_role == UserRole.SUPER_ADMIN:
                return f(*args, **kwargs)
            if current_role not in roles:
                abort(403)
            return f(*args, **kwargs)

        return wrapped

    return decorator
