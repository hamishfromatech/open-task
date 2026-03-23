"""Billing and Invoice models."""

from datetime import datetime
from app import db
import uuid


class Invoice(db.Model):
    """Invoice model."""
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # Invoice number
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Status
    status = db.Column(db.String(20), default='draft', index=True)
    # draft, sent, viewed, paid, overdue, cancelled

    # Dates
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date)

    # Amounts
    subtotal = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    discount_percent = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
    amount_due = db.Column(db.Float, default=0)

    # Currency
    currency = db.Column(db.String(3), default='USD')

    # Notes
    notes = db.Column(db.Text)
    terms = db.Column(db.Text)
    public_notes = db.Column(db.Text)  # Visible to client

    # Billing contact
    billing_contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    billing_email = db.Column(db.String(255))

    # Stripe integration
    stripe_invoice_id = db.Column(db.String(100), unique=True)
    stripe_payment_intent_id = db.Column(db.String(100))

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = db.Column(db.DateTime)

    # Relationships
    client = db.relationship('Client', backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic',
                           cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')
    time_entries = db.relationship('TimeEntry', backref='invoice', lazy='dynamic')

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

    @staticmethod
    def generate_invoice_number(organization_id, prefix='INV'):
        from app.models import Invoice
        count = Invoice.query.filter_by(organization_id=organization_id).count() + 1
        year = datetime.utcnow().year
        return f'{prefix}-{year}-{count:05d}'

    def calculate_totals(self):
        """Calculate invoice totals from items."""
        self.subtotal = sum(item.total for item in self.items)
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount - self.discount_amount
        self.amount_due = self.total - self.amount_paid
        return self.total

    @property
    def is_paid(self):
        return self.status == 'paid' or self.amount_due <= 0

    @property
    def is_overdue(self):
        if self.status in ['paid', 'cancelled', 'draft']:
            return False
        return datetime.utcnow().date() > self.due_date

    @property
    def status_badge_class(self):
        classes = {
            'draft': 'bg-gray-100 text-gray-800',
            'sent': 'bg-blue-100 text-blue-800',
            'viewed': 'bg-indigo-100 text-indigo-800',
            'paid': 'bg-green-100 text-green-800',
            'overdue': 'bg-red-100 text-red-800',
            'cancelled': 'bg-gray-100 text-gray-500',
        }
        return classes.get(self.status, 'bg-gray-100 text-gray-800')


class InvoiceItem(db.Model):
    """Invoice line item model."""
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)

    # Related entity (optional)
    time_entry_id = db.Column(db.Integer, db.ForeignKey('time_entries.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))

    # Item details
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)

    # Type
    item_type = db.Column(db.String(50), default='service')  # service, product, expense, discount

    # Taxable
    taxable = db.Column(db.Boolean, default=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<InvoiceItem {self.description[:50]}>'

    def calculate_total(self):
        """Calculate item total."""
        self.total = self.quantity * self.unit_price
        return self.total


class Payment(db.Model):
    """Payment record model."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # Payment details
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_method = db.Column(db.String(50))  # card, bank_transfer, check, cash, other

    # Payment date
    payment_date = db.Column(db.Date, nullable=False)

    # Reference
    reference_number = db.Column(db.String(100))
    notes = db.Column(db.Text)

    # Stripe integration
    stripe_payment_intent_id = db.Column(db.String(100))
    stripe_charge_id = db.Column(db.String(100))

    # Status
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed, refunded

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = db.relationship('Invoice', backref='invoice_payments')
    client = db.relationship('Client', backref='payments')
    creator = db.relationship('User', backref='recorded_payments')

    def __repr__(self):
        return f'<Payment {self.id}: ${self.amount}>'


class Subscription(db.Model):
    """Subscription model for recurring billing."""
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # Subscription details
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    # Pricing
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    billing_interval = db.Column(db.String(20), default='monthly')  # monthly, quarterly, yearly

    # Duration
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # NULL for open-ended
    next_billing_date = db.Column(db.Date)

    # Status
    status = db.Column(db.String(20), default='active', index=True)
    # active, paused, cancelled, expired

    # Stripe integration
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    stripe_customer_id = db.Column(db.String(100))

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime)

    # Relationships
    client = db.relationship('Client', backref='subscriptions')

    def __repr__(self):
        return f'<Subscription {self.name}>'