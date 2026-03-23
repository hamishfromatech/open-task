"""CRM forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Email, NumberRange


class ClientForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(1, 255)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(1, 20)])
    website = StringField('Website', validators=[Optional(), Length(1, 255)])
    address_line1 = StringField('Address Line 1', validators=[Optional(), Length(1, 255)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(1, 255)])
    city = StringField('City', validators=[Optional(), Length(1, 100)])
    state = StringField('State/Province', validators=[Optional(), Length(1, 100)])
    postal_code = StringField('Postal Code', validators=[Optional(), Length(1, 20)])
    country = StringField('Country', validators=[Optional(), Length(1, 100)])
    industry = SelectField('Industry', choices=[
        ('', '-- Select Industry --'),
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('education', 'Education'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('consulting', 'Consulting'),
        ('other', 'Other'),
    ], validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    client_type = SelectField('Type', choices=[
        ('prospect', 'Prospect'),
        ('active', 'Active Client'),
        ('inactive', 'Inactive'),
    ], default='prospect')
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], default='active')
    submit = SubmitField('Save Client')


class ContactForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(1, 20)])
    mobile = StringField('Mobile', validators=[Optional(), Length(1, 20)])
    job_title = StringField('Job Title', validators=[Optional(), Length(1, 100)])
    department = StringField('Department', validators=[Optional(), Length(1, 100)])
    is_primary = BooleanField('Primary Contact')
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Contact')


class LeadForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(1, 20)])
    company = StringField('Company', validators=[Optional(), Length(1, 255)])
    job_title = StringField('Job Title', validators=[Optional(), Length(1, 100)])
    source = SelectField('Source', choices=[
        ('', '-- Select Source --'),
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('cold_call', 'Cold Call'),
        ('trade_show', 'Trade Show'),
        ('social_media', 'Social Media'),
        ('advertisement', 'Advertisement'),
        ('other', 'Other'),
    ], validators=[Optional()])
    status = SelectField('Status', choices=[
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
        ('converted', 'Converted'),
    ], default='new')
    lead_score = IntegerField('Lead Score', validators=[Optional(), NumberRange(min=0, max=100)])
    estimated_value = FloatField('Estimated Value', validators=[Optional(), NumberRange(min=0)])
    estimated_close_date = DateField('Estimated Close Date', validators=[Optional()])
    assigned_to = SelectField('Assign To', coerce=int, validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Lead')


class OpportunityForm(FlaskForm):
    name = StringField('Opportunity Name', validators=[DataRequired(), Length(1, 255)])
    description = TextAreaField('Description', validators=[Optional()])
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    amount = FloatField('Amount', validators=[Optional(), NumberRange(min=0)])
    stage = SelectField('Stage', choices=[
        ('prospecting', 'Prospecting'),
        ('qualification', 'Qualification'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost'),
    ], default='prospecting')
    probability = IntegerField('Probability (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    expected_close_date = DateField('Expected Close Date', validators=[Optional()])
    opportunity_type = SelectField('Type', choices=[
        ('new_business', 'New Business'),
        ('renewal', 'Renewal'),
        ('upsell', 'Upsell'),
        ('cross_sell', 'Cross-sell'),
    ], default='new_business')
    owner_id = SelectField('Owner', coerce=int, validators=[Optional()])
    source = StringField('Source', validators=[Optional(), Length(1, 100)])
    submit = SubmitField('Save Opportunity')


class ActivityForm(FlaskForm):
    activity_type = SelectField('Type', choices=[
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('note', 'Note'),
        ('task', 'Task'),
        ('demo', 'Demo'),
        ('proposal', 'Proposal'),
    ], default='note')
    subject = StringField('Subject', validators=[DataRequired(), Length(1, 500)])
    description = TextAreaField('Description', validators=[Optional()])
    duration_minutes = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=0)])
    outcome = SelectField('Outcome', choices=[
        ('', '-- Select Outcome --'),
        ('successful', 'Successful'),
        ('unsuccessful', 'Unsuccessful'),
        ('no_response', 'No Response'),
        ('follow_up', 'Follow-up Required'),
    ], validators=[Optional()])
    follow_up_date = DateField('Follow-up Date', validators=[Optional()])
    follow_up_notes = TextAreaField('Follow-up Notes', validators=[Optional()])
    submit = SubmitField('Save Activity')