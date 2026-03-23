"""Database initialization script."""

import os
from app import create_app, db
from app.models.user import User, Role
from app.models.organization import Organization, OrganizationSettings
from app.models.integration import Integration
from werkzeug.security import generate_password_hash


def init_db():
    """Initialize the database with default data."""
    app = create_app()
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()

        # Create default roles
        print("Creating default roles...")
        if Role.query.count() == 0:
            roles = [
                Role(
                    name='admin',
                    description='Administrator with full access',
                    permissions=['all']
                ),
                Role(
                    name='manager',
                    description='Manager with team management access',
                    permissions=['tickets', 'projects', 'clients', 'reports', 'team', 'billing']
                ),
                Role(
                    name='agent',
                    description='Agent with limited access',
                    permissions=['tickets', 'clients', 'time_tracking', 'view_projects']
                ),
                Role(
                    name='viewer',
                    description='Read-only access',
                    permissions=['view_tickets', 'view_projects', 'view_clients']
                ),
            ]
            for role in roles:
                db.session.add(role)
            db.session.commit()
            print("✓ Created default roles")

        # Create admin organization and user
        print("Creating admin user...")
        if User.query.filter_by(email='admin@taskflow.local').first() is None:
            # Create organization
            org = Organization(
                name='TaskFlow Demo',
                slug='taskflow-demo',
                email='admin@taskflow.local',
                subscription_plan='enterprise',
                subscription_status='active',
                max_users=100,
                max_clients=1000,
                max_projects=500
            )
            db.session.add(org)
            db.session.flush()

            # Create organization settings
            settings = OrganizationSettings(organization_id=org.id)
            db.session.add(settings)

            # Get admin role
            admin_role = Role.query.filter_by(name='admin').first()

            # Create admin user
            admin = User(
                organization_id=org.id,
                role_id=admin_role.id,
                email='admin@taskflow.local',
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_staff=True,
                email_verified=True
            )
            admin.set_password('admin123')

            db.session.add(admin)
            db.session.commit()
            print("✓ Created admin user (email: admin@taskflow.local, password: admin123)")

        # Create default integrations
        print("Creating default integrations...")
        if Integration.query.count() == 0:
            integrations = [
                Integration(
                    name='Jira',
                    slug='jira',
                    category='development',
                    provider='composio',
                    description='Issue tracking and project management',
                    auth_type='oauth2'
                ),
                Integration(
                    name='Slack',
                    slug='slack',
                    category='communication',
                    provider='composio',
                    description='Team communication and collaboration',
                    auth_type='oauth2'
                ),
                Integration(
                    name='GitHub',
                    slug='github',
                    category='development',
                    provider='composio',
                    description='Version control and collaboration',
                    auth_type='oauth2'
                ),
                Integration(
                    name='Salesforce',
                    slug='salesforce',
                    category='crm',
                    provider='composio',
                    description='Customer relationship management',
                    auth_type='oauth2'
                ),
                Integration(
                    name='HubSpot',
                    slug='hubspot',
                    category='crm',
                    provider='composio',
                    description='Marketing and sales platform',
                    auth_type='oauth2'
                ),
                Integration(
                    name='Microsoft Teams',
                    slug='microsoft_teams',
                    category='communication',
                    provider='composio',
                    description='Team collaboration and communication',
                    auth_type='oauth2'
                ),
                Integration(
                    name='Gmail',
                    slug='gmail',
                    category='communication',
                    provider='composio',
                    description='Email communication',
                    auth_type='oauth2'
                ),
                Integration(
                    name='Google Calendar',
                    slug='google_calendar',
                    category='productivity',
                    provider='composio',
                    description='Calendar and scheduling',
                    auth_type='oauth2'
                ),
                Integration(
                    name='Zendesk',
                    slug='zendesk',
                    category='support',
                    provider='composio',
                    description='Customer support and ticketing',
                    auth_type='oauth2'
                ),
                Integration(
                    name='Asana',
                    slug='asana',
                    category='productivity',
                    provider='composio',
                    description='Project management',
                    auth_type='oauth2'
                ),
            ]
            for integration in integrations:
                db.session.add(integration)
            db.session.commit()
            print("✓ Created default integrations")

        print("\n✅ Database initialized successfully!")
        print("\nYou can now start the application with:")
        print("  python run.py")
        print("\nDefault credentials:")
        print("  Email: admin@taskflow.local")
        print("  Password: admin123")


if __name__ == '__main__':
    init_db()