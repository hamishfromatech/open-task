"""Ticket forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea


class TicketForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    contact_id = SelectField('Contact', coerce=int, validators=[Optional()])
    subject = StringField('Subject', validators=[DataRequired(), Length(1, 500)])
    description = TextAreaField('Description', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], default='medium')
    category = SelectField('Category', choices=[
        ('', '-- Select Category --'),
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('network', 'Network'),
        ('security', 'Security'),
        ('email', 'Email'),
        ('other', 'Other'),
    ], validators=[Optional()])
    ticket_type = SelectField('Type', choices=[
        ('incident', 'Incident'),
        ('request', 'Service Request'),
        ('change', 'Change Request'),
        ('problem', 'Problem'),
    ], default='incident')
    source = SelectField('Source', choices=[
        ('portal', 'Portal'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('chat', 'Chat'),
        ('api', 'API'),
    ], default='portal')
    assigned_to = SelectField('Assign To', coerce=int, validators=[Optional()])
    submit = SubmitField('Create Ticket')


class TicketCommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    is_internal = BooleanField('Internal note (not visible to client)')
    mark_as_resolution = BooleanField('Mark as resolution')
    submit = SubmitField('Add Comment')


class TicketFilterForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], validators=[Optional()])
    priority = SelectField('Priority', choices=[
        ('', 'All Priorities'),
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], validators=[Optional()])
    assigned_to = SelectField('Assigned To', coerce=int, validators=[Optional()])
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    search = StringField('Search', validators=[Optional()])


class TicketBulkActionForm(FlaskForm):
    action = SelectField('Action', choices=[
        ('assign', 'Assign'),
        ('status', 'Change Status'),
        ('priority', 'Change Priority'),
        ('delete', 'Delete'),
    ])
    ticket_ids = StringField('Ticket IDs')
    value = StringField('Value')
    submit = SubmitField('Apply')