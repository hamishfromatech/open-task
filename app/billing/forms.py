"""Billing forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, DateField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class InvoiceForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    issue_date = DateField('Issue Date', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    terms = TextAreaField('Terms & Conditions', validators=[Optional()])
    submit = SubmitField('Save Invoice')


class InvoiceItemForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0)])
    item_type = SelectField('Type', choices=[
        ('service', 'Service'),
        ('product', 'Product'),
        ('expense', 'Expense'),
        ('discount', 'Discount'),
    ], default='service')
    taxable = SelectField('Taxable', choices=[
        ('yes', 'Yes'),
        ('no', 'No'),
    ], default='yes')
    submit = SubmitField('Add Item')


class PaymentForm(FlaskForm):
    invoice_id = IntegerField('Invoice ID', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ], default='card')
    reference_number = StringField('Reference Number', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Record Payment')


class SubscriptionForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    name = StringField('Subscription Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    billing_interval = SelectField('Billing Interval', choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], default='monthly')
    start_date = DateField('Start Date', validators=[DataRequired()])
    submit = SubmitField('Create Subscription')