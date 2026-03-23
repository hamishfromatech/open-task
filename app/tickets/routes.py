"""Ticket routes."""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.ticket import Ticket, TicketComment, TicketHistory, TicketAttachment
from app.models.client import Client, Contact
from app.models.user import User
from app.tickets.forms import TicketForm, TicketCommentForm, TicketFilterForm

tickets_bp = Blueprint('tickets', __name__)


@tickets_bp.route('/')
@login_required
def index():
    """List tickets."""
    org_id = current_user.organization_id

    # Filters
    form = TicketFilterForm(request.args)
    query = Ticket.query.filter_by(organization_id=org_id)

    if form.status.data:
        query = query.filter(Ticket.status.in_(form.status.data))
    if form.priority.data:
        query = query.filter(Ticket.priority.in_(form.priority.data))
    if form.assigned_to.data:
        query = query.filter_by(assigned_to=form.assigned_to.data)
    if form.client_id.data:
        query = query.filter_by(client_id=form.client_id.data)
    if form.search.data:
        search = f'%{form.search.data}%'
        query = query.filter(
            db.or_(
                Ticket.subject.ilike(search),
                Ticket.description.ilike(search),
                Ticket.ticket_number.ilike(search)
            )
        )

    # Sorting
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    sort_column = getattr(Ticket, sort, Ticket.created_at)
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    tickets = query.paginate(page=page, per_page=per_page)

    # Get clients and users for filters
    clients = Client.query.filter_by(organization_id=org_id).all()
    users = User.query.filter_by(organization_id=org_id).all()

    return render_template('tickets/index.html',
                           tickets=tickets,
                           form=form,
                           clients=clients,
                           users=users)


@tickets_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new ticket."""
    org_id = current_user.organization_id
    form = TicketForm()

    # Populate client choices
    form.client_id.choices = [(0, '-- Select Client --)] + [
        (c.id, c.name) for c in Client.query.filter_by(organization_id=org_id).order_by(Client.name).all()
    ]

    if form.validate_on_submit():
        # Generate ticket number
        ticket_number = Ticket.generate_ticket_number(
            org_id,
            prefix='TKT'
        )

        ticket = Ticket(
            organization_id=org_id,
            ticket_number=ticket_number,
            client_id=form.client_id.data if form.client_id.data else None,
            contact_id=form.contact_id.data if form.contact_id.data else None,
            subject=form.subject.data,
            description=form.description.data,
            priority=form.priority.data,
            category=form.category.data,
            ticket_type=form.ticket_type.data,
            source=form.source.data,
            assigned_to=form.assigned_to.data if form.assigned_to.data else None,
            created_by=current_user.id
        )

        # Calculate SLA
        ticket.calculate_sla()

        db.session.add(ticket)
        db.session.commit()

        # Add history entry
        history = TicketHistory(
            ticket_id=ticket.id,
            user_id=current_user.id,
            field_name='status',
            old_value=None,
            new_value='open'
        )
        db.session.add(history)
        db.session.commit()

        flash(f'Ticket {ticket.ticket_number} created successfully.', 'success')
        return redirect(url_for('tickets.view', ticket_id=ticket.id))

    return render_template('tickets/create.html', form=form)


@tickets_bp.route('/<int:ticket_id>')
@login_required
def view(ticket_id):
    """View a ticket."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    # Get comments ordered by creation date
    comments = ticket.comments.order_by(TicketComment.created_at).all()

    # Get history
    history = ticket.history.order_by(TicketHistory.created_at.desc()).limit(20).all()

    # Comment form
    comment_form = TicketCommentForm()

    # Get related entities
    related_tickets = []
    if ticket.client_id:
        related_tickets = Ticket.query.filter(
            Ticket.organization_id == org_id,
            Ticket.client_id == ticket.client_id,
            Ticket.id != ticket.id
        ).order_by(Ticket.created_at.desc()).limit(5).all()

    return render_template('tickets/view.html',
                           ticket=ticket,
                           comments=comments,
                           history=history,
                           comment_form=comment_form,
                           related_tickets=related_tickets)


