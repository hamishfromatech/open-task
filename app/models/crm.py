"""CRM models - Lead, Opportunity, Activity."""

from datetime import datetime
from app import db


class Lead(db.Model):
    """Lead/Prospect model."""
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))

    # Contact information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), index=True)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(255))
    job_title = db.Column(db.String(100))

    # Source
    source = db.Column(db.String(50))  # website, referral, cold_call, trade_show, etc.
    campaign = db.Column(db.String(100))

    # Status
    status = db.Column(db.String(20), default='new', index=True)
    # new, contacted, qualified, unqualified, converted

    # Qualification
    lead_score = db.Column(db.Integer, default=0)  # 0-100
    estimated_value = db.Column(db.Float, default=0)
    estimated_close_date = db.Column(db.Date)

    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Notes
    notes = db.Column(db.Text)

    # Conversion
    converted_at = db.Column(db.DateTime)
    converted_to_opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'))

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    activities = db.relationship('Activity', backref='lead', lazy='dynamic')

    def __repr__(self):
        return f'<Lead {self.full_name}>'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def status_badge_class(self):
        classes = {
            'new': 'bg-blue-100 text-blue-800',
            'contacted': 'bg-yellow-100 text-yellow-800',
            'qualified': 'bg-green-100 text-green-800',
            'unqualified': 'bg-red-100 text-red-800',
            'converted': 'bg-purple-100 text-purple-800',
        }
        return classes.get(self.status, 'bg-gray-100 text-gray-800')


class Opportunity(db.Model):
    """Sales opportunity model."""
    __tablename__ = 'opportunities'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))

    # Basic info
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    # Value
    amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='USD')

    # Stage
    stage = db.Column(db.String(20), default='prospecting', index=True)
    # prospecting, qualification, proposal, negotiation, closed_won, closed_lost
    probability = db.Column(db.Integer, default=10)  # 0-100

    # Expected close
    expected_close_date = db.Column(db.Date)
    actual_close_date = db.Column(db.Date)

    # Type
    opportunity_type = db.Column(db.String(50))  # new_business, renewal, upsell, cross_sell

    # Assignment
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Source
    source = db.Column(db.String(50))
    campaign = db.Column(db.String(100))

    # Competitor info
    competitors = db.Column(db.JSON, default=list)
    competitive_position = db.Column(db.Text)

    # Lost reason
    lost_reason = db.Column(db.String(100))
    lost_details = db.Column(db.Text)

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id])
    activities = db.relationship('Activity', backref='opportunity', lazy='dynamic')

    def __repr__(self):
        return f'<Opportunity {self.name}>'

    @property
    def stage_badge_class(self):
        classes = {
            'prospecting': 'bg-blue-100 text-blue-800',
            'qualification': 'bg-indigo-100 text-indigo-800',
            'proposal': 'bg-yellow-100 text-yellow-800',
            'negotiation': 'bg-orange-100 text-orange-800',
            'closed_won': 'bg-green-100 text-green-800',
            'closed_lost': 'bg-red-100 text-red-800',
        }
        return classes.get(self.stage, 'bg-gray-100 text-gray-800')

    @property
    def weighted_value(self):
        return self.amount * (self.probability / 100) if self.amount else 0


class Activity(db.Model):
    """Activity/Interaction model for CRM."""
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # Related entities (polymorphic)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))

    # Activity details
    activity_type = db.Column(db.String(50), nullable=False)
    # call, email, meeting, note, task, demo, proposal, other

    subject = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)

    # Duration (for calls, meetings)
    duration_minutes = db.Column(db.Integer)

    # Outcome
    outcome = db.Column(db.String(50))  # successful, unsuccessful, no_response, etc.

    # Follow-up
    follow_up_date = db.Column(db.Date)
    follow_up_notes = db.Column(db.Text)

    # Timestamps
    activity_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship('User', backref='activities')

    def __repr__(self):
        return f'<Activity {self.activity_type}: {self.subject}>'

    @property
    def type_icon(self):
        icons = {
            'call': 'phone',
            'email': 'mail',
            'meeting': 'users',
            'note': 'file-text',
            'task': 'check-square',
            'demo': 'play',
            'proposal': 'file',
        }
        return icons.get(self.activity_type, 'activity')