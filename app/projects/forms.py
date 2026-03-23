"""Project forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(1, 255)])
    description = TextAreaField('Description', validators=[Optional()])
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    project_type = SelectField('Type', choices=[
        ('fixed', 'Fixed Price'),
        ('time_materials', 'Time & Materials'),
        ('retainer', 'Retainer'),
    ], default='fixed')
    methodology = SelectField('Methodology', choices=[
        ('kanban', 'Kanban'),
        ('scrum', 'Scrum'),
        ('waterfall', 'Waterfall'),
    ], default='kanban')
    status = SelectField('Status', choices=[
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='planning')
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    budget_type = SelectField('Budget Type', choices=[
        ('hours', 'Hours'),
        ('fixed', 'Fixed Amount'),
        ('not_applicable', 'Not Applicable'),
    ], default='hours')
    budget_hours = FloatField('Budget Hours', validators=[Optional(), NumberRange(min=0)])
    budget_amount = FloatField('Budget Amount', validators=[Optional(), NumberRange(min=0)])
    hourly_rate = FloatField('Hourly Rate', validators=[Optional(), NumberRange(min=0)])
    project_manager_id = SelectField('Project Manager', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Project')


class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(1, 500)])
    description = TextAreaField('Description', validators=[Optional()])
    phase_id = SelectField('Phase', coerce=int, validators=[Optional()])
    assigned_to = SelectField('Assignee', coerce=int, validators=[Optional()])
    priority = SelectField('Priority', choices=[
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], default='medium')
    status = SelectField('Status', choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='not_started')
    estimated_hours = FloatField('Estimated Hours', validators=[Optional(), NumberRange(min=0)])
    due_date = DateField('Due Date', validators=[Optional()])
    submit = SubmitField('Save Task')


class TimeEntryForm(FlaskForm):
    hours = FloatField('Hours', validators=[DataRequired(), NumberRange(min=0.1, max=24)])
    description = TextAreaField('Description', validators=[Optional()])
    billable = BooleanField('Billable', default=True)
    hourly_rate = FloatField('Hourly Rate', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Add Time Entry')


class ProjectPhaseForm(FlaskForm):
    name = StringField('Phase Name', validators=[DataRequired(), Length(1, 255)])
    description = TextAreaField('Description', validators=[Optional()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    submit = SubmitField('Save Phase')