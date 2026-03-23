"""Notification routes - Triggers and alerts."""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.notification import NotificationRule, NotificationLog, NotificationPreference
from app.models.integration import ConnectedAccount
from app.integrations.composio_service import ComposioService, IntegrationActions, TriggerDefinitions

notifications_bp = Blueprint('notifications', __name__)

# Mapping of internal trigger types to Composio event slugs
TRIGGER_TO_COMPOSIO = {
    'ticket_created': None,  # Internal event, handle directly
    'ticket_status_changed': None,
    'ticket_priority_changed': None,
    'ticket_assigned': None,
    'ticket_resolved': None,
    'sla_breach_warning': None,
    'sla_breached': None,
    'project_created': None,
    'project_completed': None,
    'task_assigned': None,
    'lead_created': None,
    'lead_converted': None,
    'opportunity_won': None,
    'opportunity_lost': None,
    'invoice_created': None,
    'invoice_paid': None,
    'invoice_overdue': None,
    # Composio triggers
    'github_issue_created': TriggerDefinitions.GITHUB_ISSUE_CREATED,
    'github_pr_opened': TriggerDefinitions.GITHUB_PR_OPENED,
    'slack_message': TriggerDefinitions.SLACK_MESSAGE_RECEIVED,
    'jira_issue_created': TriggerDefinitions.JIRA_ISSUE_CREATED,
    'hubspot_contact_created': TriggerDefinitions.HUBSPOT_CONTACT_CREATED,
    'hubspot_deal_created': TriggerDefinitions.HUBSPOT_DEAL_CREATED,
}


@notifications_bp.route('/rules')
@login_required
def rules():
    """List notification rules."""
    org_id = current_user.organization_id

    rules = NotificationRule.query.filter_by(organization_id=org_id).order_by(NotificationRule.created_at.desc()).all()

    # Get connected accounts for display
    connected_accounts = ConnectedAccount.query.filter_by(organization_id=org_id, status='active').all()

    return render_template('notifications/rules.html',
                           rules=rules,
                           connected_accounts=connected_accounts)


@notifications_bp.route('/rules/new', methods=['GET', 'POST'])
@login_required
def create_rule():
    """Create a new notification rule."""
    org_id = current_user.organization_id

    if request.method == 'POST':
        rule = NotificationRule(
            organization_id=org_id,
            created_by=current_user.id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            trigger_type=request.form.get('trigger_type'),
            trigger_conditions=request.form.get('conditions', {}),
            channels=request.form.get('channels', []),
            connected_account_ids=request.form.getlist('connected_accounts'),
            message_template=request.form.get('message_template'),
            is_active=request.form.get('is_active') == 'on'
        )

        db.session.add(rule)
        db.session.commit()

        flash('Notification rule created successfully.', 'success')
        return redirect(url_for('notifications.rules'))

    # Get available trigger types
    trigger_types = [
        {'value': 'ticket_created', 'label': 'When a ticket is created', 'category': 'Tickets'},
        {'value': 'ticket_status_changed', 'label': 'When ticket status changes', 'category': 'Tickets'},
        {'value': 'ticket_priority_changed', 'label': 'When ticket priority changes', 'category': 'Tickets'},
        {'value': 'ticket_assigned', 'label': 'When a ticket is assigned', 'category': 'Tickets'},
        {'value': 'ticket_resolved', 'label': 'When a ticket is resolved', 'category': 'Tickets'},
        {'value': 'sla_breach_warning', 'label': 'SLA breach warning (2 hours before)', 'category': 'Tickets'},
        {'value': 'sla_breached', 'label': 'When SLA is breached', 'category': 'Tickets'},
        {'value': 'project_created', 'label': 'When a project is created', 'category': 'Projects'},
        {'value': 'project_completed', 'label': 'When a project is completed', 'category': 'Projects'},
        {'value': 'task_assigned', 'label': 'When a task is assigned', 'category': 'Projects'},
        {'value': 'lead_created', 'label': 'When a lead is created', 'category': 'CRM'},
        {'value': 'lead_converted', 'label': 'When a lead is converted', 'category': 'CRM'},
        {'value': 'opportunity_won', 'label': 'When an opportunity is won', 'category': 'CRM'},
        {'value': 'opportunity_lost', 'label': 'When an opportunity is lost', 'category': 'CRM'},
        {'value': 'invoice_created', 'label': 'When an invoice is created', 'category': 'Billing'},
        {'value': 'invoice_paid', 'label': 'When an invoice is paid', 'category': 'Billing'},
        {'value': 'invoice_overdue', 'label': 'When an invoice is overdue', 'category': 'Billing'},
    ]

    # Get connected accounts
    connected_accounts = ConnectedAccount.query.filter_by(organization_id=org_id, status='active').all()

    return render_template('notifications/create_rule.html',
                           trigger_types=trigger_types,
                           connected_accounts=connected_accounts)


