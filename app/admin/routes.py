"""Admin routes - System management dashboard."""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app import db
from app.models.user import User, Role
from app.models.organization import Organization, OrganizationSettings
from app.models.ticket import Ticket
from app.models.project import Project
from app.models.crm import Lead, Opportunity
from app.models.billing import Invoice, Subscription
from app.models.integration import Integration, ConnectedAccount
from app.integrations.composio_service import ComposioService

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
@login_required
def index():
    """Admin dashboard home."""
    # Get overall stats
    stats = {
        'total_users': User.query.count(),
        'total_organizations': Organization.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'new_users_this_month': User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count(),
        'total_tickets': Ticket.query.count(),
        'open_tickets': Ticket.query.filter(Ticket.status.in_(['open', 'in_progress'])).count(),
        'total_projects': Project.query.count(),
        'active_projects': Project.query.filter_by(status='active').count(),
        'total_revenue': db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status == 'paid'
        ).scalar() or 0,
        'pending_invoices': Invoice.query.filter(Invoice.status.in_(['sent', 'viewed'])).count(),
    }

    # User growth (last 6 months)
    user_growth = []
    for i in range(6):
        month_start = datetime.utcnow() - timedelta(days=(5-i)*30)
        month_end = month_start + timedelta(days=30)
        count = User.query.filter(
            User.created_at >= month_start,
            User.created_at < month_end
        ).count()
        user_growth.append({
            'month': month_start.strftime('%b'),
            'users': count
        })

    # Revenue by month
    revenue_data = []
    for i in range(6):
        month_start = datetime.utcnow() - timedelta(days=(5-i)*30)
        month_end = month_start + timedelta(days=30)
        revenue = db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status == 'paid',
            Invoice.paid_date >= month_start,
            Invoice.paid_date < month_end
        ).scalar() or 0
        revenue_data.append({
            'month': month_start.strftime('%b'),
            'revenue': float(revenue)
        })

    # Recent activity
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    recent_tickets = Ticket.query.order_by(desc(Ticket.created_at)).limit(5).all()
    recent_organizations = Organization.query.order_by(desc(Organization.created_at)).limit(5).all()

    return render_template('admin/index.html',
                           stats=stats,
                           user_growth=user_growth,
                           revenue_data=revenue_data,
                           recent_users=recent_users,
                           recent_tickets=recent_tickets,
                           recent_organizations=recent_organizations)


# ==================== USER MANAGEMENT ====================

@admin_bp.route('/users')
@admin_required
@login_required
def users():
    """List all users."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')

    query = User.query

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term)
            )
        )

    if role:
        query = query.join(User.role).filter(Role.name == role)

    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)

    roles = Role.query.all()

    return render_template('admin/users/index.html', users=users, roles=roles, search=search)


@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def user_detail(user_id):
    """View/edit user details."""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            user.first_name = request.form.get('first_name', user.first_name)
            user.last_name = request.form.get('last_name', user.last_name)
            user.email = request.form.get('email', user.email)
            user.is_active = request.form.get('is_active') == 'on'
            user.is_admin = request.form.get('is_admin') == 'on'

            role_id = request.form.get('role_id')
            if role_id:
                user.role_id = role_id

            db.session.commit()
            flash('User updated successfully.', 'success')

        elif action == 'reset_password':
            from werkzeug.security import generate_password_hash
            new_password = request.form.get('new_password')
            if new_password:
                user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Password reset successfully.', 'success')

        elif action == 'deactivate':
            user.is_active = False
            db.session.commit()
            flash('User deactivated.', 'success')

        elif action == 'activate':
            user.is_active = True
            db.session.commit()
            flash('User activated.', 'success')

        return redirect(url_for('admin.user_detail', user_id=user_id))

    # Get user's tickets and projects
    user_tickets = Ticket.query.filter_by(assigned_to=user_id).order_by(Ticket.created_at.desc()).limit(10).all()
    user_projects = Project.query.filter_by(project_manager_id=user_id).order_by(Project.created_at.desc()).limit(5).all()
    time_entries = db.session.query(func.sum(TimeEntry.hours)).filter_by(user_id=user_id).scalar() or 0

    return render_template('admin/users/detail.html',
                           user=user,
                           user_tickets=user_tickets,
                           user_projects=user_projects,
                           time_entries=time_entries)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
@login_required
def new_user():
    """Create a new user."""
    from app.auth.forms import RegisterForm

    form = RegisterForm()

    # Remove terms requirement for admin creation
    del form.terms

    if form.validate_on_submit():
        # Check if email exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already in use.', 'error')
            return render_template('admin/users/new.html', form=form)

        # Create organization if needed
        org = None
        if request.form.get('create_organization'):
            org = Organization(
                name=form.company_name.data or f"{form.first_name.data}'s Organization",
                slug=form.email.data.split('@')[0].lower(),
                subscription_plan=request.form.get('plan', 'starter')
            )
            db.session.add(org)
            db.session.flush()

        user = User(
            organization_id=org.id if org else None,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_active=True,
            is_admin=request.form.get('is_admin') == 'on'
        )
        user.set_password(form.password.data)

        role_id = request.form.get('role_id')
        if role_id:
            user.role_id = role_id

        db.session.add(user)
        db.session.commit()

        flash(f'User {user.email} created successfully.', 'success')
        return redirect(url_for('admin.users'))

    roles = Role.query.all()
    return render_template('admin/users/new.html', form=form, roles=roles)


# ==================== ORGANIZATION MANAGEMENT ====================

@admin_bp.route('/organizations')
@admin_required
@login_required
def organizations():
    """List all organizations."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    plan = request.args.get('plan', '')
    status = request.args.get('status', '')

    query = Organization.query

    if search:
        search_term = f'%{search}%'
        query = query.filter(Organization.name.ilike(search_term))

    if plan:
        query = query.filter_by(subscription_plan=plan)

    if status:
        query = query.filter_by(subscription_status=status)

    organizations = query.order_by(Organization.created_at.desc()).paginate(page=page, per_page=20)

    return render_template('admin/organizations/index.html',
                           organizations=organizations,
                           search=search,
                           plan=plan,
                           status=status)


