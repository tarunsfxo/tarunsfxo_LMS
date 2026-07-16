"""
blueprints.n8n — Automation Blueprint
=======================================
All automation routes: webhook receivers, admin pages, student pages,
instructor pages, and API endpoints.

Registered at ``/n8n/`` prefix.
"""

import json
from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import current_user, login_required
from extensions import db, csrf

from automation.rbac import student_accessible, admin_required, instructor_required, webhook_authorized

n8n_bp = Blueprint("n8n", __name__, url_prefix="/n8n")


# ══════════════════════════════════════════════════════════════════
#  WEBHOOK RECEIVERS (called by n8n — CSRF exempt, secret-secured)
# ══════════════════════════════════════════════════════════════════

@n8n_bp.route("/webhook/welcome-email", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_welcome_email():
    """n8n confirms a welcome email was sent."""
    data = request.get_json(silent=True) or {}
    _log_webhook_event("welcome_email_sent", data)
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/course-enrolled", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_course_enrolled():
    """n8n confirms an enrollment email was sent."""
    data = request.get_json(silent=True) or {}
    _log_webhook_event("enrollment_confirmed", data)
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/certificate-ready", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_certificate_ready():
    """n8n confirms certificate email was delivered."""
    data = request.get_json(silent=True) or {}
    _log_webhook_event("certificate_delivered", data)
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/daily-reminder", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_daily_reminder():
    """n8n sends daily reminder data."""
    data = request.get_json(silent=True) or {}
    _log_webhook_event("daily_reminder_sent", data)
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/weekly-report", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_weekly_report():
    """n8n sends a generated weekly report to store."""
    data = request.get_json(silent=True) or {}
    try:
        from automation.models import WeeklyReport
        report = WeeklyReport(
            user_id=data.get("user_id"),
            week_start=datetime.fromisoformat(data.get("week_start", datetime.utcnow().isoformat())).date(),
            summary=data.get("summary", ""),
            pdf_url=data.get("pdf_url", ""),
            learning_hours=data.get("learning_hours", 0),
            quizzes_taken=data.get("quizzes_taken", 0),
            avg_quiz_score=data.get("avg_quiz_score", 0),
            bites_completed=data.get("bites_completed", 0),
            coding_solved=data.get("coding_solved", 0),
            xp_earned=data.get("xp_earned", 0),
        )
        db.session.add(report)
        db.session.commit()
    except Exception:
        pass
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/security-alert", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_security_alert():
    """n8n reports a security alert."""
    data = request.get_json(silent=True) or {}
    try:
        from automation.models import SecurityAlert
        alert = SecurityAlert(
            alert_type=data.get("alert_type", "unknown"),
            severity=data.get("severity", "medium"),
            detail=data.get("detail", ""),
            user_id=data.get("user_id"),
            ip_address=data.get("ip_address"),
        )
        db.session.add(alert)
        db.session.commit()
    except Exception:
        pass
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/achievement-awarded", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_achievement_awarded():
    """n8n awards an achievement."""
    data = request.get_json(silent=True) or {}
    _log_webhook_event("achievement_awarded", data)
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/feedback-analyzed", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_feedback_analyzed():
    """n8n sends feedback analysis results."""
    data = request.get_json(silent=True) or {}
    _log_webhook_event("feedback_analyzed", data)
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/career-recommendation", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_career_recommendation():
    """n8n sends career recommendation data."""
    data = request.get_json(silent=True) or {}
    _log_webhook_event("career_recommendation", data)
    return jsonify({"status": "received"})


@n8n_bp.route("/webhook/study-reminder-sent", methods=["POST"])
@csrf.exempt
@webhook_authorized
def webhook_study_reminder():
    """n8n confirms a study plan reminder was sent."""
    data = request.get_json(silent=True) or {}
    _log_webhook_event("study_reminder_sent", data)
    return jsonify({"status": "received"})


# ══════════════════════════════════════════════════════════════════
#  ADMIN PAGES
# ══════════════════════════════════════════════════════════════════

@n8n_bp.route("/dashboard")
@admin_required
def automation_dashboard():
    """Admin automation dashboard with analytics."""
    from automation.models import N8NWorkflowLog, N8NWorkflowConfig, AutomationEvent
    from sqlalchemy import func

    total_triggered = N8NWorkflowLog.query.count()
    successful = N8NWorkflowLog.query.filter_by(status="success").count()
    failed = N8NWorkflowLog.query.filter_by(status="failed").count()
    active_workflows = N8NWorkflowConfig.query.filter_by(is_enabled=True).count()

    success_rate = round(successful / total_triggered * 100) if total_triggered else 0
    avg_exec_time = db.session.query(func.avg(N8NWorkflowLog.execution_time_ms)).filter(
        N8NWorkflowLog.execution_time_ms.isnot(None)
    ).scalar() or 0

    recent_logs = N8NWorkflowLog.query.order_by(N8NWorkflowLog.created_at.desc()).limit(10).all()

    # Queue status
    from automation.queue import get_queue_status
    queue_status = get_queue_status()

    # Health
    from automation.health import get_health_status
    health = get_health_status()

    return render_template(
        "n8n/automation_dashboard.html",
        total_triggered=total_triggered,
        successful=successful,
        failed=failed,
        success_rate=success_rate,
        active_workflows=active_workflows,
        avg_exec_time=round(float(avg_exec_time)),
        recent_logs=recent_logs,
        queue_status=queue_status,
        health=health,
    )


@n8n_bp.route("/workflows")
@admin_required
def workflow_monitor():
    """Workflow monitor with enable/disable toggles."""
    from automation.models import N8NWorkflowConfig
    workflows = N8NWorkflowConfig.query.order_by(N8NWorkflowConfig.workflow_name.asc()).all()
    return render_template("n8n/workflow_monitor.html", workflows=workflows)


@n8n_bp.route("/logs")
@admin_required
def automation_logs():
    """Searchable, filterable automation logs."""
    from automation.models import N8NWorkflowLog

    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "")
    workflow_filter = request.args.get("workflow", "")

    query = N8NWorkflowLog.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if workflow_filter:
        query = query.filter_by(workflow_name=workflow_filter)

    pagination = query.order_by(N8NWorkflowLog.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template(
        "n8n/automation_logs.html",
        logs=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        workflow_filter=workflow_filter,
    )


@n8n_bp.route("/timeline")
@admin_required
def ai_timeline():
    """AI activity timeline (all users)."""
    from automation.models import AutomationEvent

    page = request.args.get("page", 1, type=int)
    events = AutomationEvent.query.order_by(
        AutomationEvent.created_at.desc()
    ).paginate(page=page, per_page=30, error_out=False)

    return render_template("n8n/ai_timeline.html", events=events.items, pagination=events)


@n8n_bp.route("/notifications")
@admin_required
def notification_center():
    """Admin notification center."""
    from automation.models import SecurityAlert
    from models import UserNotification

    alerts = SecurityAlert.query.filter_by(resolved=False).order_by(
        SecurityAlert.created_at.desc()
    ).limit(20).all()

    recent_notifs = UserNotification.query.order_by(
        UserNotification.created_at.desc()
    ).limit(30).all()

    return render_template("n8n/notification_center.html", alerts=alerts, notifications=recent_notifs)


@n8n_bp.route("/health-dashboard")
@admin_required
def health_dashboard():
    """System health dashboard."""
    from automation.health import get_health_status
    health = get_health_status()
    return render_template("n8n/health_dashboard.html", health=health)


@n8n_bp.route("/builder")
@admin_required
def automation_builder():
    """Automation Builder — IF/THEN rule creator."""
    from automation.builder import get_all_rules, AVAILABLE_TRIGGERS, AVAILABLE_ACTIONS, CONDITION_OPERATORS
    rules = get_all_rules()
    return render_template(
        "n8n/automation_builder.html",
        rules=rules,
        triggers=AVAILABLE_TRIGGERS,
        actions=AVAILABLE_ACTIONS,
        operators=CONDITION_OPERATORS,
    )


@n8n_bp.route("/api/docs")
@admin_required
def api_docs():
    """Swagger UI page."""
    return render_template("n8n/api_docs.html")


# ══════════════════════════════════════════════════════════════════
#  STUDENT PAGES
# ══════════════════════════════════════════════════════════════════

@n8n_bp.route("/ai-mentor")
@student_accessible
def ai_mentor():
    """AI Mentor chat interface."""
    from automation.services.ai_mentor import get_conversation_history
    history = get_conversation_history(current_user.id, limit=50)
    return render_template("n8n/ai_mentor.html", history=history)


@n8n_bp.route("/ai-mentor/ask", methods=["POST"])
@csrf.exempt
@student_accessible
def ai_mentor_ask():
    """Submit a question to the AI Mentor (instant response from Flask service)."""
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    if len(question) > 1000:
        return jsonify({"error": "Question too long (max 1000 characters)."}), 400

    from automation.services.ai_mentor import ask_question
    result = ask_question(current_user, question)

    return jsonify(result)


@n8n_bp.route("/my-activity")
@student_accessible
def student_activity():
    """Student automation history timeline."""
    from automation.models import AutomationEvent

    page = request.args.get("page", 1, type=int)
    events = AutomationEvent.query.filter_by(
        user_id=current_user.id
    ).order_by(
        AutomationEvent.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)

    return render_template("n8n/student_activity.html", events=events.items, pagination=events)


@n8n_bp.route("/my-reports")
@student_accessible
def my_reports():
    """Student's weekly progress reports."""
    from automation.models import WeeklyReport

    reports = WeeklyReport.query.filter_by(
        user_id=current_user.id
    ).order_by(WeeklyReport.week_start.desc()).limit(12).all()

    return render_template("n8n/weekly_report.html", reports=reports)


@n8n_bp.route("/study-planner")
@student_accessible
def study_planner():
    """AI Study Planner page."""
    from automation.services.study_planner import get_user_plans, get_today_tasks
    from models import Course

    plans = get_user_plans(current_user.id)
    today = get_today_tasks(current_user)
    courses = Course.query.order_by(Course.title.asc()).all()

    return render_template(
        "n8n/study_planner.html",
        plans=plans,
        today=today,
        courses=courses,
    )


@n8n_bp.route("/study-planner/create", methods=["POST"])
@csrf.exempt
@student_accessible
def study_planner_create():
    """Create a new study plan."""
    data = request.get_json(silent=True) or {}

    exam_name = data.get("exam_name", "").strip()
    exam_date_str = data.get("exam_date", "")
    course_ids = data.get("course_ids", [])

    if not exam_name or not exam_date_str or not course_ids:
        return jsonify({"error": "Exam name, date, and courses are required."}), 400

    try:
        exam_date = date.fromisoformat(exam_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format."}), 400

    from automation.services.study_planner import create_plan
    result = create_plan(current_user, exam_name, exam_date, course_ids)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


@n8n_bp.route("/study-planner/<int:plan_id>")
@student_accessible
def study_plan_detail(plan_id):
    """View a specific study plan."""
    from automation.services.study_planner import get_plan_details

    plan = get_plan_details(plan_id, current_user.id)
    if not plan:
        flash("Study plan not found.", "warning")
        return redirect(url_for("n8n.study_planner"))

    return render_template("n8n/study_planner.html", plan_detail=plan, plans=[], today={"plans": []}, courses=[])


@n8n_bp.route("/study-planner/<int:day_id>/complete", methods=["POST"])
@csrf.exempt
@student_accessible
def study_plan_complete_day(day_id):
    """Mark a study plan day as completed."""
    from automation.services.study_planner import mark_day_complete
    success = mark_day_complete(day_id, current_user.id)
    return jsonify({"success": success})


@n8n_bp.route("/career")
@student_accessible
def career_assistant():
    """Career & Resume assistant."""
    from automation.services.career import get_latest_recommendation
    recommendation = get_latest_recommendation(current_user.id)
    return render_template("n8n/career_assistant.html", recommendation=recommendation)


@n8n_bp.route("/career/generate", methods=["POST"])
@csrf.exempt
@student_accessible
def career_generate():
    """Generate career recommendations."""
    from automation.services.career import generate_recommendations
    result = generate_recommendations(current_user)
    return jsonify(result)


@n8n_bp.route("/feedback", methods=["GET", "POST"])
@student_accessible
def feedback():
    """Feedback submission form."""
    from models import Course

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        course_id = data.get("course_id")
        rating = data.get("rating")

        if not text:
            return jsonify({"error": "Feedback text is required."}), 400

        from automation.services.feedback import submit_feedback
        result = submit_feedback(current_user, course_id, text, rating)
        return jsonify(result)

    courses = Course.query.order_by(Course.title.asc()).all()
    return render_template("n8n/feedback.html", courses=courses)


@n8n_bp.route("/verify/<cert_code>")
def verify_certificate(cert_code):
    """Public certificate verification — no login required."""
    from automation.services.cert_pipeline import verify_certificate
    result = verify_certificate(cert_code)
    return render_template("n8n/cert_verify.html", result=result, cert_code=cert_code)


# ══════════════════════════════════════════════════════════════════
#  INSTRUCTOR PAGES
# ══════════════════════════════════════════════════════════════════

@n8n_bp.route("/instructor/workflows")
@instructor_required
def instructor_workflows():
    """Course-specific workflow status for instructors."""
    return render_template("n8n/instructor_dashboard.html")


# ══════════════════════════════════════════════════════════════════
#  JSON API ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@n8n_bp.route("/api/workflows")
@admin_required
def api_workflows():
    """List all workflow configurations."""
    from automation.models import N8NWorkflowConfig
    configs = N8NWorkflowConfig.query.all()
    return jsonify([
        {
            "id": c.id,
            "workflow_name": c.workflow_name,
            "webhook_url": c.webhook_url,
            "is_enabled": c.is_enabled,
            "cron_expression": c.cron_expression,
            "description": c.description,
            "last_triggered_at": c.last_triggered_at.isoformat() if c.last_triggered_at else None,
        }
        for c in configs
    ])


@n8n_bp.route("/api/logs")
@admin_required
def api_logs():
    """Paginated workflow execution logs."""
    from automation.models import N8NWorkflowLog

    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")
    workflow = request.args.get("workflow", "")

    query = N8NWorkflowLog.query
    if status:
        query = query.filter_by(status=status)
    if workflow:
        query = query.filter_by(workflow_name=workflow)

    pagination = query.order_by(N8NWorkflowLog.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return jsonify({
        "logs": [
            {
                "id": l.id,
                "workflow_name": l.workflow_name,
                "status": l.status,
                "execution_time_ms": l.execution_time_ms,
                "retry_count": l.retry_count,
                "error_message": l.error_message,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in pagination.items
        ],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
    })


@n8n_bp.route("/api/stats")
@admin_required
def api_stats():
    """Advanced automation analytics."""
    from automation.models import N8NWorkflowLog, AIMentorConversation
    from sqlalchemy import func

    total = N8NWorkflowLog.query.count()
    success = N8NWorkflowLog.query.filter_by(status="success").count()
    failed = N8NWorkflowLog.query.filter_by(status="failed").count()

    avg_time = db.session.query(func.avg(N8NWorkflowLog.execution_time_ms)).filter(
        N8NWorkflowLog.execution_time_ms.isnot(None)
    ).scalar() or 0

    avg_retries = db.session.query(func.avg(N8NWorkflowLog.retry_count)).scalar() or 0

    # Most used workflow
    most_used = db.session.query(
        N8NWorkflowLog.workflow_name, func.count(N8NWorkflowLog.id).label("cnt")
    ).group_by(N8NWorkflowLog.workflow_name).order_by(func.count(N8NWorkflowLog.id).desc()).first()

    # Avg AI response time
    avg_ai_time = db.session.query(func.avg(AIMentorConversation.response_time_ms)).filter(
        AIMentorConversation.response_time_ms.isnot(None)
    ).scalar() or 0

    return jsonify({
        "total_executions": total,
        "successful": success,
        "failed": failed,
        "success_rate": round(success / total * 100) if total else 0,
        "avg_execution_time_ms": round(float(avg_time)),
        "avg_retries": round(float(avg_retries), 1),
        "most_used_workflow": most_used[0] if most_used else None,
        "most_used_count": most_used[1] if most_used else 0,
        "avg_ai_response_time_ms": round(float(avg_ai_time)),
    })


@n8n_bp.route("/api/health")
def api_health():
    """System health endpoint — reads cached metrics."""
    from automation.health import get_health_status
    return jsonify(get_health_status())


@n8n_bp.route("/api/queue")
@admin_required
def api_queue():
    """Redis queue status."""
    from automation.queue import get_queue_status
    return jsonify(get_queue_status())


@n8n_bp.route("/api/builder/rules", methods=["GET"])
@admin_required
def api_builder_rules_list():
    """List automation builder rules."""
    from automation.builder import get_all_rules
    return jsonify(get_all_rules())


@n8n_bp.route("/api/builder/rules", methods=["POST"])
@csrf.exempt
@admin_required
def api_builder_rules_create():
    """Create a new automation rule."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    trigger_event = data.get("trigger_event", "").strip()
    conditions = data.get("conditions", [])
    actions = data.get("actions", [])

    if not name or not trigger_event:
        return jsonify({"error": "Name and trigger event are required."}), 400

    from automation.builder import create_rule
    result = create_rule(name, trigger_event, conditions, actions, current_user.id)
    return jsonify(result)


@n8n_bp.route("/api/builder/rules/<int:rule_id>", methods=["PUT"])
@csrf.exempt
@admin_required
def api_builder_rules_update(rule_id):
    """Update a rule."""
    data = request.get_json(silent=True) or {}
    from automation.builder import update_rule
    success = update_rule(rule_id, **data)
    return jsonify({"success": success})


@n8n_bp.route("/api/builder/rules/<int:rule_id>", methods=["DELETE"])
@csrf.exempt
@admin_required
def api_builder_rules_delete(rule_id):
    """Delete a rule."""
    from automation.builder import delete_rule
    success = delete_rule(rule_id)
    return jsonify({"success": success})


@n8n_bp.route("/api/workflows/<int:config_id>/toggle", methods=["POST"])
@csrf.exempt
@admin_required
def api_workflow_toggle(config_id):
    """Enable/disable a workflow."""
    from automation.models import N8NWorkflowConfig
    config = N8NWorkflowConfig.query.get_or_404(config_id)
    config.is_enabled = not config.is_enabled
    db.session.commit()
    return jsonify({"id": config.id, "is_enabled": config.is_enabled})


@n8n_bp.route("/api/spec")
def api_spec():
    """Return raw OpenAPI spec as JSON."""
    from automation.swagger import get_openapi_spec
    return jsonify(get_openapi_spec())


# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════

def _log_webhook_event(event_type: str, data: dict):
    """Log a webhook event to the automation timeline."""
    try:
        from automation.models import AutomationEvent
        event = AutomationEvent(
            user_id=data.get("user_id"),
            event_type=event_type,
            title=event_type.replace("_", " ").title(),
            detail=json.dumps(data, default=str)[:500],
            source="n8n",
        )
        db.session.add(event)
        db.session.commit()
    except Exception:
        pass
