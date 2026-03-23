"""Decorator for admin-only access."""

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.dashboard'))

        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Decorator to require specific role(s)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.is_admin:
                return f(*args, **kwargs)

            if current_user.role and current_user.role.name in roles:
                return f(*args, **kwargs)

            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.dashboard'))

        return decorated_function
    return decorator


def permission_required(*permissions):
    """Decorator to require specific permission(s)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.is_admin:
                return f(*args, **kwargs)

            if current_user.role:
                for permission in permissions:
                    if current_user.role.has_permission(permission):
                        return f(*args, **kwargs)

            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.dashboard'))

        return decorated_function
    return decorator