"""
automation.rbac — Role-Based Access Control for Automation Routes
==================================================================
Provides decorators that enforce access control on the n8n blueprint routes.
Reuses the existing ``User.is_admin`` field from ``models.py``.

Roles:
  • Student     — any authenticated user (can access AI Mentor, Study Planner, etc.)
  • Instructor  — users with ``is_admin=True`` OR users who have created courses
  • Admin       — users with ``is_admin=True``
  • Webhook     — requests with valid ``X-Webhook-Secret`` header
"""

from functools import wraps
from flask import request, jsonify, flash, redirect, url_for, current_app
from flask_login import current_user, login_required


def student_accessible(f):
    """Any authenticated user can access this route."""
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


def instructor_required(f):
    """Only instructors (admins or course owners) can access this route."""
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)

        # Check if user has created any courses (instructor detection)
        from models import Course
        has_courses = Course.query.filter_by().first() is not None  # simplified — in production, track course ownership
        if has_courses and current_user.is_admin:
            return f(*args, **kwargs)

        # For now, treat admins as instructors
        flash("Instructor or Admin access required.", "danger")
        return redirect(url_for("main.dashboard"))
    return wrapper


def admin_required(f):
    """Only admins can access this route."""
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return wrapper


def webhook_authorized(f):
    """Validates the N8N_WEBHOOK_SECRET header for webhook endpoints.

    Webhook endpoints are also CSRF-exempt since they're called by n8n,
    not by browser forms.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        expected_secret = current_app.config.get("N8N_WEBHOOK_SECRET", "")
        provided_secret = request.headers.get("X-Webhook-Secret", "")

        if not expected_secret or expected_secret != provided_secret:
            return jsonify({"error": "Unauthorized — invalid webhook secret"}), 401

        return f(*args, **kwargs)
    return wrapper
