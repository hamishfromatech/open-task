"""Project and task models."""

from datetime import datetime
from app import db


class Project(db.Model):
    """Project model."""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))

    # Basic info
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    project_number = db.Column(db.String(50), unique=True, index=True)

    # Type and methodology
    project_type = db.Column(db.String(50), default='fixed')  # fixed, time_materials, retainer
    methodology = db.Column(db.String(50), default='kanban')  # kanban, scrum, waterfall

    # Status
    status = db.Column(db.String(20), default='planning', index=True)
    # planning, active, on_hold, completed, cancelled

    # Timeline
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    actual_end_date = db.Column(db.Date)

    # Budget and hours
    budget_type = db.Column(db.String(20), default='hours')  # hours, fixed, not_applicable
    budget_hours = db.Column(db.Float, default=0)
    budget_amount = db.Column(db.Float, default=0)
    hourly_rate = db.Column(db.Float, default=0)

    # Project manager
    project_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Progress
    percent_complete = db.Column(db.Integer, default=0)

    # Custom fields
    custom_fields = db.Column(db.JSON, default=dict)

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    phases = db.relationship('ProjectPhase', backref='project', lazy='dynamic',
                            cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='project', lazy='dynamic')
    time_entries = db.relationship('TimeEntry', backref='project', lazy='dynamic')
    project_manager = db.relationship('User', foreign_keys=[project_manager_id])
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<Project {self.name}>'

    @staticmethod
    def generate_project_number(organization_id, prefix='PRJ'):
        from app.models import Project
        count = Project.query.filter_by(organization_id=organization_id).count() + 1
        return f'{prefix}-{count:04d}'

    @property
    def total_hours_logged(self):
        return sum(entry.hours for entry in self.time_entries)

    @property
    def remaining_hours(self):
        if self.budget_type != 'hours':
            return None
        return max(0, self.budget_hours - self.total_hours_logged)

    @property
    def hours_percentage(self):
        if self.budget_type != 'hours' or self.budget_hours == 0:
            return None
        return min(100, (self.total_hours_logged / self.budget_hours) * 100)

    def update_progress(self):
        """Update project progress based on completed tasks."""
        tasks = self.tasks.all()
        if not tasks:
            return
        completed = sum(1 for t in tasks if t.status == 'completed')
        self.percent_complete = int((completed / len(tasks)) * 100)


class ProjectPhase(db.Model):
    """Project phase/milestone model."""
    __tablename__ = 'project_phases'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    # Basic info
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)

    # Timeline
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    # Status
    status = db.Column(db.String(20), default='not_started')
    # not_started, in_progress, completed, on_hold

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = db.relationship('Task', backref='phase', lazy='dynamic')

    def __repr__(self):
        return f'<ProjectPhase {self.name}>'


class Task(db.Model):
    """Task model for projects and tickets."""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    phase_id = db.Column(db.Integer, db.ForeignKey('project_phases.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))

    # Basic info
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)

    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Priority and type
    priority = db.Column(db.String(20), default='medium')
    task_type = db.Column(db.String(50), default='task')  # task, bug, feature, improvement

    # Status
    status = db.Column(db.String(20), default='not_started', index=True)
    # not_started, in_progress, completed, cancelled

    # Effort
    estimated_hours = db.Column(db.Float, default=0)
    actual_hours = db.Column(db.Float, default=0)

    # Progress
    percent_complete = db.Column(db.Integer, default=0)

    # Dates
    due_date = db.Column(db.Date)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Dependencies
    depends_on = db.Column(db.JSON, default=list)  # List of task IDs

    # Labels/Tags
    labels = db.Column(db.JSON, default=list)

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    creator = db.relationship('User', foreign_keys=[created_by])
    time_entries = db.relationship('TimeEntry', backref='task', lazy='dynamic')

    def __repr__(self):
        return f'<Task {self.title}>'

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return datetime.utcnow().date() > self.due_date
        return False


class TimeEntry(db.Model):
    """Time tracking entry model."""
    __tablename__ = 'time_entries'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Related entity
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))

    # Time details
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    hours = db.Column(db.Float, nullable=False)

    # Billing
    billable = db.Column(db.Boolean, default=True)
    hourly_rate = db.Column(db.Float, default=0)
    is_invoiced = db.Column(db.Boolean, default=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))

    # Description
    description = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='time_entries')

    def __repr__(self):
        return f'<TimeEntry {self.id}: {self.hours}h>'

    @property
    def amount(self):
        if self.billable and self.hourly_rate:
            return self.hours * self.hourly_rate
        return 0