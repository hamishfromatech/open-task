# TaskFlow PSA - Professional Services Automation Platform

## Features
- **Service Desk & Ticketing** - ITIL-aligned ticket management with SLA tracking
- **Workflow Automation** - Automated actions based on triggers and conditions
- **CRM & Sales** - Lead and opportunity management
- **Project Management** - Phases, tasks, and resource allocation
- **Time Tracking** - Automatic billable time capture
- **Billing & Invoicing** - Stripe-powered subscription billing
- **App Integrations** - 850+ integrations via Composio Dev
- **AI Assistant** - OpenAI-powered smart features

## Quick Start

### Using Docker (Recommended)
```bash
docker-compose up --build
```

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python init_db.py

# Run the application
python run.py
```

## Environment Variables
See `.env.example` for required configuration including:
- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - PostgreSQL connection string
- `STRIPE_SECRET_KEY` - Stripe API key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `OPENAI_API_KEY` - OpenAI API key
- `COMPOSIO_API_KEY` - Composio Dev API key

## Tech Stack
- **Backend**: Python 3.11, Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Payments**: Stripe
- **Integrations**: Composio Dev
- **AI**: OpenAI GPT-4
- **Frontend**: Jinja2 templates, TailwindCSS, Alpine.js
- **Deployment**: Docker, Docker Compose