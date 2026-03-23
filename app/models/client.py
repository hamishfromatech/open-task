"""Client and Contact models."""

from datetime import datetime
from app import db


class Client(db.Model):
    """Client company model."""
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # Basic info
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), index=True)

    # Type and status
    client_type = db.Column(db.String(50), default='prospect')  # prospect, active, inactive
    status = db.Column(db.String(50), default='active')  # active, inactive, archived

    # Contact information
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(255))

    # Address
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='United States')

    # Business details
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))  # 1-10, 11-50, 51-200, 201-500, 500+
    annual_revenue = db.Column(db.Integer)

    # Notes and custom fields
    notes = db.Column(db.Text)
    custom_fields = db.Column(db.JSON, default=dict)

    # Billing
    billing_contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    payment_terms = db.Column(db.Integer, default=30)  # Net 30 days

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contacts = db.relationship('Contact', backref='client', lazy='dynamic',
                               foreign_keys='Contact.client_id')
    tickets = db.relationship('Ticket', backref='client', lazy='dynamic')
    projects = db.relationship('Project', backref='client', lazy='dynamic')
    leads = db.relationship('Lead', backref='client', lazy='dynamic')
    opportunities = db.relationship('Opportunity', backref='client', lazy='dynamic')

    def __repr__(self):
        return f'<Client {self.name}>'

    @property
    def primary_contact(self):
        return self.contacts.filter_by(is_primary=True).first()

    @property
    def active_tickets_count(self):
        return self.tickets.filter(Ticket.status.in_(['open', 'in_progress', 'pending'])).count()


class Contact(db.Model):
    """Contact person model."""
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # Personal information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), index=True)
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))

    # Role
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))

    # Status
    is_primary = db.Column(db.Boolean, default=False)
    is_billing_contact = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # Preferences
    preferred_contact_method = db.Column(db.String(20), default='email')  # email, phone
    timezone = db.Column(db.String(50))

    # Notes
    notes = db.Column(db.Text)

    # Social profiles
    linkedin = db.Column(db.String(255))
    twitter = db.Column(db.String(100))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contacted = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Contact {self.full_name}>'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def initials(self):
        return f'{self.first_name[0]}{self.last_name[0]}'.upper()