@notifications_bp.route('/rules/<int:rule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rule(rule_id):
    """Edit a notification rule."""
    org_id = current_user.organization_id
    rule = NotificationRule.query.filter_by(id=rule_id, organization_id=org_id).first_or_404()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            rule.name = request.form.get('name')
            rule.description = request.form.get('description')
            rule.trigger_type = request.form.get('trigger_type')
            rule.trigger_conditions = request.form.get('conditions', {})
            rule.channels = request.form.get('channels', [])
            rule.connected_account_ids = request.form.getlist('connected_accounts')
            rule.message_template = request.form.get('message_template')
            rule.is_active = request.form.get('is_active') == 'on'

            db.session.commit()
            flash('Notification rule updated.', 'success')

        elif action == 'toggle':
            rule.is_active = not rule.is_active
            db.session.commit()
            flash(f'Notification rule {"enabled" if rule.is_active else "disabled"}.', 'success')

        elif action == 'delete':
            db.session.delete(rule)
            db.session.commit()
            flash('Notification rule deleted.', 'success')
            return redirect(url_for('notifications.rules'))

        return redirect(url_for('notifications.edit_rule', rule_id=rule.id))

    trigger_types = [
        {'value': 'ticket_created', 'label': 'When a ticket is created', 'category': 'Tickets'},
        {'value': 'ticket_status_changed', 'label': 'When ticket status changes', 'category': 'Tickets'},
        {'value': 'ticket_priority_changed', 'label': 'When ticket priority changes', 'category': 'Tickets'},
        {'value': 'ticket_assigned', 'label': 'When a ticket is assigned', 'category': 'Tickets'},
        {'value': 'ticket_resolved', 'label': 'When a ticket is resolved', 'category': 'Tickets'},
        {'value': 'sla_breach_warning', 'label': 'SLA breach warning', 'category': 'Tickets'},
        {'value': 'sla_breached', 'label': 'When SLA is breached', 'category': 'Tickets'},
        {'value': 'project_created', 'label': 'When a project is created', 'category': 'Projects'},
        {'value': 'project_completed', 'label': 'When a project is completed', 'category': 'Projects'},
        {'value': 'lead_created', 'label': 'When a lead is created', 'category': 'CRM'},
        {'value': 'opportunity_won', 'label': 'When an opportunity is won', 'category': 'CRM'},
        {'value': 'invoice_created', 'label': 'When an invoice is created', 'category': 'Billing'},
        {'value': 'invoice_paid', 'label': 'When an invoice is paid', 'category': 'Billing'},
    ]

    connected_accounts = ConnectedAccount.query.filter_by(organization_id=org_id, status='active').all()

    return render_template('notifications/edit_rule.html',
                           rule=rule,
                           trigger_types=trigger_types,
                           connected_accounts=connected_accounts)


@notifications_bp.route('/logs')
@login_required
def logs():
    """View notification logs."""
    org_id = current_user.organization_id

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    channel = request.args.get('channel')

    query = NotificationLog.query.filter_by(organization_id=org_id)

    if status:
        query = query.filter_by(status=status)
    if channel:
        query = query.filter_by(channel=channel)

    logs = query.order_by(NotificationLog.created_at.desc()).paginate(page=page, per_page=50)

    return render_template('notifications/logs.html', logs=logs, status=status, channel=channel)


@notifications_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """User notification preferences."""
    org_id = current_user.organization_id

    prefs = NotificationPreference.query.filter_by(
        user_id=current_user.id,
        organization_id=org_id
    ).first()

    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id, organization_id=org_id)
        db.session.add(prefs)
        db.session.commit()

    if request.method == 'POST':
        prefs.email_ticket_created = request.form.get('email_ticket_created') == 'on'
        prefs.email_ticket_assigned = request.form.get('email_ticket_assigned') == 'on'
        prefs.email_ticket_resolved = request.form.get('email_ticket_resolved') == 'on'
        prefs.email_sla_warning = request.form.get('email_sla_warning') == 'on'
        prefs.email_sla_breach = request.form.get('email_sla_breach') == 'on'
        prefs.email_project_updates = request.form.get('email_project_updates') == 'on'
        prefs.email_invoice_updates = request.form.get('email_invoice_updates') == 'on'
        prefs.email_daily_digest = request.form.get('email_daily_digest') == 'on'
        prefs.email_weekly_report = request.form.get('email_weekly_report') == 'on'
        prefs.in_app_tickets = request.form.get('in_app_tickets') == 'on'
        prefs.in_app_projects = request.form.get('in_app_projects') == 'on'
        prefs.in_app_mentions = request.form.get('in_app_mentions') == 'on'
        prefs.slack_user_id = request.form.get('slack_user_id')
        prefs.teams_user_id = request.form.get('teams_user_id')
        prefs.digest_time = request.form.get('digest_time', '09:00')
        prefs.timezone = request.form.get('timezone', 'UTC')

        db.session.commit()
        flash('Notification preferences updated.', 'success')
        return redirect(url_for('notifications.preferences'))

    return render_template('notifications/preferences.html', prefs=prefs)


