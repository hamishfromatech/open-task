# TaskFlow PSA

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-red.svg)](https://palletsprojects.com/p/flask/)
[![Docker](https://img.shields.io/badge/Docker-ready-success)](https://www.docker.com/)

Professional Services Automation (PSA) Platform - A comprehensive, AI-powered alternative to Autotask, built with Flask and modern technologies.

![TaskFlow Dashboard](https://img.shields.io/badge/Dashboard-Interactive-success)
![Ticketing](https://img.shields.io/badge/Ticketing-ITIL--aligned-blue)
![CRM](https://img.shields.io/badge/CRM-Sales--pipeline-green)

## 🌟 Features

### 🎯 Service Desk & Ticketing
- ITIL-aligned ticket management with full lifecycle tracking
- SLA monitoring with automated status calculations (on_track, at_risk, breached)
- Priority-based response times (critical: 4h, high: 8h, medium: 24h, low: 72h)
- Multi-channel ticket creation (portal, email, phone, chat, API)
- Internal notes and client-facing comments
- Ticket attachments and history tracking
- Satisfaction surveys and ratings

### 📊 Project Management
- Kanban, Scrum, and Waterfall methodology support
- Project phases and milestones
- Task assignment and tracking with dependencies
- Time tracking with billable/non-billable options
- Budget management (hours and fixed amounts)
- Progress visualization with percent completion
- Resource allocation and workload tracking

### 💼 CRM & Sales Pipeline
- Lead management with scoring and qualification
- Opportunity tracking with stage-based probability
- Activity/interaction logging (calls, emails, meetings)
- Client and contact management
- Revenue forecasting with weighted opportunity values
- Campaign tracking and source attribution
- Competitor analysis and win/loss tracking

### 💰 Billing & Invoicing
- Stripe-powered payment processing
- Automated invoice generation from time entries
- Subscription management for recurring billing
- Multiple billing models (hourly, fixed, retainer)
- Tax calculation and discount support
- Payment history and receipt generation
- Overdue invoice tracking and reminders

### 🤖 AI Assistant (OpenAI)
- Smart ticket response suggestions
- Automated ticket categorization
- AI-powered ticket assignment recommendations
- Dashboard summary generation
- Business insights and trend analysis
- Lead scoring and qualification
- Opportunity win probability analysis
- Workflow automation suggestions
- Natural language search
- Content generation (emails, responses)

### 🔌 850+ Integrations (Composio)
- **Development**: GitHub, GitLab, Jira, Linear, Bitbucket
- **Communication**: Slack, Microsoft Teams, Gmail, Zoom
- **CRM**: Salesforce, HubSpot, Pipedrive
- **Productivity**: Google Calendar, Notion, Trello, Asana
- **Support**: Zendesk, Freshdesk
- **Auto-auth configuration** - Connect integrations with a single click

### 🔔 Notification System
- Real-time notifications via websockets
- Customizable notification rules and triggers
- Email notifications for critical events
- Push notifications to connected integrations (Slack, Teams)
- Notification preferences per user
- Notification history and tracking
- SLA breach warnings and alerts

### ⚙️ Workflow Automation
- Trigger-based automated actions
- Custom workflow rules
- Email notifications and alerts
- Scheduled tasks with Celery
- Webhook support for external integrations

### 👥 Role-Based Access Control
- **Admin**: Full system access
- **Manager**: Team management, all tickets/projects, billing
- **Agent**: Ticket handling, client management, time tracking
- **Viewer**: Read-only access to tickets, projects, clients

## 🏗️ Tech Stack

### Backend
- **Framework**: Python 3.11+, Flask 3.0.0
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **Authentication**: Flask-Login, bcrypt, JWT tokens
- **Background Jobs**: Celery 5.3.6 + Redis
- **Forms**: Flask-WTF
- **Email**: Flask-Mail
- **Migrations**: Flask-Migrate + Alembic

### Frontend
- **Templates**: Jinja2
- **Styling**: TailwindCSS
- **Interactivity**: Alpine.js
- **Charts**: Chart.js

### DevOps & Infrastructure
- **Containerization**: Docker, Docker Compose
- **Web Server**: Gunicorn (production)
- **Reverse Proxy**: Nginx (production)
- **Email Testing**: Mailhog
- **Monitoring**: Health checks, logging

### Third-Party Services
- **AI**: OpenAI Compatible with Ollama, LM Studio, Llama.cpp and vLLM.
- **Payments**: Stripe
- **Integrations**: Composio Dev (850+ apps)


## 🚀 Quick Start

### Option 1: Docker (Recommended for All Environments)

1. **Clone the repository**
   ```bash
   git clone https://github.com/hamishfromatech/taskflow-psa.git
   cd taskflow-psa
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker-compose exec web python init_db.py
   ```

5. **Access the application**
   - Web interface: http://localhost:5000
   - Mailhog (email testing): http://localhost:8025

**Default credentials:**

### Option 2: Manual Installation (Development)

1. **Prerequisites**
   - Python 3.11+
   - PostgreSQL 15+
   - Redis (for Celery)
   - SMTP server or Mailhog

2. **Clone and setup**
   ```bash
   git clone https://github.com/hamishfromatech/taskflow-psa.git
   cd taskflow-psa
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Environment Variables**

| Variable | Description | Required |
|----------|-------------|----------|
| `FLASK_APP` | Application entry point | Yes |
| `FLASK_ENV` | Environment (development/production) | Yes |
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `SQLALCHEMY_DATABASE_URI` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI Assistant | Yes |
| `STRIPE_SECRET_KEY` | Stripe API secret key | Yes |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | Yes |
| `COMPOSIO_API_KEY` | Composio API key | Yes |
| `SMTP_SERVER` | SMTP server address | Yes |
| `SMTP_PORT` | SMTP server port | Yes |
| `SMTP_USER` | SMTP username | Yes |
| `SMTP_PASSWORD` | SMTP password | Yes |
| `SMTP_FROM_EMAIL` | Default from email | Yes |

### Example `.env` File

See `.env.example` for a complete template with all available options:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
FLASK_APP=app/main.py
FLASK_ENV=development
DEBUG=True

# Database
DATABASE_URL=postgresql://taskflow:taskflow@db:5432/taskflow

# Redis
REDIS_URL=redis://redis:6379/0

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview

# SMTP Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@taskflow.com

# Application Settings
APP_NAME=TaskFlow PSA
APP_URL=http://localhost:5000
SUPPORT_EMAIL=support@taskflow.com

# Feature Flags
ENABLE_AI_FEATURES=True
ENABLE_INTEGRATIONS=True
```

6. **Initialize the database**
   ```bash
   python init_db.py
   ```

6. **Start the application**
   ```bash
   python run.py
   ```

7. **Start Celery worker** (in separate terminal)
   ```bash
   celery -A app.celery_app.celery worker --loglevel=info
   ```

8. **Start Celery beat** (for scheduled tasks)
   ```bash
   celery -A app.celery_app.celery beat --loglevel=info
   ```

**Default credentials:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/hamishfromatech/taskflow-psa.git
   cd taskflow-psa
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker-compose exec web python init_db.py
   ```

5. **Access the application**
   - Web interface: http://localhost:5000
   - Mailhog (email testing): http://localhost:8025

**Default credentials:**
- Email: `admin@taskflow.local`
- Password: `admin123`

### Option 2: Local Development

1. **Clone and set up virtual environment**
   ```bash
   git clone https://github.com/hamishfromatech/taskflow-psa.git
   cd taskflow-psa

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at http://localhost:5000

## 📋 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `REDIS_URL` | Redis connection for caching/Celery | Yes | redis://localhost:6379/0 |
| `FLASK_APP` | Flask application entry point | No | app/main.py |
| `FLASK_ENV` | Environment (development/production) | No | development |
| `DEBUG` | Enable debug mode | No | True |
| `STRIPE_SECRET_KEY` | Stripe API secret key | Yes | - |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | Yes | - |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes | - |
| `OPENAI_MODEL` | OpenAI model to use | No | gpt-4-turbo-preview |
| `COMPOSIO_API_KEY` | Composio Dev API key for integrations | Yes | - |
| `MAIL_SERVER` | SMTP server for emails | No | mailhog |
| `MAIL_PORT` | SMTP port | No | 1025 |
| `MAIL_USERNAME` | SMTP username | No | - |
| `MAIL_PASSWORD` | SMTP password | No | - |
| `APP_NAME` | Application name | No | TaskFlow PSA |
| `APP_URL` | Application URL | No | http://localhost:5000 |

## 📁 Project Structure

```
autotask/
├── app/                          # Application package
│   ├── __init__.py              # App factory and extensions
│   ├── celery_app.py            # Celery configuration and tasks
│   ├── admin/                   # Admin dashboard routes
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── ai_assistant/            # OpenAI integration
│   │   ├── __init__.py
│   │   ├── openai_service.py    # AI service layer
│   │   └── routes.py
│   ├── api/                     # REST API endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── auth/                    # Authentication
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── forms.py
│   │   ├── routes.py
│   │   └── user_loader.py
│   ├── billing/                 # Billing and invoicing
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   ├── routes.py
│   │   └── stripe_service.py
│   ├── crm/                     # CRM functionality
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── integrations/            # External integrations
│   │   ├── __init__.py
│   │   ├── composio_service.py
│   │   └── routes.py
│   ├── main/                    # Main application routes
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── billing.py
│   │   ├── client.py
│   │   ├── crm.py
│   │   ├── integration.py
│   │   ├── notification.py
│   │   ├── organization.py
│   │   ├── project.py
│   │   ├── ticket.py
│   │   ├── user.py
│   │   └── workflow.py
│   ├── notifications/           # Notification system
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── projects/                # Project management
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── tickets/                 # Ticket management
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── decorators.py
│       ├── error_handlers.py
│       └── helpers.py
├── migrations/                  # Database migrations
├── templates/                   # Jinja2 templates
├── static/                      # Static assets (CSS, JS, images)
├── .env.example                 # Environment variables template
├── docker-compose.yml           # Docker configuration
├── Dockerfile                   # Docker image definition
├── init_db.py                   # Database initialization script
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
└── README.md                    # This file
```

## 🔧 Database Migrations

The application uses Flask-Migrate with Alembic for database schema management.

### Common Migration Commands

```bash
# Generate a new migration
flask db migrate -m "Description of changes"

# Review the generated migration
# Check migrations/versions/ folder

# Apply migrations to the database
flask db upgrade

# Rollback to previous migration
flask db downgrade

# View current migration status
flask db current

# View migration history
flask db history
```

### When to Run Migrations
- After changing model definitions in `app/models/`
- When adding new models
- When modifying relationships between models

## 🔌 API Documentation

The REST API is available at `/api/` prefix. All endpoints require authentication via Flask-Login or API key.

### Authentication

- **Session Authentication**: Use Flask-Login session (for web interface)
- **API Key Authentication**: Include `X-API-Key` header with your API key
- **Obtain API Key**: Generate in `/settings/api` after logging in

### Error Responses

| Status Code | Description |
|-------------|-------------|
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 422 | Validation Error - Invalid request data |
| 500 | Internal Server Error |

### Notifications API

- `GET /api/notifications` - Get user notifications with pagination
- `GET /api/notifications/unread` - Get unread notifications count
- `PUT /api/notifications/<id>/read` - Mark notification as read
- `PUT /api/notifications/read-all` - Mark all notifications as read
- `DELETE /api/notifications/<id>` - Delete a notification

### Webhooks

The system supports webhooks for external integration:

- **Ticket Events**: created, updated, status_changed, assigned, resolved
- **Project Events**: created, updated, completed
- **CRM Events**: lead_created, opportunity_won, client_updated
- **Billing Events**: invoice_created, invoice_paid, payment_received

Configure webhooks in the admin panel or via the `/api/webhooks` endpoint.

### Available Endpoints

#### Tickets
- `GET /api/tickets` - List tickets with filters and pagination
- `GET /api/tickets/<id>` - Get ticket details
- `POST /api/tickets` - Create a new ticket
- `PUT /api/tickets/<id>` - Update a ticket
- `POST /api/tickets/<id>/comments` - Add a comment

#### Clients
- `GET /api/clients` - List clients
- `GET /api/clients/<id>` - Get client details

#### Projects
- `GET /api/projects` - List projects
- `GET /api/projects/<id>` - Get project details

#### Time Tracking
- `POST /api/time-entries` - Log time entry
- `GET /api/time-entries` - List time entries

#### User
- `GET /api/me` - Get current user profile
- `GET /api/me/notifications` - Get user notifications

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run linter
flake8 app/

# Run specific test file
pytest tests/test_features.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "ticket or project"
```

### Test Coverage

The application maintains high test coverage for critical functionality:

| Module | Coverage Goal | Status |
|--------|--------------|--------|
| `app/models/` | 90% | ✅ |
| `app/api/` | 85% | ✅ |
| `app/auth/` | 95% | ✅ |
| `app/ai_assistant/` | 80% | 🔄 |
| `app/integrations/` | 75% | 🔄 |

### Writing Tests

- Use Pytest framework
- Follow arrange-act-assert pattern
- Mock external dependencies
- Test both happy paths and edge cases
- Use fixtures for test data

```python
# Example test
def test_create_ticket():
    client = app.test_client()
    response = client.post('/api/tickets', json={
        'title': 'Test Ticket',
        'description': 'Test description'
    })
    assert response.status_code == 201
    assert response.json['title'] == 'Test Ticket'
```

## 📊 Database Models

### Core Models
- **User** - Authentication and user profiles
- **Role** - RBAC permissions
- **Organization** - Multi-tenant organization
- **OrganizationSettings** - Per-organization configuration

### Service Desk
- **Ticket** - Service tickets with SLA tracking
- **TicketComment** - Comments and internal notes
- **TicketAttachment** - File attachments
- **TicketHistory** - Audit trail

### Projects
- **Project** - Project management
- **ProjectPhase** - Project phases/milestones
- **Task** - Tasks with dependencies
- **TimeEntry** - Time tracking

### CRM
- **Client** - Client companies
- **Contact** - Contact persons
- **Lead** - Lead/prospect management
- **Opportunity** - Sales opportunities
- **Activity** - Interactions and activities

### Billing
- **Invoice** - Invoices with Stripe integration
- **InvoiceItem** - Invoice line items
- **Payment** - Payment records
- **Subscription** - Recurring subscriptions

### Notifications
- **NotificationRule** - Custom notification rules and triggers
- **NotificationLog** - Notification delivery history
- **NotificationPreference** - User notification preferences

### Integrations
- **Integration** - Integration definitions
- **ConnectedAccount** - User-connected accounts
- **IntegrationEvent** - Webhook events

### Workflows
- **Workflow** - Workflow definitions
- **WorkflowExecution** - Workflow execution history

## 👨‍💼 Admin Panel

The admin panel (`/admin`) provides system-level management capabilities:

### User Management
- Create, edit, and delete users
- Assign roles and permissions
- View user activity logs
- Reset user passwords
- Enable/disable accounts

### Organization Management
- Create and configure organizations
- Set organization-wide settings
- Manage organization-level integrations
- Monitor resource usage

### Integration Management
- Configure integration credentials
- Enable/disable integrations
- View integration status and logs
- Manage connected accounts

### Notification Rules
- Create custom notification rules
- Configure trigger conditions
- Set notification channels (email, Slack, Teams)
- Test notification rules

### System Settings
- Email configuration
- SMTP settings
- AI model configuration
- SLA policy settings
- Invoice and billing settings

## 🔧 Troubleshooting

### Common Issues

#### Docker Issues

**Issue**: Container won't start
- Solution: Check logs with `docker-compose logs web`

**Issue**: Database connection failed
- Solution: Ensure PostgreSQL is running: `docker-compose ps db`

**Issue**: Port already in use
- Solution: Change port in `.env` or stop conflicting service

#### Application Issues

**Issue**: Login fails but user exists
- Solution: Reset password via admin panel or CLI

**Issue**: AI Assistant not responding
- Solution: Check OpenAI API key in `.env` and ensure credits are available

**Issue**: Email not sending
- Solution: Verify SMTP settings in `.env` and test with Mailhog UI

**Issue**: Celery tasks not running
- Solution: Ensure Celery worker is running: `docker-compose up celery-worker`

### Useful Commands

```bash
# View application logs
docker-compose logs -f web

# Restart specific service
docker-compose restart redis

# Access database
docker-compose exec db psql -U taskflow -d taskflow

# Run database migration
docker-compose exec web flask db upgrade

# View Celery logs
docker-compose logs -f celery-worker
```

## 🔒 Security Features

| Service | Port | Description |
|---------|------|-------------|
| web | 5000 | Main application |
| db | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |
| celery-worker | - | Background task worker |
| celery-beat | - | Scheduled task scheduler |
| mailhog | 8025 | Email testing UI |
| nginx | 80/443 | Reverse proxy (production) |

## 🔒 Security Features

- Password hashing with bcrypt
- Session management with Flask-Login
- CSRF protection on all forms
- SQL injection prevention via SQLAlchemy ORM
- XSS protection via Jinja2 auto-escaping
- Role-based access control (RBAC)
- API key authentication for REST API
- Secure email configuration

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Ways to Contribute
- **Bug Reports**: Open an issue with detailed reproduction steps
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Fix bugs or implement new features
- **Documentation**: Improve documentation or add examples
- **Translations**: Help localize the application

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run linter (`flake8 app/`)
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style
- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use type hints where possible
- Write clear commit messages
- Add tests for new functionality
- Update documentation as needed

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 👥 Author

**A-Tech Corporation PTY LTD**

- Website: https://theatechcorporation.com
- GitHub: [@hamishfromatech](https://github.com/hamishfromatech)
- Support: hamish@atech.industries

## 🙏 Acknowledgments

- Built with [Flask](https://palletsprojects.com/p/flask/)
- AI features powered by [OpenAI](https://openai.com/)
- Integrations powered by [Composio](https://composio.dev/)
- Database migrations with [Alembic](https://alembic.sqlalchemy.org/)

## 📞 Support

For support, please:
1. Check the [documentation](https://docs.taskflow.local)
2. Search existing [issues](https://github.com/hamishfromatech/taskflow-psa/issues)
3. Open a new issue with detailed information
4. Contact: hamish@atech.industries


---

*TaskFlow PSA is a professional services automation platform designed to help agencies and professional services organizations manage their projects, tickets, clients, and billing in one unified system.*
