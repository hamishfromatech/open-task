"""CRM routes - Leads, Opportunities, Clients, Contacts."""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.client import Client, Contact
from app.models.crm import Lead, Opportunity, Activity
from app.models.user import User
from app.crm.forms import ClientForm, ContactForm, LeadForm, OpportunityForm, ActivityForm

crm_bp = Blueprint('crm', __name__)


# ==================== CLIENTS ====================

@crm_bp.route('/clients')
@login_required
def clients():
    """List clients."""
    org_id = current_user.organization_id

    search = request.args.get('search')
    status = request.args.get('status')
    query = Client.query.filter_by(organization_id=org_id)

    if search:
        search_term = f'%{search}%'
        query = query.filter(Client.name.ilike(search_term))

    if status:
        query = query.filter_by(status=status)

    clients = query.order_by(Client.created_at.desc()).all()
    return render_template('crm/clients/index.html', clients=clients)


@crm_bp.route('/clients/new', methods=['GET', 'POST'])
@login_required
def create_client():
    """Create a new client."""
    org_id = current_user.organization_id
    form = ClientForm()

    if form.validate_on_submit():
        client = Client(
            organization_id=org_id,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            website=form.website.data,
            address_line1=form.address_line1.data,
            address_line2=form.address_line2.data,
            city=form.city.data,
            state=form.state.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            industry=form.industry.data,
            notes=form.notes.data,
            client_type=form.client_type.data,
            status=form.status.data
        )

        db.session.add(client)
        db.session.commit()

        flash(f'Client "{client.name}" created successfully.', 'success')
        return redirect(url_for('crm.view_client', client_id=client.id))

    return render_template('crm/clients/create.html', form=form)


@crm_bp.route('/clients/<int:client_id>')
@login_required
def view_client(client_id):
    """View a client."""
    org_id = current_user.organization_id
    client = Client.query.filter_by(id=client_id, organization_id=org_id).first_or_404()

    # Get related data
    contacts = client.contacts.order_by(Contact.is_primary.desc()).all()
    tickets = client.tickets.order_by(Client.tickets).limit(10).all()
    projects = client.projects.limit(10).all()
    opportunities = client.opportunities.order_by(Opportunity.created_at.desc()).limit(5).all()

    return render_template('crm/clients/view.html',
                           client=client,
                           contacts=contacts,
                           tickets=tickets,
                           projects=projects,
                           opportunities=opportunities)


@crm_bp.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    """Edit a client."""
    org_id = current_user.organization_id
    client = Client.query.filter_by(id=client_id, organization_id=org_id).first_or_404()

    form = ClientForm(obj=client)

    if form.validate_on_submit():
        client.name = form.name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.website = form.website.data
        client.address_line1 = form.address_line1.data
        client.address_line2 = form.address_line2.data
        client.city = form.city.data
        client.state = form.state.data
        client.postal_code = form.postal_code.data
        client.country = form.country.data
        client.industry = form.industry.data
        client.notes = form.notes.data
        client.client_type = form.client_type.data
        client.status = form.status.data

        db.session.commit()
        flash('Client updated successfully.', 'success')
        return redirect(url_for('crm.view_client', client_id=client.id))

    return render_template('crm/clients/edit.html', client=client, form=form)


# ==================== CONTACTS ====================

@crm_bp.route('/clients/<int:client_id>/contacts/new', methods=['GET', 'POST'])
@login_required
def create_contact(client_id):
    """Create a new contact for a client."""
    org_id = current_user.organization_id
    client = Client.query.filter_by(id=client_id, organization_id=org_id).first_or_404()

    form = ContactForm()

    if form.validate_on_submit():
        contact = Contact(
            client_id=client.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            mobile=form.mobile.data,
            job_title=form.job_title.data,
            department=form.department.data,
            is_primary=form.is_primary.data,
            notes=form.notes.data
        )

        if form.is_primary.data:
            # Remove primary from other contacts
            Contact.query.filter_by(client_id=client.id).update({'is_primary': False})

        db.session.add(contact)
        db.session.commit()

        flash(f'Contact "{contact.full_name}" created successfully.', 'success')
        return redirect(url_for('crm.view_client', client_id=client.id))

    return render_template('crm/contacts/create.html', client=client, form=form)


# ==================== LEADS ====================

@crm_bp.route('/leads')
@login_required
def leads():
    """List leads."""
    org_id = current_user.organization_id

    status = request.args.get('status')
    search = request.args.get('search')

    query = Lead.query.filter_by(organization_id=org_id)

    if status:
        query = query.filter_by(status=status)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Lead.first_name.ilike(search_term),
                Lead.last_name.ilike(search_term),
                Lead.email.ilike(search_term),
                Lead.company.ilike(search_term)
            )
        )

    leads = query.order_by(Lead.created_at.desc()).all()
    return render_template('crm/leads/index.html', leads=leads)


