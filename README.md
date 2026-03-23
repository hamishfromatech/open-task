# TaskFlow PSA

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-red.svg)](https://palletsprojects.com/p/flask/)

Professional Services Automation (PSA) Platform - A comprehensive, AI-powered alternative to Autotask, built with Flask and modern technologies.

![TaskFlow Dashboard](https://img.shields.io/badge/Dashboard-Interactive-success)
![Ticketing](https://img.shields.io/badge/Ticketing-ITIL--aligned-blue)
![CRM](https://img.shields.io/badge/CRM-Sales--pipeline-green)
![Billing](https://img.shields.io/badge/Billing-Stripe-powered-orange)

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
- **AI**: OpenAI GPT-4 Turbo
- **Payments**: Stripe
- **Integrations**: Composio Dev (850+ apps)

## 🚀 Quick Start

### Option 1: Docker (Recommended for Production)

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

## 🔌 API Documentation

The REST API is available at `/api/` prefix. All endpoints require authentication via Flask-Login or API key.

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

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run linter
flake8 app/
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

### Integrations
- **Integration** - Integration definitions
- **ConnectedAccount** - User-connected accounts
- **IntegrationEvent** - Webhook events

### Workflows
- **Workflow** - Workflow definitions
- **WorkflowExecution** - Workflow execution history

## 🐳 Docker Services

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

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 👥 Author

**A-Tech Corporation PTY LTD**

- Website: https://theatechcorporation.com
- GitHub: [@hamishfromatech](https://github.com/hamishfromatech)
- Support: hamish<!-- Import failed: atech.industries. - Only .md files are supported -->

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
4. Contact: hamish<!-- Import failed: atech.industries. - Only .md files are supported -->

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

*TaskFlow PSA is a professional services automation platform designed to help agencies and professional services organizations manage their projects, tickets, clients, and billing in one unified system.*
