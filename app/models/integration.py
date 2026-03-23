"""Integration models for third-party connections."""

from datetime import datetime
from app import db


class Integration(db.Model):
    """Available integration definitions."""
    __tablename__ = 'integrations'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))

    # Identification
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50))  # communication, crm, development, productivity, etc.
    provider = db.Column(db.String(50))  # composio, native, custom

    # Description
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(500))

    # Configuration schema
    config_schema = db.Column(db.JSON, default=dict)  # JSON schema for configuration
    auth_type = db.Column(db.String(20))  # oauth2, api_key, basic

    # Capabilities
    actions = db.Column(db.JSON, default=list)  # Available actions
    triggers = db.Column(db.JSON, default=list)  # Available triggers

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_system = db.Column(db.Boolean, default=False)  # System integrations can't be deleted

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Integration {self.name}>'


class ConnectedAccount(db.Model):
    """User's connected third-party accounts."""
    __tablename__ = 'connected_accounts'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id'), nullable=False)

    # Connection details
    connection_id = db.Column(db.String(100), unique=True, index=True)  # Composio connection ID
    account_name = db.Column(db.String(255))  # User-friendly name for the connection
    account_identifier = db.Column(db.String(255))  # Email, username, or ID from provider

    # Status
    status = db.Column(db.String(20), default='active')  # active, expired, revoked, error
    last_sync_at = db.Column(db.DateTime)
    last_error = db.Column(db.Text)

    # Metadata
    metadata = db.Column(db.JSON, default=dict)  # Additional connection metadata

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    integration = db.relationship('Integration', backref='connections')
    user = db.relationship('User', backref='connected_accounts')

    def __repr__(self):
        return f'<ConnectedAccount {self.integration.name}:{self.account_name}>'


class IntegrationEvent(db.Model):
    """Events received from integrations (webhooks, etc.)."""
    __tablename__ = 'integration_events'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    connected_account_id = db.Column(db.Integer, db.ForeignKey('connected_accounts.id'))

    # Event details
    event_type = db.Column(db.String(100), nullable=False, index=True)
    event_id = db.Column(db.String(100), index=True)  # External event ID
    source = db.Column(db.String(50))  # Which integration fired this

    # Payload
    payload = db.Column(db.JSON, default=dict)

    # Processing status
    status = db.Column(db.String(20), default='pending')  # pending, processed, failed
    processed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    # Result
    result = db.Column(db.JSON, default=dict)  # What was created/updated

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    connected_account = db.relationship('ConnectedAccount', backref='events')

    def __repr__(self):
        return f'<IntegrationEvent {self.event_type}>'