@crm_bp.route('/leads/new', methods=['GET', 'POST'])
@login_required
def create_lead():
    """Create a new lead."""
    org_id = current_user.organization_id
    form = LeadForm()

    # Populate assignee choices
    users = User.query.filter_by(organization_id=org_id).all()
    form.assigned_to.choices = [(0, '-- Unassigned --)] + [
        (u.id, u.full_name) for u in users
    ]

    if form.validate_on_submit():
        lead = Lead(
            organization_id=org_id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            company=form.company.data,
            job_title=form.job_title.data,
            source=form.source.data,
            status=form.status.data,
            lead_score=form.lead_score.data,
            estimated_value=form.estimated_value.data,
            assigned_to=form.assigned_to.data if form.assigned_to.data else None,
            notes=form.notes.data
        )

        db.session.add(lead)
        db.session.commit()

        flash(f'Lead "{lead.full_name}" created successfully.', 'success')
        return redirect(url_for('crm.view_lead', lead_id=lead.id))

    return render_template('crm/leads/create.html', form=form)


@crm_bp.route('/leads/<int:lead_id>')
@login_required
def view_lead(lead_id):
    """View a lead."""
    org_id = current_user.organization_id
    lead = Lead.query.filter_by(id=lead_id, organization_id=org_id).first_or_404()

    activities = lead.activities.order_by(Activity.created_at.desc()).limit(10).all()

    return render_template('crm/leads/view.html', lead=lead, activities=activities)


@crm_bp.route('/leads/<int:lead_id>/convert', methods=['POST'])
@login_required
def convert_lead(lead_id):
    """Convert a lead to a client and opportunity."""
    org_id = current_user.organization_id
    lead = Lead.query.filter_by(id=lead_id, organization_id=org_id).first_or_404()

    # Create client
    client = Client(
        organization_id=org_id,
        name=lead.company or f"{lead.first_name} {lead.last_name}",
        email=lead.email,
        phone=lead.phone,
        status='active',
        client_type='active'
    )
    db.session.add(client)
    db.session.flush()

    # Create contact
    contact = Contact(
        client_id=client.id,
        first_name=lead.first_name,
        last_name=lead.last_name,
        email=lead.email,
        phone=lead.phone,
        is_primary=True
    )
    db.session.add(contact)
    db.session.flush()

    # Create opportunity
    opportunity = Opportunity(
        organization_id=org_id,
        client_id=client.id,
        lead_id=lead.id,
        name=f"Opportunity - {client.name}",
        amount=lead.estimated_value or 0,
        stage='prospecting',
        owner_id=current_user.id
    )
    db.session.add(opportunity)

    # Update lead status
    lead.status = 'converted'
    lead.converted_at = datetime.utcnow()
    lead.converted_to_opportunity_id = opportunity.id

    db.session.commit()

    flash('Lead converted successfully.', 'success')
    return redirect(url_for('crm.view_opportunity', opportunity_id=opportunity.id))


# ==================== OPPORTUNITIES ====================

@crm_bp.route('/opportunities')
@login_required
def opportunities():
    """List opportunities."""
    org_id = current_user.organization_id

    stage = request.args.get('stage')
    search = request.args.get('search')

    query = Opportunity.query.filter_by(organization_id=org_id)

    if stage:
        query = query.filter_by(stage=stage)

    if search:
        search_term = f'%{search}%'
        query = query.filter(Opportunity.name.ilike(search_term))

    opportunities = query.order_by(Opportunity.created_at.desc()).all()

    # Pipeline stages for kanban view
    stages = [
        {'name': 'prospecting', 'label': 'Prospecting', 'probability': 10},
        {'name': 'qualification', 'label': 'Qualification', 'probability': 25},
        {'name': 'proposal', 'label': 'Proposal', 'probability': 50},
        {'name': 'negotiation', 'label': 'Negotiation', 'probability': 75},
        {'name': 'closed_won', 'label': 'Closed Won', 'probability': 100},
        {'name': 'closed_lost', 'label': 'Closed Lost', 'probability': 0},
    ]

    return render_template('crm/opportunities/index.html',
                           opportunities=opportunities,
                           stages=stages)


@crm_bp.route('/opportunities/new', methods=['GET', 'POST'])
@login_required
def create_opportunity():
    """Create a new opportunity."""
    org_id = current_user.organization_id
    form = OpportunityForm()

    # Populate choices
    clients = Client.query.filter_by(organization_id=org_id).all()
    form.client_id.choices = [(0, '-- Select Client --)] + [
        (c.id, c.name) for c in clients
    ]

    users = User.query.filter_by(organization_id=org_id).all()
    form.owner_id.choices = [(0, '-- Select Owner --)] + [
        (u.id, u.full_name) for u in users
    ]

    if form.validate_on_submit():
        opportunity = Opportunity(
            organization_id=org_id,
            client_id=form.client_id.data if form.client_id.data else None,
            name=form.name.data,
            description=form.description.data,
            amount=form.amount.data,
            stage=form.stage.data,
            probability=form.probability.data,
            expected_close_date=form.expected_close_date.data,
            opportunity_type=form.opportunity_type.data,
            owner_id=form.owner_id.data if form.owner_id.data else None,
            source=form.source.data,
            created_by=current_user.id
        )

        db.session.add(opportunity)
        db.session.commit()

        flash(f'Opportunity "{opportunity.name}" created successfully.', 'success')
        return redirect(url_for('crm.view_opportunity', opportunity_id=opportunity.id))

    return render_template('crm/opportunities/create.html', form=form)


@crm_bp.route('/opportunities/<int:opportunity_id>')
@login_required
def view_opportunity(opportunity_id):
    """View an opportunity."""
    org_id = current_user.organization_id
    opportunity = Opportunity.query.filter_by(id=opportunity_id, organization_id=org_id).first_or_404()

    activities = opportunity.activities.order_by(Activity.created_at.desc()).limit(10).all()

    return render_template('crm/opportunities/view.html',
                           opportunity=opportunity,
                           activities=activities)


@crm_bp.route('/opportunities/<int:opportunity_id>/stage', methods=['POST'])
@login_required
def update_opportunity_stage(opportunity_id):
    """Update opportunity stage (for drag and drop)."""
    org_id = current_user.organization_id
    opportunity = Opportunity.query.filter_by(id=opportunity_id, organization_id=org_id).first_or_404()

    new_stage = request.form.get('stage')
    if new_stage in ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']:
        opportunity.stage = new_stage
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Invalid stage'}), 400