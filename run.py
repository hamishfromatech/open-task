#!/usr/bin/env python3
"""
Main entry point for TaskFlow PSA application.
"""

import os
from app import create_app, db
from app.models.user import User, Role
from app.models.organization import Organization, OrganizationSettings
from app.models.client import Client, Contact
from app.models.ticket import Ticket
from app.models.project import Project, Task
from app.models.crm import Lead, Opportunity
from app.models.billing import Invoice
from app.models.integration import Integration
from app.models.workflow import Workflow

app = create_app()

# Shell context for flask shell
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Organization': Organization,
        'OrganizationSettings': OrganizationSettings,
        'Client': Client,
        'Contact': Contact,
        'Ticket': Ticket,
        'Project': Project,
        'Task': Task,
        'Lead': Lead,
        'Opportunity': Opportunity,
        'Invoice': Invoice,
        'Integration': Integration,
        'Workflow': Workflow,
    }


if __name__ == '__main__':
    with app.app_context():
        # Create tables
        db.create_all()

        # Create default roles if they don't exist
        if Role.query.count() == 0:
            roles = [
                Role(name='admin', description='Administrator with full access',
                     permissions=['all']),
                Role(name='manager', description='Manager with team management access',
                     permissions=['tickets', 'projects', 'clients', 'reports', 'team']),
                Role(name='agent', description='Agent with limited access',
                     permissions=['tickets', 'clients', 'time_tracking']),
                Role(name='viewer', description='Read-only access',
                     permissions=['view_tickets', 'view_projects', 'view_clients']),
            ]
            for role in roles:
                db.session.add(role)
            db.session.commit()
            print("Created default roles")

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)