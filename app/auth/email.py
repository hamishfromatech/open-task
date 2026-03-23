"""Authentication email utilities."""

from flask import current_app, url_for
from flask_mail import Message
from app import mail
import jwt
from datetime import datetime, timedelta


def send_password_reset_email(user):
    """Send password reset email to user."""
    token = generate_reset_token(user)
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    subject = 'Reset Your Password - TaskFlow PSA'
    body = f'''Hello {user.first_name},

You requested to reset your password. Click the link below to reset it:

{reset_url}

This link will expire in 1 hour.

If you did not request this, please ignore this email.

Best regards,
TaskFlow PSA Team
'''

    send_email(user.email, subject, body)


def send_verification_email(user):
    """Send email verification to user."""
    token = generate_email_token(user)
    verify_url = url_for('auth.verify_email', token=token, _external=True)

    subject = 'Verify Your Email - TaskFlow PSA'
    body = f'''Hello {user.first_name},

Welcome to TaskFlow PSA! Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

Best regards,
TaskFlow PSA Team
'''

    send_email(user.email, subject, body)


def send_email(to, subject, body):
    """Send email using Flask-Mail."""
    try:
        msg = Message(
            subject,
            recipients=[to],
            body=body,
            sender=current_app.config.get('MAIL_USERNAME')
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send email: {e}')
        return False


def generate_reset_token(user, expires_in=3600):
    """Generate password reset token."""
    return jwt.encode(
        {'reset_user': user.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )


def verify_reset_token(token):
    """Verify password reset token."""
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        from app.models.user import User
        return User.query.get(data['reset_user'])
    except:
        return None


def generate_email_token(user, expires_in=86400):
    """Generate email verification token."""
    return jwt.encode(
        {'verify_user': user.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )


def verify_email_token(token):
    """Verify email verification token."""
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        from app.models.user import User
        return User.query.get(data['verify_user'])
    except:
        return None