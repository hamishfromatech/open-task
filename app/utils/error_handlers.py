"""Error handlers for the application."""

from flask import render_template
from app import app


@app.errorhandler(400)
def bad_request_error(error):
    """Handle 400 Bad Request errors."""
    return render_template('errors/400.html'), 400


@app.errorhandler(401)
def unauthorized_error(error):
    """Handle 401 Unauthorized errors."""
    return render_template('errors/401.html'), 401


@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 Forbidden errors."""
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found errors."""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error."""
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(503)
def service_unavailable_error(error):
    """Handle 503 Service Unavailable errors."""
    return render_template('errors/503.html'), 503