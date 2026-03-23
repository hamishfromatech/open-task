"""Composio integration service - With auto auth configuration."""

import os
from typing import Dict, List, Optional
from flask import current_app

# Composio Python SDK
from composio import Composio


class ComposioService:
    """Service class for Composio API operations using the official Python SDK.

    This service supports auto-configuration of auth configs using Composio's
    managed authentication. You can either:
    1. Use Composio's managed auth (default - no setup required)
    2. Use custom OAuth credentials (set env vars for each integration)
    """

    def __init__(self):
        """Initialize Composio client."""
        self.api_key = os.environ.get('COMPOSIO_API_KEY')
        self.client = Composio(api_key=self.api_key) if self.api_key else None
        self._auth_configs_cache = {}  # Cache auth configs by toolkit

    def is_configured(self) -> bool:
        """Check if Composio is properly configured."""
        return self.client is not None

    def _get_or_create_auth_config(self, toolkit_slug: str) -> Optional[str]:
        """
        Get or create an auth config for a toolkit.

        Uses Composio's managed auth by default, or creates from custom credentials
        if environment variables are set.

        Args:
            toolkit_slug: The toolkit/integration slug (e.g., 'github', 'slack')

        Returns:
            Auth config ID or None if not configured
        """
        if not self.is_configured():
            return None

        # Check cache first
        if toolkit_slug in self._auth_configs_cache:
            return self._auth_configs_cache[toolkit_slug]

        # Check for existing auth config in database
        from app.models.integration import Integration
        from app import db

        integration = Integration.query.filter_by(slug=toolkit_slug).first()
        if integration and integration.metadata and integration.metadata.get('auth_config_id'):
            self._auth_configs_cache[toolkit_slug] = integration.metadata['auth_config_id']
            return integration.metadata['auth_config_id']

        # Check for custom OAuth credentials in environment
        client_id = os.environ.get(f'COMPOSIO_{toolkit_slug.upper()}_CLIENT_ID')
        client_secret = os.environ.get(f'COMPOSIO_{toolkit_slug.upper()}_CLIENT_SECRET')

        try:
            if client_id and client_secret:
                # Create auth config with custom credentials
                auth_config = self.client.auth_configs.create(
                    toolkit=toolkit_slug,
                    name=f"{toolkit_slug.title()} Auth",
                    auth_scheme="OAUTH2",
                    credentials={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "oauth_redirect_uri": "https://backend.composio.dev/api/v3/toolkits/auth/callback",
                    }
                )
                auth_config_id = auth_config.id
            else:
                # Use Composio's managed/default auth - list existing or use default
                # Composio provides default auth configs for most popular integrations
                auth_config_id = self._get_default_auth_config(toolkit_slug)

            # Cache and save
            self._auth_configs_cache[toolkit_slug] = auth_config_id

            # Save to integration metadata
            if integration:
                if not integration.metadata:
                    integration.metadata = {}
                integration.metadata['auth_config_id'] = auth_config_id
                db.session.commit()

            return auth_config_id

        except Exception as e:
            current_app.logger.error(f"Failed to create auth config for {toolkit_slug}: {e}")
            return None

    def _get_default_auth_config(self, toolkit_slug: str) -> Optional[str]:
        """
        Get default auth config from Composio for a toolkit.

        Composio provides managed auth configs for most integrations.
        This tries to find existing auth configs or uses a toolkit-based approach.
        """
        try:
            # List existing auth configs
            auth_configs = self.client.auth_configs.list()

            # Find matching auth config for this toolkit
            for config in auth_configs:
                if hasattr(config, 'toolkit') and config.toolkit == toolkit_slug:
                    return config.id
                elif config.get('toolkit') == toolkit_slug:
                    return config['id']

            # If no existing config, try to create one using Composio's managed auth
            # This uses Composio's default OAuth credentials
            auth_config = self.client.auth_configs.create(
                toolkit=toolkit_slug,
                name=f"{toolkit_slug.title()} (Managed)",
                auth_scheme="OAUTH2",
                # When no credentials provided, Composio uses their managed auth
            )
            return auth_config.id

        except Exception as e:
            current_app.logger.error(f"Failed to get default auth config: {e}")
            return None

    def list_integrations(self, category: str = None) -> List[Dict]:
        """List available integrations/toolkits."""
        if not self.is_configured():
            return []

        try:
            # Get all available toolkits
            toolkits = self.client.toolkits.list()

            result = []
            for toolkit in toolkits:
                toolkit_data = {
                    'slug': toolkit.slug if hasattr(toolkit, 'slug') else toolkit.get('slug'),
                    'name': toolkit.name if hasattr(toolkit, 'name') else toolkit.get('name'),
                    'description': toolkit.description if hasattr(toolkit, 'description') else toolkit.get('description'),
                    'category': toolkit.category if hasattr(toolkit, 'category') else toolkit.get('category'),
                    'logo': toolkit.logo if hasattr(toolkit, 'logo') else toolkit.get('logo'),
                    'auth_schemes': toolkit.auth_schemes if hasattr(toolkit, 'auth_schemes') else toolkit.get('auth_schemes', ['OAUTH2']),
                }

                # Filter by category if specified
                if category and toolkit_data.get('category') != category:
                    continue

                result.append(toolkit_data)

            return result
        except Exception as e:
            current_app.logger.error(f"Failed to list integrations: {e}")
            return []

    def get_integration(self, toolkit_slug: str) -> Optional[Dict]:
        """Get details of a specific integration/toolkit."""
        if not self.is_configured():
            return None

        try:
            toolkit = self.client.toolkits.get(toolkit_slug)
            return {
                'slug': toolkit.slug,
                'name': toolkit.name,
                'description': toolkit.description,
                'category': toolkit.category,
                'tools': self.list_tools(toolkit_slug),
                'triggers': self.list_triggers(toolkit_slug),
            }
        except Exception as e:
            current_app.logger.error(f"Failed to get integration {toolkit_slug}: {e}")
            return None

    def list_tools(self, toolkit_slug: str) -> List[Dict]:
        """List available tools/actions for a toolkit."""
        if not self.is_configured():
            return []

        try:
            tools = self.client.tools.get(toolkits=[toolkit_slug])
            return [
                {
                    'slug': tool.slug if hasattr(tool, 'slug') else tool.get('slug'),
                    'name': tool.name if hasattr(tool, 'name') else tool.get('name'),
                    'description': tool.description if hasattr(tool, 'description') else tool.get('description'),
                }
                for tool in tools
            ]
        except Exception as e:
            current_app.logger.error(f"Failed to list tools for {toolkit_slug}: {e}")
            return []

    def list_triggers(self, toolkit_slug: str) -> List[Dict]:
        """List available triggers/webhooks for a toolkit."""
        if not self.is_configured():
            return []

        try:
            triggers = self.client.triggers.list(toolkits=[toolkit_slug])
            return [
                {
                    'slug': trigger.slug if hasattr(trigger, 'slug') else trigger.get('slug'),
                    'name': trigger.name if hasattr(trigger, 'name') else trigger.get('name'),
                    'description': trigger.description if hasattr(trigger, 'description') else trigger.get('description'),
                }
                for trigger in triggers
            ]
        except Exception as e:
            current_app.logger.error(f"Failed to list triggers for {toolkit_slug}: {e}")
            return []

    def initiate_connection(self, user_id: str, toolkit_slug: str, callback_url: str = None) -> Dict:
        """
        Initiate OAuth connection flow for a user - AUTO AUTH CONFIG.

        This method automatically gets or creates the auth config for the toolkit,
        so you don't need to manage auth_config_ids manually.

        Args:
            user_id: Unique identifier for the user in your app
            toolkit_slug: The integration to connect (e.g., 'github', 'slack')
            callback_url: URL to redirect after successful auth

        Returns:
            Dict with redirect_url and connection_request_id
        """
        if not self.is_configured():
            raise ValueError("Composio is not configured. Set COMPOSIO_API_KEY environment variable.")

        # Auto-get or create auth config
        auth_config_id = self._get_or_create_auth_config(toolkit_slug)

        if not auth_config_id:
            raise ValueError(f"Could not create auth config for {toolkit_slug}. Check COMPOSIO_API_KEY.")

        try:
            connection_request = self.client.connected_accounts.initiate(
                user_id=user_id,
                auth_config_id=auth_config_id,
                callback_url=callback_url
            )

            return {
                'redirect_url': connection_request.redirect_url,
                'connection_request_id': connection_request.id,
                'auth_config_id': auth_config_id,
            }
        except Exception as e:
            current_app.logger.error(f"Failed to initiate connection: {e}")
            raise

    def connect_toolkit(self, user_id: str, toolkit_slug: str, callback_url: str = None) -> Dict:
        """
        Alias for initiate_connection - connects a user to a toolkit.

        Args:
            user_id: Unique identifier for the user
            toolkit_slug: Integration to connect (e.g., 'github', 'slack', 'jira')
            callback_url: Optional callback URL

        Returns:
            Dict with redirect_url and connection_request_id
        """
        return self.initiate_connection(user_id, toolkit_slug, callback_url)

    def wait_for_connection(self, connection_request_id: str, timeout: int = 300) -> Dict:
        """
        Wait for a connection to be established.

        Args:
            connection_request_id: ID from initiate_connection
            timeout: Maximum seconds to wait

        Returns:
            Dict with connection details
        """
        if not self.is_configured():
            raise ValueError("Composio is not configured.")

        try:
            connected_account = self.client.connected_accounts.wait_for_connection(
                connection_request_id,
                timeout=timeout
            )

            return {
                'connected_account_id': connected_account.id,
                'status': connected_account.status if hasattr(connected_account, 'status') else 'active',
            }
        except Exception as e:
            current_app.logger.error(f"Failed to wait for connection: {e}")
            raise

    def get_connection(self, connected_account_id: str) -> Optional[Dict]:
        """Get connection details by ID."""
        if not self.is_configured():
            return None

        try:
            account = self.client.connected_accounts.get(connected_account_id)
            return {
                'id': account.id,
                'status': account.status if hasattr(account, 'status') else 'active',
                'toolkit_slug': account.toolkit_slug if hasattr(account, 'toolkit_slug') else None,
            }
        except Exception as e:
            current_app.logger.error(f"Failed to get connection: {e}")
            return None

    def list_connections(self, user_id: str = None) -> List[Dict]:
        """List all connections for a user."""
        if not self.is_configured():
            return []

        try:
            if user_id:
                accounts = self.client.connected_accounts.list(user_id=user_id)
            else:
                accounts = self.client.connected_accounts.list()

            return [
                {
                    'id': account.id,
                    'status': account.status if hasattr(account, 'status') else 'active',
                    'toolkit_slug': account.toolkit_slug if hasattr(account, 'toolkit_slug') else None,
                }
                for account in accounts
            ]
        except Exception as e:
            current_app.logger.error(f"Failed to list connections: {e}")
            return []

    def disconnect(self, connected_account_id: str) -> bool:
        """Disconnect/delete a connected account."""
        if not self.is_configured():
            return False

        try:
            self.client.connected_accounts.delete(connected_account_id)
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to disconnect: {e}")
            return False

    def execute_action(self, user_id: str, action_slug: str, arguments: Dict) -> Dict:
        """
        Execute a tool/action on a connected integration.

        Args:
            user_id: User ID who has the connected account
            action_slug: The action to execute (e.g., "GITHUB_STAR_A_REPOSITORY")
            arguments: Arguments for the action

        Returns:
            Dict with execution result
        """
        if not self.is_configured():
            raise ValueError("Composio is not configured.")

        try:
            result = self.client.tools.execute(
                user_id=user_id,
                slug=action_slug,
                arguments=arguments
            )

            return {
                'success': True,
                'data': result.data if hasattr(result, 'data') else result,
            }
        except Exception as e:
            current_app.logger.error(f"Failed to execute action {action_slug}: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    def get_tools_for_user(self, user_id: str, toolkits: List[str] = None, search: str = None) -> List[Dict]:
        """Get available tools for a user, optionally filtered."""
        if not self.is_configured():
            return []

        try:
            kwargs = {'user_id': user_id}
            if toolkits:
                kwargs['toolkits'] = toolkits
            if search:
                kwargs['search'] = search

            tools = self.client.tools.get(**kwargs)

            return [
                {
                    'slug': tool.slug if hasattr(tool, 'slug') else tool.get('slug'),
                    'name': tool.name if hasattr(tool, 'name') else tool.get('name'),
                    'description': tool.description if hasattr(tool, 'description') else tool.get('description'),
                }
                for tool in tools
            ]
        except Exception as e:
            current_app.logger.error(f"Failed to get tools: {e}")
            return []

    def list_available_triggers(self, toolkit_slug: str = None) -> List[Dict]:
        """
        List available triggers for a toolkit.

        Args:
            toolkit_slug: Optional toolkit to filter triggers

        Returns:
            List of available triggers
        """
        if not self.is_configured():
            return []

        try:
            if toolkit_slug:
                triggers = self.client.triggers.list(toolkits=[toolkit_slug])
            else:
                triggers = self.client.triggers.list()

            return [
                {
                    'slug': trigger.slug if hasattr(trigger, 'slug') else trigger.get('slug'),
                    'name': trigger.name if hasattr(trigger, 'name') else trigger.get('name'),
                    'description': trigger.description if hasattr(trigger, 'description') else trigger.get('description'),
                    'toolkit': trigger.toolkit if hasattr(trigger, 'toolkit') else trigger.get('toolkit'),
                }
                for trigger in triggers
            ]
        except Exception as e:
            current_app.logger.error(f"Failed to list triggers: {e}")
            return []

    def subscribe_trigger(self, event_slug: str, filters: List[Dict] = None) -> Dict:
        """
        Subscribe to a trigger event.

        For production webhooks, configure your webhook URL in Composio dashboard:
        https://platform.composio.dev/settings/webhook

        Args:
            event_slug: The trigger event slug (e.g., 'GITHUB_COMMIT_EVENT', 'SLACK_MESSAGE_RECEIVED')
            filters: Optional list of filters - all must match for subscription

        Returns:
            Dict with subscription details

        Example filters:
            filters=[
                {"field": "repository.name", "operator": "EQUALS", "value": "my-repo"}
            ]
        """
        if not self.is_configured():
            raise ValueError("Composio is not configured.")

        try:
            subscription = self.client.triggers.subscribe(
                event_slug=event_slug,
                filters=filters or []
            )

            return {
                'id': subscription.id if hasattr(subscription, 'id') else None,
                'event_slug': event_slug,
                'status': 'active',
            }
        except Exception as e:
            current_app.logger.error(f"Failed to subscribe to trigger {event_slug}: {e}")
            raise

    def subscribe_multiple_triggers(self, event_slugs: List[str], filters: List[Dict] = None) -> Dict:
        """
        Subscribe to multiple trigger events (OR logic between events, AND logic for filters).

        Args:
            event_slugs: List of trigger event slugs (e.g., ['ISSUE_CREATED_EVENT', 'PR_OPENED_EVENT'])
            filters: Optional list of filters

        Returns:
            Dict with subscription details
        """
        if not self.is_configured():
            raise ValueError("Composio is not configured.")

        try:
            subscription = self.client.triggers.subscribe(
                event_slugs=event_slugs,
                filters=filters or []
            )

            return {
                'id': subscription.id if hasattr(subscription, 'id') else None,
                'event_slugs': event_slugs,
                'status': 'active',
            }
        except Exception as e:
            current_app.logger.error(f"Failed to subscribe to triggers: {e}")
            raise

    def unsubscribe_trigger(self, subscription_id: str) -> bool:
        """Unsubscribe from a trigger."""
        if not self.is_configured():
            return False

        try:
            self.client.triggers.unsubscribe(subscription_id)
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to unsubscribe: {e}")
            return False


class TriggerDefinitions:
    """Common trigger event slugs for popular integrations."""

    # GitHub triggers
    GITHUB_COMMIT_EVENT = "GITHUB_COMMIT_EVENT"
    GITHUB_ISSUE_CREATED = "GITHUB_ISSUE_CREATED_EVENT"
    GITHUB_ISSUE_CLOSED = "GITHUB_ISSUE_CLOSED_EVENT"
    GITHUB_PR_OPENED = "GITHUB_PULL_REQUEST_OPENED_EVENT"
    GITHUB_PR_MERGED = "GITHUB_PULL_REQUEST_MERGED_EVENT"
    GITHUB_PUSH_EVENT = "GITHUB_PUSH_EVENT"

    # Slack triggers
    SLACK_MESSAGE_RECEIVED = "SLACK_MESSAGE_RECEIVED_EVENT"
    SLACK_CHANNEL_CREATED = "SLACK_CHANNEL_CREATED_EVENT"
    SLACK_USER_JOINED = "SLACK_USER_JOINED_EVENT"

    # Jira triggers
    JIRA_ISSUE_CREATED = "JIRA_ISSUE_CREATED_EVENT"
    JIRA_ISSUE_UPDATED = "JIRA_ISSUE_UPDATED_EVENT"
    JIRA_ISSUE_STATUS_CHANGED = "JIRA_ISSUE_STATUS_CHANGED_EVENT"

    # HubSpot triggers
    HUBSPOT_CONTACT_CREATED = "HUBSPOT_CONTACT_CREATED_EVENT"
    HUBSPOT_DEAL_CREATED = "HUBSPOT_DEAL_CREATED_EVENT"
    HUBSPOT_DEAL_STAGE_CHANGED = "HUBSPOT_DEAL_STAGE_CHANGED_EVENT"

    # Salesforce triggers
    SALESFORCE_LEAD_CREATED = "SALESFORCE_LEAD_CREATED_EVENT"
    SALESFORCE_OPPORTUNITY_CREATED = "SALESFORCE_OPPORTUNITY_CREATED_EVENT"
    SALESFORCE_CASE_CREATED = "SALESFORCE_CASE_CREATED_EVENT"

    # Gmail triggers
    GMAIL_EMAIL_RECEIVED = "GMAIL_EMAIL_RECEIVED_EVENT"

    # Notion triggers
    NOTION_PAGE_CREATED = "NOTION_PAGE_CREATED_EVENT"
    NOTION_PAGE_UPDATED = "NOTION_PAGE_UPDATED_EVENT"

    # Linear triggers
    LINEAR_ISSUE_CREATED = "LINEAR_ISSUE_CREATED_EVENT"
    LINEAR_ISSUE_UPDATED = "LINEAR_ISSUE_UPDATED_EVENT"


class IntegrationActions:
    """Helper class for common integration actions."""

    def __init__(self, composio_service: ComposioService):
        self.composio = composio_service

    def create_github_issue(self, user_id: str, owner: str, repo: str, title: str, body: str = None) -> Dict:
        """Create a GitHub issue."""
        return self.composio.execute_action(
            user_id=user_id,
            action_slug="GITHUB_CREATE_AN_ISSUE",
            arguments={
                'owner': owner,
                'repo': repo,
                'title': title,
                'body': body or '',
            }
        )

    def send_slack_message(self, user_id: str, channel: str, message: str) -> Dict:
        """Send a Slack message."""
        return self.composio.execute_action(
            user_id=user_id,
            action_slug="SLACK_SEND_A_MESSAGE_TO_A_CHANNEL",
            arguments={
                'channel': channel,
                'text': message,
            }
        )

    def create_jira_ticket(self, user_id: str, project_key: str, summary: str, description: str = None, issue_type: str = "Task") -> Dict:
        """Create a Jira ticket."""
        return self.composio.execute_action(
            user_id=user_id,
            action_slug="JIRA_CREATE_ISSUE",
            arguments={
                'project_key': project_key,
                'summary': summary,
                'description': description or '',
                'issue_type': issue_type,
            }
        )

    def create_hubspot_contact(self, user_id: str, email: str, first_name: str = None, last_name: str = None) -> Dict:
        """Create a HubSpot contact."""
        return self.composio.execute_action(
            user_id=user_id,
            action_slug="HUBSPOT_CREATE_CONTACT",
            arguments={
                'email': email,
                'firstname': first_name or '',
                'lastname': last_name or '',
            }
        )

    def send_gmail(self, user_id: str, to: str, subject: str, body: str) -> Dict:
        """Send an email via Gmail."""
        return self.composio.execute_action(
            user_id=user_id,
            action_slug="GMAIL_SEND_EMAIL",
            arguments={
                'to': to,
                'subject': subject,
                'body': body,
            }
        )