"""Billing routes - Invoices and Payments."""

from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.billing import Invoice, InvoiceItem, Payment, Subscription
from app.models.client import Client, Contact
from app.models.project import TimeEntry
from app.billing.forms import InvoiceForm, InvoiceItemForm, PaymentForm
from app.billing.stripe_service import StripeService

billing_bp = Blueprint('billing', __name__)


@billing_bp.route('/')
@login_required
def index():
    """Billing dashboard."""
    org_id = current_user.organization_id

    # Summary stats
    stats = {
        'total_invoiced': db.session.query(db.func.sum(Invoice.total)).filter(
            Invoice.organization_id == org_id
        ).scalar() or 0,
        'total_collected': db.session.query(db.func.sum(Invoice.amount_paid)).filter(
            Invoice.organization_id == org_id
        ).scalar() or 0,
        'outstanding': db.session.query(db.func.sum(Invoice.amount_due)).filter(
            Invoice.organization_id == org_id,
            Invoice.status.in_(['sent', 'viewed', 'overdue'])
        ).scalar() or 0,
        'overdue_count': Invoice.query.filter(
            Invoice.organization_id == org_id,
            Invoice.status == 'overdue'
        ).count(),
    }
    stats['collection_rate'] = (stats['total_collected'] / stats['total_invoiced'] * 100) if stats['total_invoiced'] > 0 else 0

    # Recent invoices
    recent_invoices = Invoice.query.filter_by(organization_id=org_id)\
        .order_by(Invoice.created_at.desc()).limit(5).all()

    # Overdue invoices
    overdue_invoices = Invoice.query.filter(
        Invoice.organization_id == org_id,
        Invoice.status == 'overdue'
    ).order_by(Invoice.due_date).limit(5).all()

    return render_template('billing/index.html',
                           stats=stats,
                           recent_invoices=recent_invoices,
                           overdue_invoices=overdue_invoices)


# ==================== INVOICES ====================

@billing_bp.route('/invoices')
@login_required
def invoices():
    """List invoices."""
    org_id = current_user.organization_id

    status = request.args.get('status')
    client_id = request.args.get('client_id', type=int)
    search = request.args.get('search')

    query = Invoice.query.filter_by(organization_id=org_id)

    if status:
        query = query.filter_by(status=status)

    if client_id:
        query = query.filter_by(client_id=client_id)

    if search:
        search_term = f'%{search}%'
        query = query.filter(Invoice.invoice_number.ilike(search_term))

    invoices = query.order_by(Invoice.created_at.desc()).all()
    clients = Client.query.filter_by(organization_id=org_id).all()

    return render_template('billing/invoices/index.html',
                           invoices=invoices,
                           clients=clients)


@billing_bp.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def create_invoice():
    """Create a new invoice."""
    org_id = current_user.organization_id
    form = InvoiceForm()

    # Populate client choices
    clients = Client.query.filter_by(organization_id=org_id).all()
    form.client_id.choices = [(0, '-- Select Client --)] + [
        (c.id, c.name) for c in clients
    ]

    if form.validate_on_submit():
        invoice_number = Invoice.generate_invoice_number(org_id)

        invoice = Invoice(
            organization_id=org_id,
            client_id=form.client_id.data,
            invoice_number=invoice_number,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            notes=form.notes.data,
            terms=form.terms.data,
            created_by=current_user.id
        )

        db.session.add(invoice)
        db.session.flush()

        # Add line items
        for item_data in request.form.getlist('items'):
            # Parse item data (would normally be from a separate form)
            pass

        invoice.calculate_totals()
        db.session.commit()

        flash(f'Invoice {invoice.invoice_number} created successfully.', 'success')
        return redirect(url_for('billing.view_invoice', invoice_id=invoice.id))

    # Get unbilled time entries
    unbilled_time = TimeEntry.query.filter_by(
        organization_id=org_id,
        is_invoiced=False,
        billable=True
    ).all()

    return render_template('billing/invoices/create.html', form=form, unbilled_time=unbilled_time)


@billing_bp.route('/invoices/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    """View an invoice."""
    org_id = current_user.organization_id
    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=org_id).first_or_404()

    items = invoice.items.order_by(InvoiceItem.id).all()
    payments = invoice.payments.order_by(Payment.payment_date).all()

    return render_template('billing/invoices/view.html',
                           invoice=invoice,
                           items=items,
                           payments=payments)


@billing_bp.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(invoice_id):
    """Edit an invoice."""
    org_id = current_user.organization_id
    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=org_id).first_or_404()

    if invoice.status == 'paid':
        flash('Cannot edit a paid invoice.', 'error')
        return redirect(url_for('billing.view_invoice', invoice_id=invoice.id))

    form = InvoiceForm(obj=invoice)
    clients = Client.query.filter_by(organization_id=org_id).all()
    form.client_id.choices = [(0, '-- Select Client --)] + [
        (c.id, c.name) for c in clients
    ]

    if form.validate_on_submit():
        invoice.client_id = form.client_id.data
        invoice.issue_date = form.issue_date.data
        invoice.due_date = form.due_date.data
        invoice.notes = form.notes.data
        invoice.terms = form.terms.data

        invoice.calculate_totals()
        db.session.commit()

        flash('Invoice updated successfully.', 'success')
        return redirect(url_for('billing.view_invoice', invoice_id=invoice.id))

    return render_template('billing/invoices/edit.html', invoice=invoice, form=form)


@billing_bp.route('/invoices/<int:invoice_id>/send', methods=['POST'])
@login_required
def send_invoice(invoice_id):
    """Send invoice to client via email."""
    org_id = current_user.organization_id
    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=org_id).first_or_404()

    if invoice.status == 'draft':
        invoice.status = 'sent'
        invoice.sent_at = datetime.utcnow()
        db.session.commit()

        # TODO: Send email notification
        # send_invoice_email(invoice)

        flash('Invoice sent successfully.', 'success')
    else:
        flash('Invoice has already been sent.', 'warning')

    return redirect(url_for('billing.view_invoice', invoice_id=invoice.id))


