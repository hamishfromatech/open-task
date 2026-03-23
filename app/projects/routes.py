"""Project routes."""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.project import Project, ProjectPhase, Task, TimeEntry
from app.models.client import Client
from app.models.user import User
from app.projects.forms import ProjectForm, TaskForm, TimeEntryForm

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/')
@login_required
def index():
    """List projects."""
    org_id = current_user.organization_id

    # Filters
    status = request.args.get('status')
    search = request.args.get('search')

    query = Project.query.filter_by(organization_id=org_id)

    if status:
        query = query.filter_by(status=status)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )

    # Sorting
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    sort_column = getattr(Project, sort, Project.created_at)
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    projects = query.paginate(page=page, per_page=per_page)

    return render_template('projects/index.html', projects=projects)


@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new project."""
    org_id = current_user.organization_id
    form = ProjectForm()

    # Populate client choices
    form.client_id.choices = [(0, '-- No Client --)] + [
        (c.id, c.name) for c in Client.query.filter_by(organization_id=org_id).order_by(Client.name).all()
    ]

    # Populate project manager choices
    users = User.query.filter_by(organization_id=org_id).all()
    form.project_manager_id.choices = [(0, '-- Select Manager --)] + [
        (u.id, u.full_name) for u in users
    ]

    if form.validate_on_submit():
        project_number = Project.generate_project_number(org_id)

        project = Project(
            organization_id=org_id,
            project_number=project_number,
            name=form.name.data,
            description=form.description.data,
            client_id=form.client_id.data if form.client_id.data else None,
            project_type=form.project_type.data,
            methodology=form.methodology.data,
            status=form.status.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            budget_type=form.budget_type.data,
            budget_hours=form.budget_hours.data,
            budget_amount=form.budget_amount.data,
            hourly_rate=form.hourly_rate.data,
            project_manager_id=form.project_manager_id.data if form.project_manager_id.data else None,
            created_by=current_user.id
        )

        db.session.add(project)
        db.session.commit()

        flash(f'Project {project.project_number} created successfully.', 'success')
        return redirect(url_for('projects.view', project_id=project.id))

    return render_template('projects/create.html', form=form)


@projects_bp.route('/<int:project_id>')
@login_required
def view(project_id):
    """View a project."""
    org_id = current_user.organization_id
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()

    # Get phases with tasks
    phases = project.phases.order_by(ProjectPhase.order).all()

    # Get all tasks
    tasks = project.tasks.order_by(Task.created_at).all()

    # Get time entries
    time_entries = project.time_entries.order_by(TimeEntry.created_at.desc()).limit(20).all()

    # Calculate stats
    total_hours = sum(entry.hours for entry in project.time_entries)
    task_stats = {
        'total': len(tasks),
        'completed': sum(1 for t in tasks if t.status == 'completed'),
        'in_progress': sum(1 for t in tasks if t.status == 'in_progress'),
        'not_started': sum(1 for t in tasks if t.status == 'not_started'),
    }

    return render_template('projects/view.html',
                           project=project,
                           phases=phases,
                           tasks=tasks,
                           time_entries=time_entries,
                           total_hours=total_hours,
                           task_stats=task_stats)


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    """Edit a project."""
    org_id = current_user.organization_id
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()

    form = ProjectForm(obj=project)
    form.client_id.choices = [(0, '-- No Client --)] + [
        (c.id, c.name) for c in Client.query.filter_by(organization_id=org_id).order_by(Client.name).all()
    ]
    users = User.query.filter_by(organization_id=org_id).all()
    form.project_manager_id.choices = [(0, '-- Select Manager --)] + [
        (u.id, u.full_name) for u in users
    ]

    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.client_id = form.client_id.data if form.client_id.data else None
        project.project_type = form.project_type.data
        project.methodology = form.methodology.data
        project.status = form.status.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.budget_type = form.budget_type.data
        project.budget_hours = form.budget_hours.data
        project.budget_amount = form.budget_amount.data
        project.hourly_rate = form.hourly_rate.data
        project.project_manager_id = form.project_manager_id.data if form.project_manager_id.data else None

        project.update_progress()
        db.session.commit()

        flash('Project updated successfully.', 'success')
        return redirect(url_for('projects.view', project_id=project.id))

    return render_template('projects/edit.html', project=project, form=form)


@projects_bp.route('/<int:project_id>/tasks', methods=['GET', 'POST'])
@login_required
def tasks(project_id):
    """Manage project tasks."""
    org_id = current_user.organization_id
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()

    if request.method == 'POST':
        # Create new task
        form = TaskForm()
        if form.validate_on_submit():
            task = Task(
                organization_id=org_id,
                project_id=project.id,
                title=form.title.data,
                description=form.description.data,
                assigned_to=form.assigned_to.data if form.assigned_to.data else None,
                priority=form.priority.data,
                status=form.status.data,
                estimated_hours=form.estimated_hours.data,
                due_date=form.due_date.data,
                created_by=current_user.id
            )
            db.session.add(task)
            project.update_progress()
            db.session.commit()
            flash('Task created successfully.', 'success')
            return redirect(url_for('projects.tasks', project_id=project.id))

    # Get tasks
    tasks = project.tasks.order_by(Task.created_at).all()

    # Get users for assignment
    users = User.query.filter_by(organization_id=org_id).all()

    form = TaskForm()
    form.assigned_to.choices = [(0, '-- Unassigned --)] + [
        (u.id, u.full_name) for u in users
    ]

    return render_template('projects/tasks.html', project=project, tasks=tasks, form=form)


@projects_bp.route('/<int:project_id>/time-entries', methods=['GET', 'POST'])
@login_required
def time_entries(project_id):
    """Manage time entries for a project."""
    org_id = current_user.organization_id
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()

    form = TimeEntryForm()

    if form.validate_on_submit():
        entry = TimeEntry(
            organization_id=org_id,
            user_id=current_user.id,
            project_id=project.id,
            hours=form.hours.data,
            description=form.description.data,
            billable=form.billable.data,
            hourly_rate=form.hourly_rate.data or project.hourly_rate
        )
        db.session.add(entry)
        db.session.commit()
        flash('Time entry added successfully.', 'success')
        return redirect(url_for('projects.time_entries', project_id=project.id))

    # Get time entries
    entries = project.time_entries.order_by(TimeEntry.created_at.desc()).all()

    return render_template('projects/time_entries.html', project=project, entries=entries, form=form)


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    """Delete a project."""
    org_id = current_user.organization_id
    project = Project.query.filter_by(id=project_id, organization_id=org_id).first_or_404()

    if not current_user.is_admin:
        flash('You do not have permission to delete projects.', 'error')
        return redirect(url_for('projects.view', project_id=project.id))

    project_number = project.project_number
    db.session.delete(project)
    db.session.commit()

    flash(f'Project {project_number} has been deleted.', 'success')
    return redirect(url_for('projects.index'))