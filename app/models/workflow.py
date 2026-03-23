"""Workflow automation models."""

from datetime import datetime
from app import db


class Workflow(db.Model):
    """Workflow automation definition."""
    __tablename__ = 'workflows'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # Basic info
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(100), index=True)

    # Trigger
    trigger_type = db.Column(db.String(50), nullable=False)
    # ticket_created, ticket_updated, ticket_status_changed,
    # project_created, project_completed, lead_created, etc.
    trigger_config = db.Column(db.JSON, default=dict)  # Conditions for trigger

    # Actions
    actions = db.Column(db.JSON, default=list)
    # List of actions to execute:
    # [{"type": "assign_ticket", "config": {...}},
    #  {"type": "send_email", "config": {...}},
    #  {"type": "create_task", "config": {...}},
    #  {"type": "update_field", "config": {...}}]

    # Conditions (optional filter)
    conditions = db.Column(db.JSON, default=list)
    # Conditions to check before executing actions

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_system = db.Column(db.Boolean, default=False)

    # Execution stats
    execution_count = db.Column(db.Integer, default=0)
    last_execution_at = db.Column(db.DateTime)

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    executions = db.relationship('WorkflowExecution', backref='workflow', lazy='dynamic')
    creator = db.relationship('User', backref='created_workflows')

    def __repr__(self):
        return f'<Workflow {self.name}>'


class WorkflowRule(db.Model):
    """Individual workflow rule (for complex conditions)."""
    __tablename__ = 'workflow_rules'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False)

    # Rule details
    name = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)

    # Conditions (AND logic within a rule)
    conditions = db.Column(db.JSON, default=list)
    # [{"field": "priority", "operator": "equals", "value": "high"},
    #  {"field": "category", "operator": "in", "value": ["hardware", "software"]}]

    # Actions for this rule
    actions = db.Column(db.JSON, default=list)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow = db.relationship('Workflow', backref='rules')

    def __repr__(self):
        return f'<WorkflowRule {self.name}>'


class WorkflowExecution(db.Model):
    """Workflow execution log."""
    __tablename__ = 'workflow_executions'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # Trigger info
    trigger_type = db.Column(db.String(50))
    trigger_entity_type = db.Column(db.String(50))  # ticket, project, lead, etc.
    trigger_entity_id = db.Column(db.Integer)

    # Execution status
    status = db.Column(db.String(20), default='pending', index=True)
    # pending, running, completed, failed

    # Results
    actions_executed = db.Column(db.JSON, default=list)
    actions_failed = db.Column(db.JSON, default=list)
    error_message = db.Column(db.Text)

    # Timing
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    duration_ms = db.Column(db.Integer)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WorkflowExecution {self.workflow_id}:{self.status}>'

    @property
    def was_successful(self):
        return self.status == 'completed' and len(self.actions_failed) == 0


class ScheduledTask(db.Model):
    """Scheduled task for recurring automations."""
    __tablename__ = 'scheduled_tasks'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'))

    # Task details
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(50), default='workflow')  # workflow, report, cleanup, etc.

    # Schedule
    schedule_type = db.Column(db.String(20), default='cron')  # cron, interval, once
    schedule_config = db.Column(db.JSON, default=dict)
    # Cron: {"expression": "0 9 * * *"}
    # Interval: {"interval": 60, "unit": "minutes"}
    # Once: {"datetime": "2024-01-01T10:00:00Z"}

    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_run_at = db.Column(db.DateTime)
    next_run_at = db.Column(db.DateTime)
    last_run_status = db.Column(db.String(20))

    # Execution count
    run_count = db.Column(db.Integer, default=0)
    failure_count = db.Column(db.Integer, default=0)

    # Configuration
    config = db.Column(db.JSON, default=dict)

    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ScheduledTask {self.name}>'