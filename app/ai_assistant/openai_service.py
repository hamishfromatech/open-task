"""OpenAI service for AI-powered features."""

import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from flask import current_app


class AIAssistant:
    """Service class for OpenAI operations."""

    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4-turbo-preview')

    def _get_system_prompt(self, prompt_type: str) -> str:
        """Get system prompt for different AI tasks."""
        prompts = {
            'assistant': """You are an intelligent assistant for TaskFlow PSA, a professional services automation platform.
            Help users with:
            - Service desk ticket management
            - Project management
            - CRM and sales operations
            - Billing and invoicing
            - Workflow automation

            Be concise, professional, and helpful. Provide actionable insights.""",

            'ticket_response': """You are a technical support specialist. Generate professional, helpful responses to customer tickets.
            Be empathetic, clear, and solution-focused. Include troubleshooting steps when appropriate.""",

            'ticket_categorization': """Analyze the ticket and return JSON with:
            - category: one of [hardware, software, network, security, email, other]
            - priority: one of [critical, high, medium, low]
            - suggested_assignee_type: type of specialist needed
            - related_keywords: list of relevant keywords""",

            'lead_scoring': """Analyze the lead and return a score (0-100) based on:
            - Company fit
            - Engagement level
            - Budget indicators
            - Timeline
            Return JSON with score, confidence, and reasoning.""",

            'opportunity_analysis': """Analyze the opportunity and provide insights on:
            - Win probability
            - Key risks
            - Recommended next steps
            - Competitive positioning""",

            'workflow_suggestion': """Analyze patterns and suggest workflow automations.
            Return JSON array of workflow suggestions with trigger, conditions, and actions.""",

            'content_generation': """Generate professional business content based on the specified type.
            Be clear, concise, and appropriate for business communication.""",

            'search': """Parse the natural language search query and identify:
            - Entity types to search (tickets, clients, projects, etc.)
            - Filter conditions
            - Sort preferences
            Return structured search parameters."""
        }
        return prompts.get(prompt_type, prompts['assistant'])

    def chat(self, user_id: int, organization_id: int, message: str, context: Dict = None) -> str:
        """Chat with AI assistant."""
        messages = [
            {"role": "system", "content": self._get_system_prompt('assistant')}
        ]

        # Add context if provided
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({
                "role": "system",
                "content": f"Context:\n{context_str}"
            })

        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content

    def suggest_ticket_response(self, ticket) -> str:
        """Generate a suggested response for a ticket."""
        ticket_context = f"""
        Ticket Subject: {ticket.subject}
        Description: {ticket.description}
        Priority: {ticket.priority}
        Category: {ticket.category}
        Client: {ticket.client.name if ticket.client else 'N/A'}
        Previous Comments:
        """

        for comment in ticket.comments.limit(5):
            ticket_context += f"\n- {comment.content[:200]}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt('ticket_response')},
                {"role": "user", "content": f"Generate a response to this ticket:\n{ticket_context}"}
            ],
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content

    def categorize_ticket(self, ticket) -> Dict:
        """Categorize and analyze a ticket."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt('ticket_categorization')},
                {"role": "user", "content": f"Categorize this ticket:\nSubject: {ticket.subject}\nDescription: {ticket.description}"}
            ],
            max_tokens=200,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def recommend_assignee(self, ticket) -> Dict:
        """Recommend best assignee for a ticket."""
        from app.models.user import User
        from app import db

        # Get team members
        users = User.query.filter_by(organization_id=ticket.organization_id, is_active=True).all()

        # Get workload for each user
        workloads = {}
        for user in users:
            open_tickets = Ticket.query.filter_by(
                assigned_to=user.id,
                status__in=['open', 'in_progress', 'pending']
            ).count()
            workloads[user.id] = {
                'name': user.full_name,
                'open_tickets': open_tickets
            }

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": """Analyze the ticket and recommend the best assignee based on:
                - Skills match (category, type)
                - Current workload
                - SLA requirements

                Return JSON with:
                - recommendations: list of {user_id, name, score, reasoning}
                - estimated_resolution_time: hours"""},
                {"role": "user", "content": f"""
                Ticket: {ticket.subject}
                Category: {ticket.category}
                Priority: {ticket.priority}
                Type: {ticket.ticket_type}

                Available team members:
                {json.dumps(workloads, indent=2)}
                """}
            ],
            max_tokens=500,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def generate_dashboard_summary(self, organization_id: int) -> Dict:
        """Generate AI summary of dashboard data."""
        from app.models.ticket import Ticket
        from app.models.project import Project
        from app.models.crm import Opportunity
        from app import db
        from sqlalchemy import func
        from datetime import datetime, timedelta

        # Get statistics
        total_tickets = Ticket.query.filter_by(organization_id=organization_id).count()
        open_tickets = Ticket.query.filter_by(organization_id=organization_id, status='open').count()
        in_progress = Ticket.query.filter_by(organization_id=organization_id, status='in_progress').count()
        resolved_this_week = Ticket.query.filter(
            Ticket.organization_id == organization_id,
            Ticket.status == 'resolved',
            Ticket.resolved_at >= datetime.utcnow() - timedelta(days=7)
        ).count()

        pipeline_value = db.session.query(func.sum(Opportunity.amount)).filter(
            Opportunity.organization_id == organization_id,
            Opportunity.stage.notin_(['closed_won', 'closed_lost'])
        ).scalar() or 0

        active_projects = Project.query.filter_by(organization_id=organization_id, status='active').count()

        summary_text = f"""
        Dashboard Summary:
        - Total Tickets: {total_tickets}
        - Open Tickets: {open_tickets}
        - In Progress: {in_progress}
        - Resolved This Week: {resolved_this_week}
        - Pipeline Value: ${pipeline_value:,.0f}
        - Active Projects: {active_projects}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Provide a brief executive summary with key insights and recommendations."},
                {"role": "user", "content": summary_text}
            ],
            max_tokens=300,
            temperature=0.5
        )

        return {
            'summary': response.choices[0].message.content,
            'stats': {
                'total_tickets': total_tickets,
                'open_tickets': open_tickets,
                'resolved_this_week': resolved_this_week,
                'pipeline_value': pipeline_value,
                'active_projects': active_projects
            }
        }

    def generate_insights(self, organization_id: int, start_date: str, end_date: str) -> Dict:
        """Generate AI insights from business data."""
        # This would gather various metrics and analyze them
        # For now, return a structured response

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Analyze business metrics and provide insights with recommendations."},
                {"role": "user", "content": f"Generate insights for organization {organization_id} from {start_date} to {end_date}"}
            ],
            max_tokens=500,
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def score_lead(self, lead) -> Dict:
        """Score a lead using AI."""
        lead_context = f"""
        Lead Information:
        - Name: {lead.full_name}
        - Company: {lead.company}
        - Job Title: {lead.job_title}
        - Source: {lead.source}
        - Estimated Value: ${lead.estimated_value or 0:,.0f}
        - Status: {lead.status}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt('lead_scoring')},
                {"role": "user", "content": f"Score this lead:\n{lead_context}"}
            ],
            max_tokens=300,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def analyze_opportunity(self, opportunity) -> Dict:
        """Analyze an opportunity for win probability."""
        opp_context = f"""
        Opportunity: {opportunity.name}
        Amount: ${opportunity.amount:,.0f}
        Stage: {opportunity.stage}
        Probability: {opportunity.probability}%
        Expected Close: {opportunity.expected_close_date}
        Type: {opportunity.opportunity_type}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt('opportunity_analysis')},
                {"role": "user", "content": f"Analyze this opportunity:\n{opp_context}"}
            ],
            max_tokens=400,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def suggest_workflows(self, organization_id: int, entity_type: str) -> List[Dict]:
        """Suggest workflow automations based on patterns."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt('workflow_suggestion')},
                {"role": "user", "content": f"Suggest workflows for {entity_type} management in a PSA platform"}
            ],
            max_tokens=500,
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result.get('suggestions', [])

    def generate_content(self, content_type: str, context: Dict) -> str:
        """Generate content (emails, responses, etc.)."""
        content_prompts = {
            'email': "Generate a professional email.",
            'ticket_response': "Generate a helpful ticket response.",
            'proposal': "Generate a business proposal section.",
            'follow_up': "Generate a follow-up message."
        }

        system_prompt = content_prompts.get(content_type, "Generate professional content.")

        context_str = json.dumps(context, indent=2)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"{system_prompt}\n{self._get_system_prompt('content_generation')}"},
                {"role": "user", "content": f"Context:\n{context_str}"}
            ],
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content

    def natural_language_search(self, organization_id: int, query: str) -> Dict:
        """Parse natural language search query."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt('search')},
                {"role": "user", "content": f"Parse this search query: {query}"}
            ],
            max_tokens=300,
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)