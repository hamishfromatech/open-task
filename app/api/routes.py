"""API routes for REST API access."""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.ticket import Ticket, TicketComment
from app.models.project import Project, Task, TimeEntry
from app.models.crm import Client, Contact, Lead, Opportunity
from app.models.user import User
from datetime import datetime
from functools import wraps

api_bp = Blueprint('api', __name__)


# API Key authentication decorator
def api_key_required(f):
    """Decorator for API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401

        # Find user by API key
        user = User.query.filter_by(api_key=api_key, is_active=True).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # Set current user for the request
        return f(*args, **kwargs)
    return decorated_function


# ==================== TICKETS API ====================

@api_bp.route('/tickets')
@login_required
def list_tickets():
    """List tickets."""
    org_id = current_user.organization_id

    # Filters
    status = request.args.get('status')
    priority = request.args.get('priority')
    client_id = request.args.get('client_id', type=int)
    assigned_to = request.args.get('assigned_to', type=int)

    query = Ticket.query.filter_by(organization_id=org_id)

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if client_id:
        query = query.filter_by(client_id=client_id)
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    tickets = query.order_by(Ticket.created_at.desc()).paginate(page=page, per_page=per_page)

    return jsonify({
        'tickets': [{
            'id': t.id,
            'ticket_number': t.ticket_number,
            'subject': t.subject,
            'status': t.status,
            'priority': t.priority,
            'category': t.category,
            'client': {'id': t.client.id, 'name': t.client.name} if t.client else None,
            'assignee': {'id': t.assignee.id, 'name': t.assignee.full_name} if t.assignee else None,
            'created_at': t.created_at.isoformat(),
            'updated_at': t.updated_at.isoformat(),
        } for t in tickets.items],
        'total': tickets.total,
        'pages': tickets.pages,
        'current_page': tickets.page
    })


@api_bp.route('/tickets/<int:ticket_id>')
@login_required
def get_ticket(ticket_id):
    """Get ticket details."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    return jsonify({
        'id': ticket.id,
        'ticket_number': ticket.ticket_number,
        'subject': ticket.subject,
        'description': ticket.description,
        'status': ticket.status,
        'priority': ticket.priority,
        'category': ticket.category,
        'ticket_type': ticket.ticket_type,
        'client': {'id': ticket.client.id, 'name': ticket.client.name} if ticket.client else None,
        'contact': {'id': ticket.contact.id, 'name': ticket.contact.full_name} if ticket.contact else None,
        'assignee': {'id': ticket.assignee.id, 'name': ticket.assignee.full_name} if ticket.assignee else None,
        'sla_due_at': ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
        'sla_status': ticket.sla_status,
        'created_at': ticket.created_at.isoformat(),
        'updated_at': ticket.updated_at.isoformat(),
        'comments': [{
            'id': c.id,
            'content': c.content,
            'user': {'id': c.user.id, 'name': c.user.full_name} if c.user else None,
            'is_internal': c.is_internal,
            'created_at': c.created_at.isoformat()
        } for c in ticket.comments]
    })


@api_bp.route('/tickets', methods=['POST'])
@login_required
def create_ticket():
    """Create a new ticket."""
    org_id = current_user.organization_id
    data = request.get_json()

    ticket = Ticket(
        organization_id=org_id,
        ticket_number=Ticket.generate_ticket_number(org_id),
        subject=data['subject'],
        description=data['description'],
        priority=data.get('priority', 'medium'),
        category=data.get('category'),
        ticket_type=data.get('ticket_type', 'incident'),
        client_id=data.get('client_id'),
        contact_id=data.get('contact_id'),
        assigned_to=data.get('assigned_to'),
        source='api',
        created_by=current_user.id
    )
    ticket.calculate_sla()

    db.session.add(ticket)
    db.session.commit()

    return jsonify({
        'id': ticket.id,
        'ticket_number': ticket.ticket_number,
        'message': 'Ticket created successfully'
    }), 201


@api_bp.route('/tickets/<int:ticket_id>', methods=['PUT'])
@login_required
def update_ticket(ticket_id):
    """Update a ticket."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    data = request.get_json()

    if 'status' in data:
        ticket.status = data['status']
    if 'priority' in data:
        ticket.priority = data['priority']
    if 'assigned_to' in data:
        ticket.assigned_to = data['assigned_to']
    if 'category' in data:
        ticket.category = data['category']

    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Ticket updated successfully'})


@api_bp.route('/tickets/<int:ticket_id>/comments', methods=['POST'])
@login_required
def add_ticket_comment(ticket_id):
    """Add a comment to a ticket."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    data = request.get_json()

    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        content=data['content'],
        is_internal=data.get('is_internal', False)
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        'id': comment.id,
        'message': 'Comment added successfully'
    }), 201


# ==================== CLIENTS API ====================