@tickets_bp.route('/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(ticket_id):
    """Edit a ticket."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    form = TicketForm(obj=ticket)
    form.client_id.choices = [(0, '-- Select Client --)] + [
        (c.id, c.name) for c in Client.query.filter_by(organization_id=org_id).order_by(Client.name).all()
    ]

    if form.validate_on_submit():
        changes = []

        # Track changes
        for field in ['subject', 'description', 'priority', 'status', 'category', 'assigned_to']:
            old_value = getattr(ticket, field)
            new_value = form[field].data
            if old_value != new_value:
                changes.append({
                    'field': field,
                    'old': old_value,
                    'new': new_value
                })
                setattr(ticket, field, new_value)

        ticket.updated_at = datetime.utcnow()

        # Add history entries
        for change in changes:
            history = TicketHistory(
                ticket_id=ticket.id,
                user_id=current_user.id,
                field_name=change['field'],
                old_value=str(change['old']),
                new_value=str(change['new'])
            )
            db.session.add(history)

        db.session.commit()
        flash('Ticket updated successfully.', 'success')
        return redirect(url_for('tickets.view', ticket_id=ticket.id))

    return render_template('tickets/edit.html', ticket=ticket, form=form)


@tickets_bp.route('/<int:ticket_id>/comment', methods=['POST'])
@login_required
def add_comment(ticket_id):
    """Add a comment to a ticket."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    form = TicketCommentForm()
    if form.validate_on_submit():
        comment = TicketComment(
            ticket_id=ticket.id,
            user_id=current_user.id,
            content=form.content.data,
            is_internal=form.is_internal.data
        )

        # If marked as resolution
        if form.mark_as_resolution.data:
            comment.is_resolution = True
            ticket.resolution = form.content.data
            ticket.status = 'resolved'
            ticket.resolved_at = datetime.utcnow()

        db.session.add(comment)
        db.session.commit()

        flash('Comment added successfully.', 'success')

    return redirect(url_for('tickets.view', ticket_id=ticket.id))


@tickets_bp.route('/<int:ticket_id>/status', methods=['POST'])
@login_required
def update_status(ticket_id):
    """Update ticket status."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    new_status = request.form.get('status')
    if new_status in ['open', 'in_progress', 'pending', 'resolved', 'closed', 'cancelled']:
        old_status = ticket.status
        ticket.status = new_status

        if new_status == 'resolved':
            ticket.resolved_at = datetime.utcnow()
        elif new_status == 'closed':
            ticket.closed_at = datetime.utcnow()

        # Add history
        history = TicketHistory(
            ticket_id=ticket.id,
            user_id=current_user.id,
            field_name='status',
            old_value=old_status,
            new_value=new_status
        )
        db.session.add(history)
        db.session.commit()

        flash(f'Ticket status updated to {new_status}.', 'success')

    return redirect(url_for('tickets.view', ticket_id=ticket.id))


@tickets_bp.route('/<int:ticket_id>/assign', methods=['POST'])
@login_required
def assign(ticket_id):
    """Assign ticket to a user."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    assignee_id = request.form.get('assignee_id', type=int)
    old_assignee = ticket.assigned_to
    ticket.assigned_to = assignee_id if assignee_id else None

    # Add history
    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=current_user.id,
        field_name='assigned_to',
        old_value=str(old_assignee) if old_assignee else 'Unassigned',
        new_value=str(assignee_id) if assignee_id else 'Unassigned'
    )
    db.session.add(history)
    db.session.commit()

    flash('Ticket assigned successfully.', 'success')
    return redirect(url_for('tickets.view', ticket_id=ticket.id))


@tickets_bp.route('/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete(ticket_id):
    """Delete a ticket."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    if not current_user.is_admin:
        flash('You do not have permission to delete tickets.', 'error')
        return redirect(url_for('tickets.view', ticket_id=ticket.id))

    ticket_number = ticket.ticket_number
    db.session.delete(ticket)
    db.session.commit()

    flash(f'Ticket {ticket_number} has been deleted.', 'success')
    return redirect(url_for('tickets.index'))


@tickets_bp.route('/api/contacts/<int:client_id>')
@login_required
def get_contacts(client_id):
    """Get contacts for a client (API endpoint)."""
    org_id = current_user.organization_id
    contacts = Contact.query.filter_by(client_id=client_id).all()
    return jsonify([{
        'id': c.id,
        'name': c.full_name,
        'email': c.email,
        'phone': c.phone
    } for c in contacts])