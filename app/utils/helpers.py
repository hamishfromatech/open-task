"""Utility functions and helpers."""

from datetime import datetime
import re
import uuid


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


def format_datetime(dt, fmt='%Y-%m-%d %H:%M'):
    """Format datetime object."""
    if dt is None:
        return ''
    return dt.strftime(fmt)


def format_date(dt, fmt='%Y-%m-%d'):
    """Format date object."""
    if dt is None:
        return ''
    return dt.strftime(fmt)


def format_currency(amount, currency='USD'):
    """Format currency amount."""
    if amount is None:
        return '$0.00'
    return f'${amount:,.2f}'


def time_ago(dt):
    """Return human-readable time ago string."""
    if dt is None:
        return 'never'

    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f'{years} year{"s" if years > 1 else ""} ago'
    elif diff.days > 30:
        months = diff.days // 30
        return f'{months} month{"s" if months > 1 else ""} ago'
    elif diff.days > 0:
        return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    else:
        return 'just now'


def truncate(text, length=100):
    """Truncate text to specified length."""
    if len(text) <= length:
        return text
    return text[:length] + '...'


def calculate_percentage(value, total):
    """Calculate percentage."""
    if total == 0:
        return 0
    return min(100, (value / total) * 100)