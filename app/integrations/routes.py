"""Integration routes - Composio with auto-auth configuration."""

import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session
from flask_login import login_required, current_user
from app import db
from app.models.integration import Integration, ConnectedAccount, IntegrationEvent
from app.integrations.composio_service import ComposioService, IntegrationActions

integrations_bp = Blueprint('integrations', __name__)


@integrations_bp.route('/')
@login_required
def index():
    """Integrations dashboard."""
    org_id = current_user.organization_id

    # Get connected accounts
    connected_accounts = ConnectedAccount.query.filter_by(
        organization_id=org_id
    ).all()

    # Initialize Composio service
    composio = ComposioService()

    # Get available integrations from Composio
    available_integrations = []
    if composio.is_configured():
        try:
            available_integrations = composio.list_integrations()
        except Exception as e:
            current_app.logger.error(f"Failed to fetch integrations: {e}")
            flash("Could not load available integrations. Check COMPOSIO_API_KEY configuration.", "warning")

    # Group by category
    categories = {}
    for integration in available_integrations:
        category = integration.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(integration)

    # Popular integrations with icons
    popular_integrations = [
        {'slug': 'github', 'name': 'GitHub', 'category': 'Development', 'icon': 'fab fa-github'},
        {'slug': 'slack', 'name': 'Slack', 'category': 'Communication', 'icon': 'fab fa-slack'},
        {'slug': 'jira', 'name': 'Jira', 'category': 'Project Management', 'icon': 'fab fa-jira'},
        {'slug': 'salesforce', 'name': 'Salesforce', 'category': 'CRM', 'icon': 'fab fa-salesforce'},
        {'slug': 'hubspot', 'name': 'HubSpot', 'category': 'CRM', 'icon': 'fab fa-hubspot'},
        {'slug': 'gmail', 'name': 'Gmail', 'category': 'Communication', 'icon': 'fas fa-envelope'},
        {'slug': 'googlecalendar', 'name': 'Google Calendar', 'category': 'Productivity', 'icon': 'fas fa-calendar'},
        {'slug': 'zendesk', 'name': 'Zendesk', 'category': 'Support', 'icon': 'fas fa-headset'},
        {'slug': 'notion', 'name': 'Notion', 'category': 'Productivity', 'icon': 'fas fa-sticky-note'},
        {'slug': 'trello', 'name': 'Trello', 'category': 'Project Management', 'icon': 'fab fa-trello'},
        {'slug': 'asana', 'name': 'Asana', 'category': 'Project Management', 'icon': 'fas fa-tasks'},
        {'slug': 'linear', 'name': 'Linear', 'category': 'Development', 'icon': 'fas fa-code-branch'},
    ]

    return render_template('integrations/index.html',
                           connected_accounts=connected_accounts,
                           categories=categories,
                           popular_integrations=popular_integrations,
                           composio_configured=composio.is_configured())


@integrations_bp.route('/connect/<toolkit_slug>', methods=['GET', 'POST'])
@login_required
def connect(toolkit_slug):
    """
    Initiate connection flow for an integration - AUTO AUTH.

    No need to pre-configure auth_config_id - it's automatically created.
    Just call with the toolkit slug (e.g., 'github', 'slack', 'jira').
    """
    org_id = current_user.organization_id
    user_id = str(current_user.id)

    composio = ComposioService()

    if not composio.is_configured():
        flash('Composio is not configured. Set COMPOSIO_API_KEY environment variable.', 'error')
        return redirect(url_for('integrations.index'))

    # Get or create integration record
    integration = Integration.query.filter_by(slug=toolkit_slug).first()
    if not integration:
        # Get integration info from Composio
        integration_info = composio.get_integration(toolkit_slug)
        integration = Integration(
            name=integration_info.get('name', toolkit_slug.title()) if integration_info else toolkit_slug.title(),
            slug=toolkit_slug,
            category=integration_info.get('category', 'Other') if integration_info else 'Other',
            provider='composio',
        )
        db.session.add(integration)
        db.session.flush()

    # Check for existing active connection
    existing = ConnectedAccount.query.filter_by(
        organization_id=org_id,
        user_id=current_user.id,
        integration_id=integration.id,
        status='active'
    ).first()

    if existing:
        flash(f'You already have an active connection to {integration.name}.', 'info')
        return redirect(url_for('integrations.details', account_id=existing.id))

    try:
        # AUTO-AUTH: This automatically creates auth config if needed
        # No need to set COMPOSIO_AUTH_CONFIG_ID anymore!
        callback_url = url_for('integrations.callback', toolkit=toolkit_slug, _external=True)

        result = composio.initiate_connection(
            user_id=user_id,
            toolkit_slug=toolkit_slug,  # Just pass the toolkit slug!
            callback_url=callback_url
        )

        # Store in session for callback
        session['composio_connection_request_id'] = result['connection_request_id']
        session['composio_integration_id'] = integration.id
        session['composio_auth_config_id'] = result.get('auth_config_id')

        # Redirect to Composio's hosted auth page
        return redirect(result['redirect_url'])

    except Exception as e:
        current_app.logger.error(f"Failed to connect integration: {e}")
        flash(f'Failed to connect {integration.name}: {str(e)}', 'error')
        return redirect(url_for('integrations.index'))


