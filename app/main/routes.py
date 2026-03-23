"""Main application routes."""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, and_
from app import db
from app.models.ticket import Ticket
from app.models.project import Project, Task
from app.models.crm import Lead, Opportunity
from app.models.client import Client
from app.models.billing import Invoice
from app.models.user import User

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard."""
    org_id = current_user.organization_id

    # Get statistics
    stats = {
        'total_tickets': Ticket.query.filter_by(organization_id=org_id).count(),
        'open_tickets': Ticket.query.filter_by(organization_id=org_id, status='open').count(),
        'in_progress_tickets': Ticket.query.filter_by(organization_id=org_id, status='in_progress').count(),
        'resolved_today': Ticket.query.filter(
            Ticket.organization_id == org_id,
            Ticket.status == 'resolved',
            Ticket.resolved_at >= datetime.utcnow().date()
        ).count(),
        'total_clients': Client.query.filter_by(organization_id=org_id).count(),
        'active_projects': Project.query.filter_by(organization_id=org_id, status='active').count(),
        'open_opportunities': Opportunity.query.filter(
            Opportunity.organization_id == org_id,
            Opportunity.stage.notin_(['closed_won', 'closed_lost'])
        ).count(),
        'pipeline_value': db.session.query(func.sum(Opportunity.amount)).filter(
            Opportunity.organization_id == org_id,
            Opportunity.stage.notin_(['closed_won', 'closed_lost'])
        ).scalar() or 0,
    }

    # Recent tickets
    recent_tickets = Ticket.query.filter_by(organization_id=org_id)\
        .order_by(Ticket.created_at.desc()).limit(5).all()

    # Tickets by status
    ticket_status_data = db.session.query(
        Ticket.status, func.count(Ticket.id)
    ).filter_by(organization_id=org_id).group_by(Ticket.status).all()

    # Tickets by priority
    ticket_priority_data = db.session.query(
        Ticket.priority, func.count(Ticket.id)
    ).filter_by(organization_id=org_id).group_by(Ticket.priority).all()

    # SLA at risk tickets
    sla_at_risk = Ticket.query.filter(
        Ticket.organization_id == org_id,
        Ticket.status.in_(['open', 'in_progress', 'pending']),
        Ticket.sla_status.in_(['at_risk', 'breached'])
    ).order_by(Ticket.sla_due_at).limit(5).all()

    # Upcoming deadlines (tasks and projects)
    upcoming_deadlines = Task.query.filter(
        Task.organization_id == org_id,
        Task.status != 'completed',
        Task.due_date != None,
        Task.due_date <= datetime.utcnow().date() + timedelta(days=7)
    ).order_by(Task.due_date).limit(5).all()

    # Recent activity (would normally come from an activity log table)
    # For now, we'll use recent tickets
    recent_activity = Ticket.query.filter_by(organization_id=org_id)\
        .order_by(Ticket.updated_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           stats=stats,
                           recent_tickets=recent_tickets,
                           ticket_status_data=ticket_status_data,
                           ticket_priority_data=ticket_priority_data,
                           sla_at_risk=sla_at_risk,
                           upcoming_deadlines=upcoming_deadlines,
                           recent_activity=recent_activity)


@main_bp.route('/search')
@login_required
def search():
    """Global search."""
    query = request.args.get('q', '').strip()
    results = {
        'tickets': [],
        'clients': [],
        'projects': [],
        'contacts': [],
    }

    if query:
        org_id = current_user.organization_id
        search_term = f'%{query}%'

        # Search tickets
        results['tickets'] = Ticket.query.filter(
            Ticket.organization_id == org_id,
            db.or_(
                Ticket.subject.ilike(search_term),
                Ticket.description.ilike(search_term),
                Ticket.ticket_number.ilike(search_term)
            )
        ).limit(10).all()

        # Search clients
        results['clients'] = Client.query.filter(
            Client.organization_id == org_id,
            Client.name.ilike(search_term)
        ).limit(10).all()

        # Search projects
        results['projects'] = Project.query.filter(
            Project.organization_id == org_id,
            db.or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term)
            )
        ).limit(10).all()

    return render_template('search_results.html', query=query, results=results)


@main_bp.route('/reports')
@login_required
def reports():
    """Reports dashboard."""
    org_id = current_user.organization_id

    # Date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date:
        start_date = datetime.utcnow().date() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    if not end_date:
        end_date = datetime.utcnow().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Ticket metrics
    ticket_metrics = {
        'created': Ticket.query.filter(
            Ticket.organization_id == org_id,
            Ticket.created_at >= start_date,
            Ticket.created_at <= end_date
        ).count(),
        'resolved': Ticket.query.filter(
            Ticket.organization_id == org_id,
            Ticket.resolved_at >= start_date,
            Ticket.resolved_at <= end_date
        ).count(),
        'avg_resolution_time': 0,  # Calculate from resolved tickets
    }

    # Revenue metrics
    revenue_metrics = {
        'invoiced': db.session.query(func.sum(Invoice.total)).filter(
            Invoice.organization_id == org_id,
            Invoice.issue_date >= start_date,
            Invoice.issue_date <= end_date
        ).scalar() or 0,
        'collected': db.session.query(func.sum(Invoice.amount_paid)).filter(
            Invoice.organization_id == org_id,
            Invoice.paid_date >= start_date,
            Invoice.paid_date <= end_date
        ).scalar() or 0,
    }

    return render_template('reports/index.html',
                           start_date=start_date,
                           end_date=end_date,
                           ticket_metrics=ticket_metrics,
                           revenue_metrics=revenue_metrics)


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Organization settings."""
    from app.models.organization import OrganizationSettings
    from app.main.forms import OrganizationSettingsForm

    org = current_user.organization
    settings_obj = OrganizationSettings.query.filter_by(organization_id=org.id).first()

    if not settings_obj:
        settings_obj = OrganizationSettings(organization_id=org.id)
        db.session.add(settings_obj)
        db.session.commit()

    form = OrganizationSettingsForm(obj=settings_obj)

    if form.validate_on_submit():
        settings_obj.default_ticket_priority = form.default_ticket_priority.data
        settings_obj.default_sla_hours = form.default_sla_hours.data
        settings_obj.auto_assign_tickets = form.auto_assign_tickets.data
        settings_obj.ticket_number_prefix = form.ticket_number_prefix.data
        settings_obj.notify_on_new_ticket = form.notify_on_new_ticket.data
        settings_obj.notify_on_ticket_update = form.notify_on_ticket_update.data
        settings_obj.notify_on_ticket_resolve = form.notify_on_ticket_resolve.data
        settings_obj.daily_digest_email = form.daily_digest_email.data
        settings_obj.enable_ai_features = form.enable_ai_features.data
        settings_obj.currency = form.currency.data
        settings_obj.timezone = form.timezone.data

        db.session.commit()
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('main.settings'))

    return render_template('settings/index.html', org=org, settings=settings_obj, form=form)


@main_bp.route('/team')
@login_required
def team():
    """Team management."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.dashboard'))

    org = current_user.organization
    members = User.query.filter_by(organization_id=org.id).all()

    return render_template('settings/team.html', org=org, members=members)