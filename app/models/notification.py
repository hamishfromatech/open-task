"""Notification and Trigger models."""

from datetime import datetime
from app import db


class NotificationRule(db.Model):
    """Notification rule for triggers."""
    __tablename__ = 'notification_rules'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Rule name and description
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    # Trigger conditions
    trigger_type = db.Column(db.String(50), nullable=False)
    # ticket_created, ticket_status_changed, ticket_priority_changed,
    # sla_breach_warning, sla_breached, ticket_assigned, ticket_resolved,
    # project_created, project_completed, task_assigned, task_completed,
    # lead_created, lead_converted, opportunity_won, opportunity_lost,
    # invoice_created, invoice_paid, invoice_overdue,
    # time_entry_logged, custom

    trigger_conditions = db.Column(db.JSON, default=dict)
    # Conditions for triggering:
    # {"priority": ["critical", "high"], "category": ["hardware", "software"], ...}
    # {"status_from": ["open"], "status_to": ["resolved"], ...}

    # Notification channels
    channels = db.Column(db.JSON, default=list)
    # [{"type": "slack", "config": {"channel": "#alerts"}},
    #  {"type": "email", "config": {"recipients": ["admin@example.com"]}},
    #  {"type": "teams", "config": {"webhook_url": "..."}},
    #  {"type": "webhook", "config": {"url": "...", "method": "POST"}}]

    # Connected accounts to use for sending
    connected_account_ids = db.Column(db.JSON, default=list)

    # Metadata (for storing subscription IDs, etc.)
    metadata = db.Column(db.JSON, default=dict)

    # Message template
    message_template = db.Column(db.Text)
    # Template variables: {{ticket.subject}}, {{ticket.priority}}, {{user.name}}, etc.

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Statistics
    trigger_count = db.Column(db.Integer, default=0)
    last_triggered_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = db.relationship('Organization', backref='notification_rules')
    creator = db.relationship('User', backref='created_notification_rules')

    def __repr__(self):
        return f'<NotificationRule {self.name}>'


class NotificationLog(db.Model):
    """Log of sent notifications."""
    __tablename__ = 'notification_logs'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('notification_rules.id'))

    # Trigger details
    trigger_type = db.Column(db.String(50))
    trigger_entity_type = db.Column(db.String(50))  # ticket, project, lead, etc.
    trigger_entity_id = db.Column(db.Integer)
    trigger_data = db.Column(db.JSON, default=dict)  # Data that triggered this

    # Notification details
    channel = db.Column(db.String(50))  # slack, email, teams, webhook
    recipient = db.Column(db.String(255))  # Channel, email, URL
    subject = db.Column(db.String(500))
    message = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    rule = db.relationship('NotificationRule', backref='logs')

    def __repr__(self):
        return f'<NotificationLog {self.id}:{self.status}>'


class NotificationPreference(db.Model):
    """User notification preferences."""
    __tablename__ = 'notification_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # Email notifications
    email_ticket_created = db.Column(db.Boolean, default=True)
    email_ticket_assigned = db.Column(db.Boolean, default=True)
    email_ticket_resolved = db.Column(db.Boolean, default=True)
    email_sla_warning = db.Column(db.Boolean, default=True)
    email_sla_breach = db.Column(db.Boolean, default=True)
    email_project_updates = db.Column(db.Boolean, default=True)
    email_invoice_updates = db.Column(db.Boolean, default=True)
    email_daily_digest = db.Column(db.Boolean, default=False)
    email_weekly_report = db.Column(db.Boolean, default=False)

    # In-app notifications
    in_app_tickets = db.Column(db.Boolean, default=True)
    in_app_projects = db.Column(db.Boolean, default=True)
    in_app_mentions = db.Column(db.Boolean, default=True)
    in_app_system = db.Column(db.Boolean, default=True)

    # Connected channels (for direct messaging)
    slack_user_id = db.Column(db.String(100))
    teams_user_id = db.Column(db.String(100))

    # Digest preferences
    digest_time = db.Column(db.String(10), default='09:00')  # Time for daily digest
    timezone = db.Column(db.String(50), default='UTC')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='notification_preferences')

    def __repr__(self):
        return f'<NotificationPreference user:{self.user_id}>'