@admin_bp.route('/organizations/<int:org_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def organization_detail(org_id):
    """View/edit organization details."""
    org = Organization.query.get_or_404(org_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            org.name = request.form.get('name', org.name)
            org.subscription_plan = request.form.get('plan', org.subscription_plan)
            org.subscription_status = request.form.get('status', org.subscription_status)
            org.max_users = request.form.get('max_users', org.max_users, type=int)
            org.max_clients = request.form.get('max_clients', org.max_clients, type=int)
            org.max_projects = request.form.get('max_projects', org.max_projects, type=int)
            org.is_active = request.form.get('is_active') == 'on'

            db.session.commit()
            flash('Organization updated.', 'success')

        elif action == 'update_limits':
            org.max_users = request.form.get('max_users', type=int)
            org.max_clients = request.form.get('max_clients', type=int)
            org.max_projects = request.form.get('max_projects', type=int)
            org.storage_limit_mb = request.form.get('storage_limit_mb', type=int)

            db.session.commit()
            flash('Limits updated.', 'success')

        return redirect(url_for('admin.organization_detail', org_id=org_id))

    # Get organization stats
    stats = {
        'members': User.query.filter_by(organization_id=org_id).count(),
        'clients': db.session.query(func.count()).select_from(db.text('clients')).filter_by(organization_id=org_id).scalar() or 0,
        'tickets': Ticket.query.filter_by(organization_id=org_id).count(),
        'projects': Project.query.filter_by(organization_id=org_id).count(),
        'open_tickets': Ticket.query.filter(
            Ticket.organization_id == org_id,
            Ticket.status.in_(['open', 'in_progress'])
        ).count(),
        'revenue': db.session.query(func.sum(Invoice.total)).filter(
            Invoice.organization_id == org_id,
            Invoice.status == 'paid'
        ).scalar() or 0,
    }

    members = User.query.filter_by(organization_id=org_id).all()

    return render_template('admin/organizations/detail.html',
                           org=org,
                           stats=stats,
                           members=members)


# ==================== BILLING & SUBSCRIPTIONS ====================

@admin_bp.route('/billing')
@admin_required
@login_required
def billing():
    """Admin billing overview."""
    # Get billing stats
    stats = {
        'total_revenue': db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status == 'paid'
        ).scalar() or 0,
        'pending_revenue': db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status.in_(['sent', 'viewed'])
        ).scalar() or 0,
        'overdue_revenue': db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status == 'overdue'
        ).scalar() or 0,
        'active_subscriptions': Subscription.query.filter_by(status='active').count(),
        'total_invoices': Invoice.query.count(),
    }

    # Revenue by plan
    revenue_by_plan = db.session.query(
        Organization.subscription_plan,
        func.sum(Invoice.total)
    ).join(Invoice).filter(
        Invoice.status == 'paid'
    ).group_by(Organization.subscription_plan).all()

    # Recent invoices
    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(20).all()

    # Overdue invoices
    overdue_invoices = Invoice.query.filter_by(status='overdue').order_by(Invoice.due_date).limit(20).all()

    return render_template('admin/billing/index.html',
                           stats=stats,
                           revenue_by_plan=revenue_by_plan,
                           recent_invoices=recent_invoices,
                           overdue_invoices=overdue_invoices)


