"""Stripe service for payment processing."""

import os
import stripe
from datetime import datetime
from flask import current_app
from app import db
from app.models.billing import Invoice, Payment
from app.models.organization import Organization


class StripeService:
    """Service class for Stripe operations."""

    def __init__(self):
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

    def create_customer(self, organization):
        """Create a Stripe customer for an organization."""
        customer = stripe.Customer.create(
            email=organization.email,
            name=organization.name,
            metadata={
                'organization_id': organization.id
            }
        )
        organization.stripe_customer_id = customer.id
        db.session.commit()
        return customer

    def create_subscription(self, organization, plan_id):
        """Create a subscription for an organization."""
        if not organization.stripe_customer_id:
            self.create_customer(organization)

        subscription = stripe.Subscription.create(
            customer=organization.stripe_customer_id,
            items=[{'price': plan_id}],
            metadata={
                'organization_id': organization.id
            }
        )

        organization.stripe_subscription_id = subscription.id
        organization.subscription_status = subscription.status

        db.session.commit()
        return subscription

    def create_invoice(self, invoice):
        """Create a Stripe invoice from our invoice model."""
        from app.models.client import Client

        client = Client.query.get(invoice.client_id)

        # Get or create Stripe customer
        if not client:
            raise ValueError("Client not found")

        # Create invoice items
        for item in invoice.items:
            stripe.InvoiceItem.create(
                customer=client.id,  # Would need Stripe customer ID
                amount=int(item.total * 100),  # Stripe uses cents
                currency='usd',
                description=item.description
            )

        # Create invoice
        stripe_invoice = stripe.Invoice.create(
            customer=client.id,  # Would need Stripe customer ID
            auto_advance=True,
            metadata={
                'invoice_id': invoice.id
            }
        )

        return stripe_invoice

    def handle_invoice_paid(self, stripe_invoice):
        """Handle invoice paid webhook."""
        invoice_id = stripe_invoice.get('metadata', {}).get('invoice_id')
        if not invoice_id:
            return

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return

        invoice.status = 'paid'
        invoice.paid_date = datetime.utcnow()
        invoice.amount_paid = stripe_invoice.amount_paid / 100  # Convert from cents
        invoice.stripe_payment_intent_id = stripe_invoice.payment_intent

        db.session.commit()

    def handle_payment_failed(self, stripe_invoice):
        """Handle payment failed webhook."""
        invoice_id = stripe_invoice.get('metadata', {}).get('invoice_id')
        if not invoice_id:
            return

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return

        invoice.status = 'overdue'
        db.session.commit()

    def handle_subscription_updated(self, stripe_subscription):
        """Handle subscription updated webhook."""
        org_id = stripe_subscription.get('metadata', {}).get('organization_id')
        if not org_id:
            return

        organization = Organization.query.get(org_id)
        if not organization:
            return

        organization.subscription_status = stripe_subscription.status

        if stripe_subscription.status == 'active':
            organization.subscription_ends_at = datetime.fromtimestamp(
                stripe_subscription.current_period_end
            )

        db.session.commit()

    def cancel_subscription(self, organization):
        """Cancel a subscription."""
        if not organization.stripe_subscription_id:
            return

        subscription = stripe.Subscription.delete(
            organization.stripe_subscription_id
        )

        organization.subscription_status = 'cancelled'
        db.session.commit()

        return subscription

    def get_subscription_plans(self):
        """Get available subscription plans from Stripe."""
        plans = []

        starter_price = os.environ.get('STRIPE_STARTER_PRICE_ID')
        professional_price = os.environ.get('STRIPE_PROFESSIONAL_PRICE_ID')
        enterprise_price = os.environ.get('STRIPE_ENTERPRISE_PRICE_ID')

        if starter_price:
            plans.append({
                'id': starter_price,
                'name': 'Starter',
                'price': 29,
                'features': ['5 users', 'Basic ticketing', 'Email support']
            })

        if professional_price:
            plans.append({
                'id': professional_price,
                'name': 'Professional',
                'price': 79,
                'features': ['25 users', 'Advanced ticketing', 'CRM', 'Phone support']
            })

        if enterprise_price:
            plans.append({
                'id': enterprise_price,
                'name': 'Enterprise',
                'price': 199,
                'features': ['Unlimited users', 'All features', 'AI Assistant', 'Priority support']
            })

        return plans