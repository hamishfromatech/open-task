"""Ticket and related models."""

from datetime import datetime, timedelta
from app import db


class Ticket(db.Model):
    """Service desk ticket model."""
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Client and contact
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))

    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))

    # Classification
    category = db.Column(db.String(50))  # hardware, software, network, security, other
    subcategory = db.Column(db.String(50))
    ticket_type = db.Column(db.String(50), default='incident')  # incident, request, change, problem

    # Content
    subject = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Priority and SLA
    priority = db.Column(db.String(20), default='medium')  # critical, high, medium, low
    urgency = db.Column(db.String(20), default='medium')
    impact = db.Column(db.String(20), default='medium')
    sla_due_at = db.Column(db.DateTime)
    sla_status = db.Column(db.String(20), default='on_track')  # on_track, at_risk, breached

    # Status
    status = db.Column(db.String(20), default='open', index=True)
    # open, in_progress, pending, resolved, closed, cancelled

    # Source
    source = db.Column(db.String(20), default='portal')  # portal, email, phone, chat, api

    # Time tracking
    estimated_hours = db.Column(db.Float, default=0)
    actual_hours = db.Column(db.Float, default=0)

    # Resolution
    resolution = db.Column(db.Text)
    resolution_notes = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)

    # Satisfaction
    satisfaction_rating = db.Column(db.Integer)  # 1-5
    satisfaction_comment = db.Column(db.Text)

    # Custom fields
    custom_fields = db.Column(db.JSON, default=dict)

    # Integration references
    external_id = db.Column(db.String(255), index=True)  # ID from external system
    integration_source = db.Column(db.String(50))  # jira, zendesk, etc.

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = db.relationship('Contact', backref='tickets')
    comments = db.relationship('TicketComment', backref='ticket', lazy='dynamic',
                              cascade='all, delete-orphan')
    attachments = db.relationship('TicketAttachment', backref='ticket', lazy='dynamic',
                                  cascade='all, delete-orphan')
    history = db.relationship('TicketHistory', backref='ticket', lazy='dynamic',
                              cascade='all, delete-orphan')
    time_entries = db.relationship('TimeEntry', backref='ticket', lazy='dynamic')

    def __repr__(self):
        return f'<Ticket {self.ticket_number}>'

    @staticmethod
    def generate_ticket_number(organization_id, prefix='TKT'):
        """Generate a unique ticket number."""
        from app.models import Ticket
        count = Ticket.query.filter_by(organization_id=organization_id).count() + 1
        return f'{prefix}-{count:06d}'

    def calculate_sla(self, sla_hours=24):
        """Calculate SLA due date based on priority."""
        sla_map = {
            'critical': 4,
            'high': 8,
            'medium': 24,
            'low': 72,
        }
        hours = sla_map.get(self.priority, sla_hours)
        if not self.sla_due_at:
            self.sla_due_at = datetime.utcnow() + timedelta(hours=hours)
        return self.sla_due_at

    def update_sla_status(self):
        """Update SLA status based on current time."""
        if not self.sla_due_at:
            return

        now = datetime.utcnow()
        time_remaining = (self.sla_due_at - now).total_seconds() / 3600  # hours

        if time_remaining < 0:
            self.sla_status = 'breached'
        elif time_remaining < 2:  # Less than 2 hours
            self.sla_status = 'at_risk'
        else:
            self.sla_status = 'on_track'

    @property
    def is_open(self):
        return self.status in ['open', 'in_progress', 'pending']

    @property
    def time_since_opened(self):
        delta = datetime.utcnow() - self.created_at
        if delta.days > 0:
            return f'{delta.days}d'
        hours = delta.seconds // 3600
        if hours > 0:
            return f'{hours}h'
        minutes = (delta.seconds // 60) % 60
        return f'{minutes}m'


class TicketComment(db.Model):
    """Comment on a ticket."""
    __tablename__ = 'ticket_comments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))

    # Content
    content = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Internal note vs visible to client
    is_resolution = db.Column(db.Boolean, default=False)  # Marks comment as resolution

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='ticket_comments')
    contact = db.relationship('Contact', backref='ticket_comments')
    attachments = db.relationship('TicketAttachment', backref='comment', lazy='dynamic')

    def __repr__(self):
        return f'<TicketComment {self.id}>'


class TicketAttachment(db.Model):
    """File attachment for tickets."""
    __tablename__ = 'ticket_attachments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('ticket_comments.id'))

    # File info
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # bytes
    mime_type = db.Column(db.String(100))

    # Timestamps
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    uploader = db.relationship('User', backref='uploaded_attachments')

    def __repr__(self):
        return f'<TicketAttachment {self.filename}>'


class TicketHistory(db.Model):
    """Audit trail for ticket changes."""
    __tablename__ = 'ticket_history'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Change details
    field_name = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='ticket_history')

    def __repr__(self):
        return f'<TicketHistory {self.ticket_id}:{self.field_name}>'