@admin_bp.route('/billing/subscriptions')
@admin_required
@login_required
def subscriptions():
    """Manage subscriptions."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Subscription.query

    if status:
        query = query.filter_by(status=status)

    subscriptions = query.order_by(Subscription.created_at.desc()).paginate(page=page, per_page=20)

    return render_template('admin/billing/subscriptions.html',
                           subscriptions=subscriptions,
                           status=status)


# ==================== SYSTEM SETTINGS ====================

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
@login_required
def settings():
    """System-wide settings."""
    if request.method == 'POST':
        # Update system settings (these would be stored in a system config table)
        settings = {
            'system_name': request.form.get('system_name'),
            'system_email': request.form.get('system_email'),
            'default_plan': request.form.get('default_plan'),
            'max_users_starter': request.form.get('max_users_starter', type=int),
            'max_users_professional': request.form.get('max_users_professional', type=int),
            'max_users_enterprise': request.form.get('max_users_enterprise', type=int),
            'enable_ai_features': request.form.get('enable_ai_features') == 'on',
            'enable_integrations': request.form.get('enable_integrations') == 'on',
            'require_email_verification': request.form.get('require_email_verification') == 'on',
            'maintenance_mode': request.form.get('maintenance_mode') == 'on',
        }

        # In production, save to a system_config table
        # SystemConfig.set_many(settings)
        flash('Settings updated.', 'success')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings/index.html')


@admin_bp.route('/settings/roles', methods=['GET', 'POST'])
@admin_required
@login_required
def roles():
    """Manage user roles and permissions."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            role = Role(
                name=request.form.get('name'),
                description=request.form.get('description'),
                permissions=request.form.getlist('permissions')
            )
            db.session.add(role)
            db.session.commit()
            flash('Role created.', 'success')

        elif action == 'update':
            role_id = request.form.get('role_id')
            role = Role.query.get_or_404(role_id)
            role.name = request.form.get('name')
            role.description = request.form.get('description')
            role.permissions = request.form.getlist('permissions')
            db.session.commit()
            flash('Role updated.', 'success')

        elif action == 'delete':
            role_id = request.form.get('role_id')
            role = Role.query.get_or_404(role_id)
            if role.users.count() > 0:
                flash('Cannot delete role with assigned users.', 'error')
            else:
                db.session.delete(role)
                db.session.commit()
                flash('Role deleted.', 'success')

        return redirect(url_for('admin.roles'))

    roles = Role.query.all()

    # Available permissions
    permissions = [
        'all', 'tickets', 'projects', 'clients', 'reports', 'team',
        'billing', 'time_tracking', 'view_tickets', 'view_projects', 'view_clients',
        'manage_integrations', 'manage_workflows', 'manage_ai'
    ]

    return render_template('admin/settings/roles.html', roles=roles, permissions=permissions)


# ==================== INTEGRATIONS MANAGEMENT ====================

@admin_bp.route('/integrations')
@admin_required
@login_required
def integrations():
    """Manage system integrations."""
    # Get Composio available integrations
    composio = ComposioService()
    available_integrations = []

    if composio.is_configured():
        try:
            available_integrations = composio.list_integrations()
        except Exception as e:
            flash(f'Could not fetch integrations: {str(e)}', 'warning')

    # Get connected accounts across all organizations
    connected_accounts = ConnectedAccount.query.order_by(ConnectedAccount.created_at.desc()).limit(50).all()

    # Stats
    stats = {
        'total_connections': ConnectedAccount.query.count(),
        'active_connections': ConnectedAccount.query.filter_by(status='active').count(),
        'available_apps': len(available_integrations),
    }

    return render_template('admin/integrations/index.html',
                           available_integrations=available_integrations,
                           connected_accounts=connected_accounts,
                           stats=stats,
                           composio_configured=composio.is_configured())


