"""Authentication routes."""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models.user import User, Role
from app.auth.forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from app.auth.email import send_password_reset_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return redirect(url_for('auth.login'))

            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect(next_page or url_for('main.dashboard'))

        flash('Invalid email or password.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('An account with this email already exists.', 'error')
            return redirect(url_for('auth.register'))

        # Create organization (for now, single-user org)
        from app.models.organization import Organization, OrganizationSettings

        org = Organization(
            name=form.company_name.data or f"{form.first_name.data}'s Organization",
            slug=form.email.data.split('@')[0].lower()
        )
        db.session.add(org)
        db.session.flush()

        # Create user
        user = User(
            organization_id=org.id,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_admin=True,
            email_verified=False
        )
        user.set_password(form.password.data)

        # Assign default role
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            user.role_id = admin_role.id

        db.session.add(user)
        db.session.flush()

        # Create organization settings
        settings = OrganizationSettings(organization_id=org.id)
        db.session.add(settings)

        db.session.commit()

        login_user(user)
        flash('Welcome to TaskFlow PSA! Your account has been created.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('If an account with that email exists, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    user = User.verify_reset_token(token)
    if not user:
        flash('The reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address."""
    user = User.verify_email_token(token)
    if user:
        user.email_verified = True
        db.session.commit()
        flash('Your email has been verified. Thank you!', 'success')
    else:
        flash('The verification link is invalid or has expired.', 'error')

    return redirect(url_for('main.dashboard'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile settings."""
    from app.auth.forms import ProfileForm

    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.job_title = form.job_title.data
        current_user.timezone = form.timezone.data
        current_user.email_notifications = form.email_notifications.data
        current_user.dark_mode = form.dark_mode.data

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    from app.auth.forms import ChangePasswordForm

    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been changed.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', form=form)