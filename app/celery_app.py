# Celery configuration
from celery import Celery
from app import create_app

def make_celery(app_name=__name__):
    """Create Celery instance."""
    flask_app = create_app()
    celery = Celery(
        app_name,
        broker=flask_app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
        backend=flask_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(flask_app.config)

    class ContextTask(celery.Task):
        """Task with Flask app context."""
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery()


@celery.task
def send_email_task(to, subject, body):
    """Background task to send email."""
    from flask_mail import Message
    from app import mail

    msg = Message(
        subject,
        recipients=[to],
        body=body
    )
    mail.send(msg)


@celery.task
def process_webhook_task(event_id):
    """Process webhook event in background."""
    from app import db
    from app.models.integration import IntegrationEvent

    event = IntegrationEvent.query.get(event_id)
    if not event:
        return

    # Process based on event type
    # This would be implemented based on specific integration requirements
    pass


@celery.task
def sync_integration_task(connected_account_id):
    """Sync data from integration in background."""
    from app import db
    from app.models.integration import ConnectedAccount
    from app.integrations.composio_service import ComposioService

    account = ConnectedAccount.query.get(connected_account_id)
    if not account:
        return

    try:
        service = ComposioService()
        service.trigger_sync(account.connection_id)
        account.last_sync_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        account.last_error = str(e)
        db.session.commit()


@celery.task
def calculate_sla_task():
    """Calculate and update SLA status for all open tickets."""
    from app import db
    from app.models.ticket import Ticket

    tickets = Ticket.query.filter(Ticket.status.in_(['open', 'in_progress', 'pending'])).all()

    for ticket in tickets:
        ticket.update_sla_status()

    db.session.commit()


@celery.task
def generate_daily_report_task(organization_id):
    """Generate daily report for organization."""
    from datetime import datetime, timedelta
    from app import db
    from app.models.ticket import Ticket
    from app.models.project import Project
    from app.models.crm import Opportunity
    from sqlalchemy import func

    # Get metrics for the past day
    yesterday = datetime.utcnow() - timedelta(days=1)

    report = {
        'date': yesterday.strftime('%Y-%m-%d'),
        'tickets_created': Ticket.query.filter(
            Ticket.organization_id == organization_id,
            Ticket.created_at >= yesterday
        ).count(),
        'tickets_resolved': Ticket.query.filter(
            Ticket.organization_id == organization_id,
            Ticket.resolved_at >= yesterday
        ).count(),
        'opportunities_won': Opportunity.query.filter(
            Opportunity.organization_id == organization_id,
            Opportunity.stage == 'closed_won',
            Opportunity.actual_close_date >= yesterday
        ).count(),
    }

    # Send email notification
    # This would send to organization admins

    return report


@celery.task
def cleanup_old_data_task():
    """Clean up old data based on retention policy."""
    from datetime import datetime, timedelta
    from app import db
    from app.models.ticket import TicketHistory

    # Delete ticket history older than 90 days
    cutoff = datetime.utcnow() - timedelta(days=90)

    TicketHistory.query.filter(TicketHistory.created_at < cutoff).delete()
    db.session.commit()