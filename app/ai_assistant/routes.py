"""AI Assistant routes - OpenAI powered features."""

from flask import Blueprint, render_template, request, jsonify, stream_template, current_app
from flask_login import login_required, current_user
from app import db
from app.ai_assistant.openai_service import AIAssistant
from app.models.ticket import Ticket
from app.models.project import Project, Task
from app.models.crm import Lead, Opportunity
from app.models.client import Client
import json

ai_bp = Blueprint('ai_assistant', __name__)


@ai_bp.route('/')
@login_required
def index():
    """AI Assistant dashboard."""
    return render_template('ai/index.html')


@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Chat with AI assistant."""
    data = request.get_json()
    message = data.get('message')
    context = data.get('context', {})

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    try:
        assistant = AIAssistant()
        response = assistant.chat(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            message=message,
            context=context
        )
        return jsonify({'response': response})
    except Exception as e:
        current_app.logger.error(f"AI chat error: {e}")
        return jsonify({'error': 'Failed to process message'}), 500


@ai_bp.route('/tickets/<int:ticket_id>/suggest', methods=['POST'])
@login_required
def suggest_ticket_response(ticket_id):
    """Generate AI-suggested response for a ticket."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    try:
        assistant = AIAssistant()
        suggestion = assistant.suggest_ticket_response(ticket)
        return jsonify({'suggestion': suggestion})
    except Exception as e:
        current_app.logger.error(f"AI suggestion error: {e}")
        return jsonify({'error': 'Failed to generate suggestion'}), 500


@ai_bp.route('/tickets/<int:ticket_id>/categorize', methods=['POST'])
@login_required
def categorize_ticket(ticket_id):
    """AI-powered ticket categorization."""
    org_id = current_user.organization_id
    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    try:
        assistant = AIAssistant()
        categorization = assistant.categorize_ticket(ticket)
        return jsonify(categorization)
    except Exception as e:
        current_app.logger.error(f"AI categorization error: {e}")
        return jsonify({'error': 'Failed to categorize ticket'}), 500


@ai_bp.route('/tickets/smart-assign', methods=['POST'])
@login_required
def smart_assign():
    """AI-powered ticket assignment recommendations."""
    org_id = current_user.organization_id
    data = request.get_json()
    ticket_id = data.get('ticket_id')

    ticket = Ticket.query.filter_by(id=ticket_id, organization_id=org_id).first_or_404()

    try:
        assistant = AIAssistant()
        recommendations = assistant.recommend_assignee(ticket)
        return jsonify(recommendations)
    except Exception as e:
        current_app.logger.error(f"AI assignment error: {e}")
        return jsonify({'error': 'Failed to get recommendations'}), 500


@ai_bp.route('/summaries/dashboard', methods=['GET'])
@login_required
def dashboard_summary():
    """Generate AI summary of dashboard data."""
    org_id = current_user.organization_id

    try:
        assistant = AIAssistant()
        summary = assistant.generate_dashboard_summary(org_id)
        return jsonify(summary)
    except Exception as e:
        current_app.logger.error(f"AI summary error: {e}")
        return jsonify({'error': 'Failed to generate summary'}), 500


@ai_bp.route('/reports/insights', methods=['GET'])
@login_required
def insights():
    """Generate AI insights from business data."""
    org_id = current_user.organization_id

    # Get date range
    from datetime import datetime, timedelta
    start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))

    try:
        assistant = AIAssistant()
        insights = assistant.generate_insights(org_id, start_date, end_date)
        return jsonify(insights)
    except Exception as e:
        current_app.logger.error(f"AI insights error: {e}")
        return jsonify({'error': 'Failed to generate insights'}), 500


@ai_bp.route('/lead-score/<int:lead_id>', methods=['GET'])
@login_required
def lead_score(lead_id):
    """AI-powered lead scoring."""
    org_id = current_user.organization_id
    lead = Lead.query.filter_by(id=lead_id, organization_id=org_id).first_or_404()

    try:
        assistant = AIAssistant()
        score = assistant.score_lead(lead)
        return jsonify(score)
    except Exception as e:
        current_app.logger.error(f"AI lead scoring error: {e}")
        return jsonify({'error': 'Failed to score lead'}), 500


@ai_bp.route('/opportunity/analyze', methods=['POST'])
@login_required
def analyze_opportunity():
    """Analyze opportunity win probability."""
    org_id = current_user.organization_id
    data = request.get_json()
    opportunity_id = data.get('opportunity_id')

    opportunity = Opportunity.query.filter_by(id=opportunity_id, organization_id=org_id).first_or_404()

    try:
        assistant = AIAssistant()
        analysis = assistant.analyze_opportunity(opportunity)
        return jsonify(analysis)
    except Exception as e:
        current_app.logger.error(f"AI opportunity analysis error: {e}")
        return jsonify({'error': 'Failed to analyze opportunity'}), 500


@ai_bp.route('/workflow/suggest', methods=['POST'])
@login_required
def suggest_workflow():
    """Suggest workflow automation based on patterns."""
    org_id = current_user.organization_id
    data = request.get_json()
    entity_type = data.get('entity_type', 'ticket')

    try:
        assistant = AIAssistant()
        suggestions = assistant.suggest_workflows(org_id, entity_type)
        return jsonify(suggestions)
    except Exception as e:
        current_app.logger.error(f"AI workflow suggestion error: {e}")
        return jsonify({'error': 'Failed to suggest workflows'}), 500


@ai_bp.route('/content/generate', methods=['POST'])
@login_required
def generate_content():
    """Generate content using AI (emails, responses, etc.)."""
    data = request.get_json()
    content_type = data.get('content_type')
    context = data.get('context', {})

    if not content_type:
        return jsonify({'error': 'Content type is required'}), 400

    try:
        assistant = AIAssistant()
        content = assistant.generate_content(content_type, context)
        return jsonify({'content': content})
    except Exception as e:
        current_app.logger.error(f"AI content generation error: {e}")
        return jsonify({'error': 'Failed to generate content'}), 500


@ai_bp.route('/search', methods=['POST'])
@login_required
def ai_search():
    """AI-powered natural language search."""
    org_id = current_user.organization_id
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        assistant = AIAssistant()
        results = assistant.natural_language_search(org_id, query)
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"AI search error: {e}")
        return jsonify({'error': 'Failed to search'}), 500


@ai_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """AI assistant settings."""
    from app.models.organization import OrganizationSettings

    org_id = current_user.organization_id
    settings_obj = OrganizationSettings.query.filter_by(organization_id=org_id).first()

    if request.method == 'POST':
        data = request.get_json()
        settings_obj.enable_ai_features = data.get('enable_ai_features', True)
        settings_obj.ai_model = data.get('ai_model', 'gpt-4-turbo-preview')
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({
        'enable_ai_features': settings_obj.enable_ai_features,
        'ai_model': settings_obj.ai_model
    })