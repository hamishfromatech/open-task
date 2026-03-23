"""Organization and settings models."""

from datetime import datetime
from app import db


class Organization(db.Model):
    """Organization/Company model for multi-tenancy."""
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)

    # Branding
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7), default='#3B82F6')
    secondary_color = db.Column(db.String(7), default='#1E40AF')

    # Contact
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(255))
    address = db.Column(db.Text)

    # Subscription
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    subscription_plan = db.Column(db.String(50), default='starter')
    subscription_status = db.Column(db.String(50), default='active')
    subscription_ends_at = db.Column(db.DateTime)

    # Limits
    max_users = db.Column(db.Integer, default=5)
    max_clients = db.Column(db.Integer, default=50)
    max_projects = db.Column(db.Integer, default=20)
    storage_limit_mb = db.Column(db.Integer, default=1000)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    on_trial = db.Column(db.Boolean, default=False)
    trial_ends_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    settings = db.relationship('OrganizationSettings', backref='organization', uselist=False)
    clients = db.relationship('Client', backref='organization', lazy='dynamic')

    def __repr__(self):
        return f'<Organization {self.name}>'

    @property
    def is_subscribed(self):
        if self.on_trial and self.trial_ends_at and self.trial_ends_at > datetime.utcnow():
            return True
        return self.subscription_status == 'active'

    def usage_percentage(self, resource):
        """Calculate usage percentage for a resource."""
        limits = {
            'users': self.max_users,
            'clients': self.max_clients,
            'projects': self.max_projects,
        }
        counts = {
            'users': self.members.count() if hasattr(self, 'members') else 0,
            'clients': self.clients.count(),
            'projects': 0,  # Would need to count projects
        }
        limit = limits.get(resource, 1)
        count = counts.get(resource, 0)
        return min(100, (count / limit) * 100) if limit > 0 else 0


class OrganizationSettings(db.Model):
    """Organization-specific settings."""
    __tablename__ = 'organization_settings'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # Ticketing settings
    default_ticket_priority = db.Column(db.String(20), default='medium')
    default_sla_hours = db.Column(db.Integer, default=24)
    auto_assign_tickets = db.Column(db.Boolean, default=False)
    ticket_number_prefix = db.Column(db.String(10), default='TKT')

    # Notification settings
    notify_on_new_ticket = db.Column(db.Boolean, default=True)
    notify_on_ticket_update = db.Column(db.Boolean, default=True)
    notify_on_ticket_resolve = db.Column(db.Boolean, default=True)
    daily_digest_email = db.Column(db.Boolean, default=True)

    # Integration settings
    enable_ai_features = db.Column(db.Boolean, default=True)
    ai_model = db.Column(db.String(50), default='gpt-4-turbo-preview')

    # Business settings
    currency = db.Column(db.String(3), default='USD')
    timezone = db.Column(db.String(50), default='UTC')
    date_format = db.Column(db.String(20), default='YYYY-MM-DD')
    time_format = db.Column(db.String(10), default='24h')

    # Custom fields (JSON)
    custom_fields = db.Column(db.JSON, default=dict)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<OrganizationSettings for Organization {self.organization_id}>'