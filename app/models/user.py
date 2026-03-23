"""User and authentication models."""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Role(db.Model):
    """User roles for RBAC."""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'

    def has_permission(self, permission):
        return permission in self.permissions


class User(db.Model, UserMixin):
    """User model for authentication and profile."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)

    # Profile information
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    job_title = db.Column(db.String(100))

    # Settings
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    email_notifications = db.Column(db.Boolean, default=True)
    dark_mode = db.Column(db.Boolean, default=False)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_staff = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime)

    # Relationships
    organization = db.relationship('Organization', backref='members')
    tickets_assigned = db.relationship('Ticket', backref='assignee', foreign_keys='Ticket.assigned_to')
    tickets_created = db.relationship('Ticket', backref='creator', foreign_keys='Ticket.created_by')
    time_entries = db.relationship('TimeEntry', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def initials(self):
        return f'{self.first_name[0]}{self.last_name[0]}'.upper()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return self.role and self.role.name == role_name

    def can(self, permission):
        if self.is_admin:
            return True
        return self.role and self.role.has_permission(permission)


class UserRole(db.Model):
    """Many-to-many relationship between users and roles (for future multi-role support)."""
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='user_roles')
    role = db.relationship('Role', backref='user_roles')