@admin_bp.route('/integrations/test')
@admin_required
@login_required
def test_integration():
    """Test Composio connection."""
    composio = ComposioService()

    if not composio.is_configured():
        return jsonify({'success': False, 'error': 'Composio not configured'})

    try:
        integrations = composio.list_integrations()
        return jsonify({
            'success': True,
            'count': len(integrations),
            'integrations': integrations[:10]  # First 10
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== ANALYTICS & REPORTS ====================

@admin_bp.route('/analytics')
@admin_required
@login_required
def analytics():
    """System analytics and reports."""
    # Date range
    start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    # User analytics
    user_stats = {
        'total': User.query.count(),
        'new': User.query.filter(User.created_at >= start, User.created_at <= end).count(),
        'active': User.query.filter_by(is_active=True).count(),
    }

    # Organization analytics
    org_stats = {
        'total': Organization.query.count(),
        'new': Organization.query.filter(
            Organization.created_at >= start,
            Organization.created_at <= end
        ).count(),
        'active': Organization.query.filter_by(is_active=True).count(),
        'by_plan': db.session.query(
            Organization.subscription_plan,
            func.count(Organization.id)
        ).group_by(Organization.subscription_plan).all()
    }

    # Ticket analytics
    ticket_stats = {
        'total': Ticket.query.count(),
        'by_status': db.session.query(
            Ticket.status,
            func.count(Ticket.id)
        ).group_by(Ticket.status).all(),
        'by_priority': db.session.query(
            Ticket.priority,
            func.count(Ticket.id)
        ).group_by(Ticket.priority).all(),
        'avg_resolution_time': 0,  # Calculate from resolved tickets
    }

    # Revenue analytics
    revenue_stats = {
        'total': db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status == 'paid',
            Invoice.paid_date >= start,
            Invoice.paid_date <= end
        ).scalar() or 0,
        'by_month': []
    }

    # Monthly breakdown
    for i in range(12):
        month_start = datetime.utcnow() - timedelta(days=(11-i)*30)
        month_end = month_start + timedelta(days=30)
        revenue = db.session.query(func.sum(Invoice.total)).filter(
            Invoice.status == 'paid',
            Invoice.paid_date >= month_start,
            Invoice.paid_date < month_end
        ).scalar() or 0
        revenue_stats['by_month'].append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(revenue)
        })

    return render_template('admin/analytics/index.html',
                           start_date=start_date,
                           end_date=end_date,
                           user_stats=user_stats,
                           org_stats=org_stats,
                           ticket_stats=ticket_stats,
                           revenue_stats=revenue_stats)


@admin_bp.route('/logs')
@admin_required
@login_required
def logs():
    """System activity logs."""
    from app.models.workflow import WorkflowExecution

    page = request.args.get('page', 1, type=int)
    log_type = request.args.get('type', '')

    # Get workflow executions as logs
    logs_query = WorkflowExecution.query

    if log_type:
        logs_query = logs_query.filter_by(status=log_type)

    logs = logs_query.order_by(WorkflowExecution.created_at.desc()).paginate(page=page, per_page=50)

    return render_template('admin/logs.html', logs=logs, log_type=log_type)


# ==================== NOTIFICATION RULES ====================

@admin_bp.route('/notifications')
@admin_required
@login_required
def notification_rules():
    """Manage system-wide notification rules."""
    from app.models.notification import NotificationRule, NotificationLog

    # Get all notification rules
    rules = NotificationRule.query.order_by(NotificationRule.created_at.desc()).all()

    # Get recent notification logs
    recent_logs = NotificationLog.query.order_by(NotificationLog.created_at.desc()).limit(20).all()

    # Stats
    stats = {
        'total_rules': NotificationRule.query.count(),
        'active_rules': NotificationRule.query.filter_by(is_active=True).count(),
        'notifications_sent': NotificationLog.query.filter_by(status='sent').count(),
        'failed_notifications': NotificationLog.query.filter_by(status='failed').count(),
    }

    return render_template('admin/notifications/rules.html',
                           rules=rules,
                           recent_logs=recent_logs,
                           stats=stats)