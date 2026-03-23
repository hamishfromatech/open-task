"""Main forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class OrganizationSettingsForm(FlaskForm):
    # Ticketing settings
    default_ticket_priority = SelectField('Default Ticket Priority', choices=[
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], default='medium')
    default_sla_hours = IntegerField('Default SLA (hours)', default=24)
    auto_assign_tickets = BooleanField('Auto-assign tickets')
    ticket_number_prefix = StringField('Ticket Number Prefix', validators=[Length(1, 10)], default='TKT')

    # Notification settings
    notify_on_new_ticket = BooleanField('Notify on new ticket', default=True)
    notify_on_ticket_update = BooleanField('Notify on ticket update', default=True)
    notify_on_ticket_resolve = BooleanField('Notify on ticket resolution', default=True)
    daily_digest_email = BooleanField('Send daily digest email', default=True)

    # AI settings
    enable_ai_features = BooleanField('Enable AI features', default=True)

    # Business settings
    currency = SelectField('Currency', choices=[
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('CAD', 'CAD - Canadian Dollar'),
        ('AUD', 'AUD - Australian Dollar'),
    ], default='USD')
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('America/New_York', 'Eastern Time (US)'),
        ('America/Chicago', 'Central Time (US)'),
        ('America/Denver', 'Mountain Time (US)'),
        ('America/Los_Angeles', 'Pacific Time (US)'),
        ('Europe/London', 'London'),
        ('Europe/Paris', 'Paris'),
        ('Asia/Tokyo', 'Tokyo'),
        ('Australia/Sydney', 'Sydney'),
    ], default='UTC')

    submit = SubmitField('Save Settings')


class InviteMemberForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 255)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 100)])
    role = SelectField('Role', choices=[
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('agent', 'Agent'),
        ('viewer', 'Viewer'),
    ], default='agent')
    submit = SubmitField('Send Invitation')