@integrations_bp.route('/callback')
@login_required
def callback():
    """Handle OAuth callback from Composio."""
    org_id = current_user.organization_id

    # Get connection request from session
    connection_request_id = session.pop('composio_connection_request_id', None)
    integration_id = session.pop('composio_integration_id', None)

    if not connection_request_id:
        flash('Connection session expired. Please try again.', 'error')
        return redirect(url_for('integrations.index'))

    composio = ComposioService()

    try:
        # Wait for connection to complete (up to 60 seconds)
        connection_result = composio.wait_for_connection(connection_request_id, timeout=60)

        integration = Integration.query.get(integration_id)
        if not integration:
            flash('Integration not found.', 'error')
            return redirect(url_for('integrations.index'))

        # Save connected account
        connected_account = ConnectedAccount(
            organization_id=org_id,
            user_id=current_user.id,
            integration_id=integration.id,
            connection_id=connection_result['connected_account_id'],
            account_name=integration.name,
            status=connection_result.get('status', 'active')
        )
        db.session.add(connected_account)
        db.session.commit()

        flash(f'Successfully connected {integration.name}!', 'success')
        return redirect(url_for('integrations.details', account_id=connected_account.id))

    except Exception as e:
        current_app.logger.error(f"Failed to complete connection: {e}")
        flash(f'Failed to complete connection: {str(e)}', 'error')
        return redirect(url_for('integrations.index'))


@integrations_bp.route('/disconnect/<int:account_id>', methods=['POST'])
@login_required
def disconnect(account_id):
    """Disconnect an integration."""
    org_id = current_user.organization_id

    connected_account = ConnectedAccount.query.filter_by(
        id=account_id,
        organization_id=org_id
    ).first_or_404()

    composio = ComposioService()

    if composio.is_configured() and connected_account.connection_id:
        try:
            composio.disconnect(connected_account.connection_id)
        except Exception as e:
            current_app.logger.error(f"Failed to disconnect from Composio: {e}")

    connected_account.status = 'revoked'
    db.session.commit()

    flash('Integration disconnected successfully.', 'success')
    return redirect(url_for('integrations.index'))


@integrations_bp.route('/account/<int:account_id>')
@login_required
def details(account_id):
    """View integration details."""
    org_id = current_user.organization_id

    connected_account = ConnectedAccount.query.filter_by(
        id=account_id,
        organization_id=org_id
    ).first_or_404()

    # Get available tools for this integration
    composio = ComposioService()
    tools = []
    triggers = []

    if composio.is_configured():
        try:
            tools = composio.list_tools(connected_account.integration.slug)
            triggers = composio.list_triggers(connected_account.integration.slug)
        except Exception as e:
            current_app.logger.error(f"Failed to get integration details: {e}")

    # Get recent events
    events = IntegrationEvent.query.filter_by(
        connected_account_id=account_id
    ).order_by(IntegrationEvent.created_at.desc()).limit(20).all()

    return render_template('integrations/details.html',
                           account=connected_account,
                           tools=tools,
                           triggers=triggers,
                           events=events)


@integrations_bp.route('/account/<int:account_id>/tools')
@login_required
def list_tools(account_id):
    """List available tools for an integration."""
    org_id = current_user.organization_id

    connected_account = ConnectedAccount.query.filter_by(
        id=account_id,
        organization_id=org_id
    ).first_or_404()

    composio = ComposioService()

    if not composio.is_configured():
        return jsonify({'error': 'Composio not configured'}), 400

    try:
        tools = composio.get_tools_for_user(
            user_id=str(current_user.id),
            toolkits=[connected_account.integration.slug]
        )
        return jsonify({'tools': tools})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@integrations_bp.route('/account/<int:account_id>/execute', methods=['POST'])
@login_required
def execute_tool(account_id):
    """Execute a tool/action on an integration."""
    org_id = current_user.organization_id

    connected_account = ConnectedAccount.query.filter_by(
        id=account_id,
        organization_id=org_id
    ).first_or_404()

    data = request.get_json()
    action_slug = data.get('action')
    arguments = data.get('arguments', {})

    if not action_slug:
        return jsonify({'error': 'Action slug required'}), 400

    composio = ComposioService()

    if not composio.is_configured():
        return jsonify({'error': 'Composio not configured'}), 400

    try:
        result = composio.execute_action(
            user_id=str(current_user.id),
            action_slug=action_slug,
            arguments=arguments
        )

        # Log the execution
        event = IntegrationEvent(
            organization_id=org_id,
            connected_account_id=connected_account.id,
            event_type=f'action.{action_slug}',
            source='manual',
            payload={'arguments': arguments},
            status='processed' if result.get('success') else 'failed',
            result=result
        )
        db.session.add(event)
        db.session.commit()

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== WEBHOOKS ====================