# ==================== COMPOSIO TRIGGER SUBSCRIPTIONS ====================

@notifications_bp.route('/triggers/available')
@login_required
def available_triggers():
    """Get available Composio triggers."""
    composio = ComposioService()

    if not composio.is_configured():
        return jsonify({'error': 'Composio not configured'}), 400

    toolkit = request.args.get('toolkit')

    try:
        triggers = composio.list_available_triggers(toolkit_slug=toolkit)
        return jsonify({'triggers': triggers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/triggers/subscribe', methods=['POST'])
@login_required
def subscribe_trigger():
    """Subscribe to a Composio trigger event."""
    org_id = current_user.organization_id
    data = request.get_json()

    event_slug = data.get('event_slug')
    filters = data.get('filters', [])
    rule_id = data.get('rule_id')  # Link to notification rule

    if not event_slug:
        return jsonify({'error': 'event_slug required'}), 400

    composio = ComposioService()

    if not composio.is_configured():
        return jsonify({'error': 'Composio not configured'}), 400

    try:
        result = composio.subscribe_trigger(
            event_slug=event_slug,
            filters=filters
        )

        # Link to notification rule if provided
        if rule_id:
            rule = NotificationRule.query.filter_by(id=rule_id, organization_id=org_id).first()
            if rule:
                # Store subscription ID in rule metadata
                if not rule.metadata:
                    rule.metadata = {}
                rule.metadata['composio_subscription_id'] = result.get('id')
                db.session.commit()

        return jsonify({
            'success': True,
            'subscription': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/triggers/unsubscribe', methods=['POST'])
@login_required
def unsubscribe_trigger():
    """Unsubscribe from a Composio trigger."""
    data = request.get_json()
    subscription_id = data.get('subscription_id')

    if not subscription_id:
        return jsonify({'error': 'subscription_id required'}), 400

    composio = ComposioService()

    if not composio.is_configured():
        return jsonify({'error': 'Composio not configured'}), 400

    try:
        success = composio.unsubscribe_trigger(subscription_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== COMPOSIO WEBHOOK HANDLER ====================

@notifications_bp.route('/webhook/composio', methods=['POST'])
def composio_webhook():
    """
    Handle webhook events from Composio triggers.

    Configure this URL in Composio dashboard:
    https://platform.composio.dev/settings/webhook

    The webhook URL should be: https://your-domain.com/notifications/webhook/composio
    """
    data = request.get_json()

    # Log the incoming webhook
    current_app.logger.info(f"Received Composio webhook: {data.get('type')}")

    # Extract event details
    event_type = data.get('type')
    event_data = data.get('data', {})
    timestamp = data.get('timestamp')
    log_id = data.get('log_id')

    # Find matching notification rules
    rules = NotificationRule.query.filter_by(
        trigger_type=event_type,
        is_active=True
    ).all()

    for rule in rules:
        try:
            # Process the webhook based on trigger type
            result = process_composio_webhook(rule, event_type, event_data)

            # Log the notification
            log = NotificationLog(
                organization_id=rule.organization_id,
                rule_id=rule.id,
                trigger_type=event_type,
                trigger_data=event_data,
                channel='webhook',
                status='sent' if result.get('success') else 'failed',
                error_message=result.get('error') if not result.get('success') else None,
                sent_at=datetime.utcnow()
            )
            db.session.add(log)

            # Update rule stats
            rule.trigger_count += 1
            rule.last_triggered_at = datetime.utcnow()

        except Exception as e:
            current_app.logger.error(f"Error processing webhook for rule {rule.id}: {e}")
            # Log failure
            log = NotificationLog(
                organization_id=rule.organization_id,
                rule_id=rule.id,
                trigger_type=event_type,
                trigger_data=event_data,
                channel='webhook',
                status='failed',
                error_message=str(e)
            )
            db.session.add(log)

    db.session.commit()

    return jsonify({'status': 'received'}), 200


def process_composio_webhook(rule, event_type, event_data):
    """Process a webhook event and send notifications based on rule."""
    from app.notifications.routes import send_notification

    # Build entity from event data
    entity = build_entity_from_webhook(event_type, event_data)

    if not entity:
        return {'success': False, 'error': 'Could not build entity from webhook'}

    # Send notifications based on rule channels
    results = []
    for channel_config in rule.channels:
        channel_type = channel_config.get('type')

        try:
            if channel_type == 'slack':
                result = send_to_slack_channel(rule, channel_config, entity, event_type)
            elif channel_type == 'teams':
                result = send_to_teams_channel(rule, channel_config, entity, event_type)
            elif channel_type == 'email':
                result = send_to_email(rule, channel_config, entity, event_type)
            elif channel_type == 'webhook':
                result = send_to_webhook_url(rule, channel_config, entity, event_type)
            else:
                result = {'success': False, 'error': f'Unknown channel type: {channel_type}'}

            results.append(result)

        except Exception as e:
            results.append({'success': False, 'error': str(e)})

    # Return overall success
    success = all(r.get('success', False) for r in results)
    return {
        'success': success,
        'results': results
    }


def build_entity_from_webhook(event_type, event_data):
    """Build a generic entity object from webhook data."""
    class WebhookEntity:
        def __init__(self, data):
            self.id = data.get('id')
            self.type = data.get('type')
            self.data = data
            # Common fields
            self.subject = data.get('subject') or data.get('title') or data.get('name')
            self.description = data.get('description') or data.get('body') or data.get('content')
            self.status = data.get('status')
            self.priority = data.get('priority')
            self.created_at = data.get('created_at') or data.get('timestamp')

    return WebhookEntity(event_data)


# ==================== NOTIFICATION SENDING ====================

def send_notification(rule, entity, entity_type):
    """
    Send notification based on rule.

    Args:
        rule: NotificationRule object
        entity: The entity that triggered the notification
        entity_type: Type of entity (ticket, project, etc.)

    Returns:
        bool: True if notification was sent successfully
    """
    from app import create_app
    app = create_app()

    with app.app_context():
        composio = ComposioService()

        # Build message from template
        message = render_message_template(rule.message_template, entity, entity_type)

        # Send to each channel
        for channel_config in rule.channels:
            channel_type = channel_config.get('type')
            result = None

            try:
                if channel_type == 'slack':
                    result = send_to_slack(composio, rule, channel_config, message, entity)
                elif channel_type == 'teams':
                    result = send_to_teams(composio, rule, channel_config, message, entity)
                elif channel_type == 'email':
                    result = send_to_email(rule, channel_config, message, entity)
                elif channel_type == 'webhook':
                    result = send_to_webhook(rule, channel_config, message, entity)
                elif channel_type == 'gmail':
                    result = send_to_gmail(composio, rule, channel_config, message, entity)

                # Log success
                log = NotificationLog(
                    organization_id=rule.organization_id,
                    rule_id=rule.id,
                    trigger_type=rule.trigger_type,
                    trigger_entity_type=entity_type,
                    trigger_entity_id=entity.id,
                    channel=channel_type,
                    recipient=channel_config.get('recipient', ''),
                    message=message,
                    status='sent',
                    sent_at=datetime.utcnow()
                )
                db.session.add(log)

            except Exception as e:
                current_app.logger.error(f"Failed to send notification: {e}")
                # Log failure
                log = NotificationLog(
                    organization_id=rule.organization_id,
                    rule_id=rule.id,
                    trigger_type=rule.trigger_type,
                    trigger_entity_type=entity_type,
                    trigger_entity_id=entity.id,
                    channel=channel_type,
                    recipient=channel_config.get('recipient', ''),
                    message=message,
                    status='failed',
                    error_message=str(e)
                )
                db.session.add(log)

        # Update rule stats
        rule.trigger_count += 1
        rule.last_triggered_at = datetime.utcnow()
        db.session.commit()

        return True


def send_to_slack(composio, rule, channel_config, message, entity):
    """Send notification to Slack."""
    account_id = channel_config.get('connected_account_id')
    channel = channel_config.get('channel', '#general')

    # Find connected account
    account = ConnectedAccount.query.get(account_id)
    if not account:
        raise ValueError("Slack account not connected")

    actions = IntegrationActions(composio)
    return actions.send_slack_message(
        user_id=str(rule.created_by),
        channel=channel,
        message=message
    )


def send_to_teams(composio, rule, channel_config, message, entity):
    """Send notification to Microsoft Teams."""
    webhook_url = channel_config.get('webhook_url')

    if not webhook_url:
        raise ValueError("Teams webhook URL not configured")

    # Post to Teams webhook
    import requests
    payload = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": None,
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [{
                    "type": "TextBlock",
                    "text": message
                }]
            }
        }]
    }

    return requests.post(webhook_url, json=payload)


def send_to_email(rule, channel_config, message, entity):
    """Send notification via email."""
    from flask_mail import Message
    from app import mail

    recipients = channel_config.get('recipients', [])
    subject = channel_config.get('subject', f'Notification: {rule.name}')

    msg = Message(
        subject=subject,
        recipients=recipients,
        body=message
    )

    mail.send(msg)
    return {'success': True}


def send_to_webhook(rule, channel_config, message, entity):
    """Send notification to custom webhook."""
    import requests

    url = channel_config.get('url')
    method = channel_config.get('method', 'POST')

    payload = {
        'rule_id': rule.id,
        'rule_name': rule.name,
        'trigger_type': rule.trigger_type,
        'entity_type': entity.__class__.__name__,
        'entity_id': entity.id,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }

    headers = channel_config.get('headers', {})

    if method == 'POST':
        return requests.post(url, json=payload, headers=headers)
    else:
        return requests.get(url, params=payload, headers=headers)


def send_to_gmail(composio, rule, channel_config, message, entity):
    """Send notification via Gmail."""
    account_id = channel_config.get('connected_account_id')
    to = channel_config.get('to')
    subject = channel_config.get('subject', f'Notification: {rule.name}')

    account = ConnectedAccount.query.get(account_id)
    if not account:
        raise ValueError("Gmail account not connected")

    actions = IntegrationActions(composio)
    return actions.send_gmail(
        user_id=str(rule.created_by),
        to=to,
        subject=subject,
        body=message
    )


def render_message_template(template, entity, entity_type):
    """Render message template with entity data."""
    if not template:
        # Default template
        template = "🔔 {{entity_type}}: {{entity_name}}\n\n{{message}}"

    # Build context
    context = {
        'entity_type': entity_type,
        'entity_id': entity.id,
        'entity_name': getattr(entity, 'name', None) or getattr(entity, 'subject', None) or getattr(entity, 'title', str(entity.id)),
        'message': getattr(entity, 'description', ''),
    }

    # Add entity-specific fields
    if entity_type == 'ticket':
        context.update({
            'ticket_number': entity.ticket_number,
            'subject': entity.subject,
            'priority': entity.priority,
            'status': entity.status,
            'client': entity.client.name if entity.client else 'N/A',
            'url': f'/tickets/{entity.id}'
        })
    elif entity_type == 'project':
        context.update({
            'project_number': entity.project_number,
            'name': entity.name,
            'status': entity.status,
            'url': f'/projects/{entity.id}'
        })
    elif entity_type == 'opportunity':
        context.update({
            'name': entity.name,
            'amount': f"${entity.amount:,.2f}",
            'stage': entity.stage,
            'url': f'/crm/opportunities/{entity.id}'
        })
    elif entity_type == 'invoice':
        context.update({
            'invoice_number': entity.invoice_number,
            'amount': f"${entity.total:,.2f}",
            'status': entity.status,
            'url': f'/billing/invoices/{entity.id}'
        })

    # Simple template rendering
    message = template
    for key, value in context.items():
        message = message.replace('{{' + key + '}}', str(value) if value else '')

    return message