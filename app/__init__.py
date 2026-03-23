"""
TaskFlow PSA - Professional Services Automation Platform
A modern, AI-powered PSA system for IT service providers.
"""

from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

def create_app(config_class=None):
    """Application factory pattern."""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///taskflow.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = os.environ.get('FLASK_ENV') == 'development'

    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 1025))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

    # Stripe configuration
    app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY')
    app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.tickets.routes import tickets_bp
    from app.projects.routes import projects_bp
    from app.crm.routes import crm_bp
    from app.billing.routes import billing_bp
    from app.integrations.routes import integrations_bp
    from app.ai_assistant.routes import ai_bp
    from app.api.routes import api_bp
    from app.admin.routes import admin_bp
    from app.notifications.routes import notifications_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(tickets_bp, url_prefix='/tickets')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(crm_bp, url_prefix='/crm')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(integrations_bp, url_prefix='/integrations')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Template filters
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        if value is None:
            return ""
        return value.strftime(format)

    @app.template_filter('date')
    def format_date(value, format='%Y-%m-%d'):
        if value is None:
            return ""
        return value.strftime(format)

    @app.template_filter('currency')
    def format_currency(value):
        if value is None:
            return "$0.00"
        return f"${value:,.2f}"

    @app.template_filter('status_badge')
    def status_badge(status):
        badges = {
            'open': 'bg-blue-100 text-blue-800',
            'in_progress': 'bg-yellow-100 text-yellow-800',
            'pending': 'bg-purple-100 text-purple-800',
            'resolved': 'bg-green-100 text-green-800',
            'closed': 'bg-gray-100 text-gray-800',
            'cancelled': 'bg-red-100 text-red-800',
        }
        return badges.get(status, 'bg-gray-100 text-gray-800')

    @app.template_filter('priority_badge')
    def priority_badge(priority):
        badges = {
            'critical': 'bg-red-100 text-red-800 border-red-200',
            'high': 'bg-orange-100 text-orange-800 border-orange-200',
            'medium': 'bg-yellow-100 text-yellow-800 border-yellow-200',
            'low': 'bg-green-100 text-green-800 border-green-200',
        }
        return badges.get(priority, 'bg-gray-100 text-gray-800')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Context processor for global template variables
    @app.context_processor
    def inject_globals():
        return dict(
            app_name=os.environ.get('APP_NAME', 'TaskFlow PSA'),
            current_year=datetime.now().year,
            enable_ai=os.environ.get('ENABLE_AI_FEATURES', 'true').lower() == 'true',
            enable_integrations=os.environ.get('ENABLE_INTEGRATIONS', 'true').lower() == 'true',
            stripe_publishable_key=app.config.get('STRIPE_PUBLISHABLE_KEY')
        )

    # Shell context for flask shell
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Organization, Ticket, Project, Client, Contact
        return {
            'db': db,
            'User': User,
            'Organization': Organization,
            'Ticket': Ticket,
            'Project': Project,
            'Client': Client,
            'Contact': Contact,
        }

    return app