@integrations_bp.route('/webhooks/composio', methods=['POST'])
def composio_webhook():
    """Handle webhooks from Composio triggers."""
    data = request.get_json()

    event_type = data.get('trigger_type') or data.get('event_type')
    connected_account_id = data.get('connected_account_id')
    payload = data.get('payload', {})

    # Find connected account
    connected_account = ConnectedAccount.query.filter_by(
        connection_id=connected_account_id
    ).first()

    if not connected_account:
        current_app.logger.warning(f"Webhook for unknown connection: {connected_account_id}")
        return jsonify({'error': 'Unknown connection'}), 404

    # Log event
    event = IntegrationEvent(
        organization_id=connected_account.organization_id,
        connected_account_id=connected_account.id,
        event_type=event_type,
        event_id=data.get('id'),
        source='composio',
        payload=payload
    )
    db.session.add(event)
    db.session.commit()

    # Process event based on type
    try:
        if event_type and 'ticket' in event_type.lower():
            process_ticket_event(event)
        elif event_type and 'contact' in event_type.lower():
            process_contact_event(event)
        elif event_type and 'issue' in event_type.lower():
            process_issue_event(event)

        event.status = 'processed'
        event.processed_at = datetime.utcnow()

    except Exception as e:
        current_app.logger.error(f"Failed to process webhook: {e}")
        event.status = 'failed'
        event.error_message = str(e)

    db.session.commit()
    return jsonify({'status': 'success'}), 200


def process_ticket_event(event):
    """Process ticket-related events from integrations."""
    from app.models.ticket import Ticket, TicketHistory
    from app.models.client import Client

    payload = event.payload
    action = payload.get('action', 'created')

    if action == 'created':
        # Find or create client
        client_data = payload.get('client', {})
        client = None
        if client_data.get('email'):
            client = Client.query.filter_by(
                organization_id=event.organization_id,
                email=client_data.get('email')
            ).first()

            if not client and client_data.get('name'):
                client = Client(
                    organization_id=event.organization_id,
                    name=client_data.get('name'),
                    email=client_data.get('email'),
                    status='active'
                )
                db.session.add(client)
                db.session.flush()

        # Create ticket
        ticket = Ticket(
            organization_id=event.organization_id,
            client_id=client.id if client else None,
            ticket_number=Ticket.generate_ticket_number(event.organization_id),
            subject=payload.get('subject', 'Imported from Integration'),
            description=payload.get('description', ''),
            priority=payload.get('priority', 'medium'),
            status=payload.get('status', 'open'),
            category=payload.get('category'),
            source='integration',
            external_id=payload.get('id'),
            integration_source=event.source,
            created_by=1  # System user
        )
        db.session.add(ticket)
        db.session.flush()

        event.result = {'ticket_id': ticket.id, 'action': 'created'}


def process_contact_event(event):
    """Process contact-related events from integrations."""
    from app.models.client import Client, Contact

    payload = event.payload
    action = payload.get('action', 'created')

    if action in ['created', 'updated']:
        # Find or create client
        client = None
        if payload.get('company'):
            client = Client.query.filter_by(
                organization_id=event.organization_id,
                name=payload.get('company')
            ).first()

        contact_data = payload.get('contact', payload)

        if contact_data.get('email'):
            contact = Contact.query.filter_by(
                client_id=client.id if client else None,
                email=contact_data.get('email')
            ).first()

            if contact:
                # Update existing contact
                contact.first_name = contact_data.get('first_name', contact.first_name)
                contact.last_name = contact_data.get('last_name', contact.last_name)
            else:
                # Create new contact
                contact = Contact(
                    client_id=client.id if client else None,
                    first_name=contact_data.get('first_name', 'Unknown'),
                    last_name=contact_data.get('last_name', ''),
                    email=contact_data.get('email'),
                    phone=contact_data.get('phone')
                )
                db.session.add(contact)

            event.result = {'contact_id': contact.id, 'action': action}


def process_issue_event(event):
    """Process issue-related events from integrations like GitHub/Jira."""
    from app.models.project import Task

    payload = event.payload
    action = payload.get('action', 'created')

    if action == 'created':
        # Create task from issue
        task = Task(
            organization_id=event.organization_id,
            title=payload.get('title', 'Imported Issue'),
            description=payload.get('description', payload.get('body', '')),
            status='not_started' if payload.get('state') == 'open' else 'completed',
            external_id=payload.get('id'),
            created_by=1  # System user
        )
        db.session.add(task)
        db.session.flush()

        event.result = {'task_id': task.id, 'action': 'created'}