@billing_bp.route('/invoices/<int:invoice_id>/payment', methods=['GET', 'POST'])
@login_required
def record_payment(invoice_id):
    """Record a payment for an invoice."""
    org_id = current_user.organization_id
    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=org_id).first_or_404()

    form = PaymentForm()
    form.invoice_id.data = invoice.id

    if form.validate_on_submit():
        payment = Payment(
            organization_id=org_id,
            invoice_id=invoice.id,
            client_id=invoice.client_id,
            amount=form.amount.data,
            payment_date=form.payment_date.data,
            payment_method=form.payment_method.data,
            reference_number=form.reference_number.data,
            notes=form.notes.data,
            created_by=current_user.id
        )

        # Update invoice
        invoice.amount_paid += payment.amount
        invoice.amount_due = invoice.total - invoice.amount_paid

        if invoice.amount_due <= 0:
            invoice.status = 'paid'
            invoice.paid_date = payment.payment_date

        db.session.add(payment)
        db.session.commit()

        flash('Payment recorded successfully.', 'success')
        return redirect(url_for('billing.view_invoice', invoice_id=invoice.id))

    return render_template('billing/payments/create.html', invoice=invoice, form=form)


@billing_bp.route('/invoices/<int:invoice_id>/stripe', methods=['POST'])
@login_required
def create_stripe_invoice(invoice_id):
    """Create a Stripe invoice for online payment."""
    org_id = current_user.organization_id
    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=org_id).first_or_404()

    try:
        stripe_service = StripeService()
        stripe_invoice = stripe_service.create_invoice(invoice)

        invoice.stripe_invoice_id = stripe_invoice.id
        db.session.commit()

        flash('Stripe invoice created. Customer will receive payment link.', 'success')
        return redirect(url_for('billing.view_invoice', invoice_id=invoice.id))

    except Exception as e:
        flash(f'Error creating Stripe invoice: {str(e)}', 'error')
        return redirect(url_for('billing.view_invoice', invoice_id=invoice.id))


# ==================== PAYMENTS ====================

@billing_bp.route('/payments')
@login_required
def payments():
    """List all payments."""
    org_id = current_user.organization_id

    payments = Payment.query.filter_by(organization_id=org_id)\
        .order_by(Payment.payment_date.desc()).all()

    return render_template('billing/payments/index.html', payments=payments)


# ==================== STRIPE WEBHOOKS ====================

@billing_bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events."""
    import stripe
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    if event['type'] == 'invoice.paid':
        stripe_service = StripeService()
        stripe_service.handle_invoice_paid(event['data']['object'])

    elif event['type'] == 'invoice.payment_failed':
        stripe_service = StripeService()
        stripe_service.handle_payment_failed(event['data']['object'])

    elif event['type'] == 'customer.subscription.updated':
        stripe_service = StripeService()
        stripe_service.handle_subscription_updated(event['data']['object'])

    return jsonify({'status': 'success'}), 200


# ==================== SUBSCRIPTIONS ====================

@billing_bp.route('/subscriptions')
@login_required
def subscriptions():
    """List subscriptions."""
    org_id = current_user.organization_id

    subscriptions = Subscription.query.filter_by(organization_id=org_id).all()

    return render_template('billing/subscriptions/index.html', subscriptions=subscriptions)