@api_bp.route('/clients')
@login_required
def list_clients():
    """List clients."""
    org_id = current_user.organization_id

    search = request.args.get('search')
    query = Client.query.filter_by(organization_id=org_id)

    if search:
        search_term = f'%{search}%'
        query = query.filter(Client.name.ilike(search_term))

    clients = query.order_by(Client.name).all()

    return jsonify({
        'clients': [{
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'phone': c.phone,
            'status': c.status,
            'client_type': c.client_type
        } for c in clients]
    })


@api_bp.route('/clients/<int:client_id>')
@login_required
def get_client(client_id):
    """Get client details."""
    org_id = current_user.organization_id
    client = Client.query.filter_by(id=client_id, organization_id=org_id).first_or_404()

    return jsonify({
        'id': client.id,
        'name': client.name,
        'email': client.email,
        'phone': client.phone,
        'website': client.website,
        'address': {
            'line1': client.address_line1,
            'line2': client.address_line2,
            'city': client.city,
            'state': client.state,
            'postal_code': client.postal_code,
            'country': client.country
        },
        'industry': client.industry,
        'status': client.status,
        'contacts': [{
            'id': c.id,
            'name': c.full_name,
            'email': c.email,
            'phone': c.phone,
            'is_primary': c.is_primary
        } for c in client.contacts]
    })


# ==================== PROJECTS API ====================

@api_bp.route('/projects')
@login_required
def list_projects():
    """List projects."""
    org_id = current_user.organization_id

    status = request.args.get('status')
    query = Project.query.filter_by(organization_id=org_id)

    if status:
        query = query.filter_by(status=status)

    projects = query.order_by(Project.created_at.desc()).all()

    return jsonify({
        'projects': [{
            'id': p.id,
            'project_number': p.project_number,
            'name': p.name,
            'status': p.status,
            'client': {'id': p.client.id, 'name': p.client.name} if p.client else None,
            'start_date': p.start_date.isoformat() if p.start_date else None,
            'end_date': p.end_date.isoformat() if p.end_date else None,
            'percent_complete': p.percent_complete
        } for p in projects]
    })


@api_bp.route('/projects/<int:project_id>')
@login_required
def get_project(project_id):
    """Get project details."""
    org_id = current_user.organization_id
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()

    return jsonify({
        'id': project.id,
        'project_number': project.project_number,
        'name': project.name,
        'description': project.description,
        'status': project.status,
        'project_type': project.project_type,
        'methodology': project.methodology,
        'client': {'id': project.client.id, 'name': project.client.name} if project.client else None,
        'project_manager': {'id': project.project_manager.id, 'name': project.project_manager.full_name} if project.project_manager else None,
        'start_date': project.start_date.isoformat() if project.start_date else None,
        'end_date': project.end_date.isoformat() if project.end_date else None,
        'budget_hours': project.budget_hours,
        'total_hours_logged': project.total_hours_logged,
        'percent_complete': project.percent_complete
    })


# ==================== TIME TRACKING API ====================

@api_bp.route('/time-entries', methods=['POST'])
@login_required
def log_time():
    """Log time entry."""
    org_id = current_user.organization_id
    data = request.get_json()

    entry = TimeEntry(
        organization_id=org_id,
        user_id=current_user.id,
        project_id=data.get('project_id'),
        task_id=data.get('task_id'),
        ticket_id=data.get('ticket_id'),
        hours=data['hours'],
        description=data.get('description'),
        billable=data.get('billable', True)
    )

    db.session.add(entry)
    db.session.commit()

    return jsonify({
        'id': entry.id,
        'message': 'Time entry logged successfully'
    }), 201


@api_bp.route('/time-entries')
@login_required
def list_time_entries():
    """List time entries."""
    org_id = current_user.organization_id

    user_id = request.args.get('user_id', type=int)
    project_id = request.args.get('project_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = TimeEntry.query.filter_by(organization_id=org_id)

    if user_id:
        query = query.filter_by(user_id=user_id)
    if project_id:
        query = query.filter_by(project_id=project_id)
    if start_date:
        query = query.filter(TimeEntry.created_at >= start_date)
    if end_date:
        query = query.filter(TimeEntry.created_at <= end_date)

    entries = query.order_by(TimeEntry.created_at.desc()).all()

    return jsonify({
        'time_entries': [{
            'id': e.id,
            'user': {'id': e.user.id, 'name': e.user.full_name},
            'hours': e.hours,
            'description': e.description,
            'billable': e.billable,
            'project': {'id': e.project.id, 'name': e.project.name} if e.project else None,
            'ticket': {'id': e.ticket.id, 'number': e.ticket.ticket_number} if e.ticket else None,
            'created_at': e.created_at.isoformat()
        } for e in entries]
    })


# ==================== USER PROFILE API ====================

@api_bp.route('/me')
@login_required
def get_current_user():
    """Get current user profile."""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'full_name': current_user.full_name,
        'job_title': current_user.job_title,
        'timezone': current_user.timezone,
        'is_admin': current_user.is_admin
    })


@api_bp.route('/me/notifications')
@login_required
def get_notifications():
    """Get user notifications."""
    # Would normally come from a notifications table
    return jsonify({'notifications': []})