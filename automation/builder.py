"""
automation.builder — Automation Builder Rule Engine
=====================================================
Allows admins to create IF/THEN automation rules inside the LMS.
When ``automation.trigger.fire()`` fires an event, the builder engine
loads matching rules and executes their actions.

Example rule:
    IF course_completed AND score >= 80%
    THEN award_badge("Course Graduate") + send_email("congrats") + trigger_workflow("recommend_next")
"""

import json
import logging
from datetime import datetime

from extensions import db

logger = logging.getLogger("automation.builder")

# Cache of active rules (loaded on init, refreshed on changes)
_rules_cache: list = []


def init_builder(app):
    """Load active rules from the database into the in-memory cache."""
    with app.app_context():
        _refresh_rules_cache()


def _refresh_rules_cache():
    """Reload rules from database into memory."""
    global _rules_cache
    try:
        from automation.models import AutomationRule

        rules = AutomationRule.query.filter_by(is_enabled=True).all()
        _rules_cache = [
            {
                "id": r.id,
                "name": r.name,
                "trigger_event": r.trigger_event,
                "conditions": json.loads(r.conditions_json) if r.conditions_json else [],
                "actions": json.loads(r.actions_json) if r.actions_json else [],
            }
            for r in rules
        ]
        logger.debug("Loaded %d automation rules into cache", len(_rules_cache))
    except Exception:
        _rules_cache = []
        logger.debug("Could not load automation rules (table may not exist yet)")


def evaluate_rules(event_name: str, payload: dict):
    """Evaluate all active rules against a fired event.

    Called from ``automation.trigger._dispatch()``.
    """
    matching_rules = [r for r in _rules_cache if r["trigger_event"] == event_name]

    for rule in matching_rules:
        try:
            # Check conditions
            if _evaluate_conditions(rule["conditions"], payload):
                _execute_actions(rule["actions"], payload)

                # Update execution count
                _update_rule_stats(rule["id"])

                logger.info("Rule '%s' executed for event '%s'", rule["name"], event_name)
        except Exception:
            logger.exception("Error evaluating rule '%s'", rule["name"])


def create_rule(name: str, trigger_event: str, conditions: list, actions: list, created_by: int) -> dict:
    """Create a new automation rule."""
    from automation.models import AutomationRule

    rule = AutomationRule(
        name=name,
        trigger_event=trigger_event,
        conditions_json=json.dumps(conditions),
        actions_json=json.dumps(actions),
        is_enabled=True,
        created_by=created_by,
    )
    db.session.add(rule)
    db.session.commit()

    # Refresh cache
    _refresh_rules_cache()

    return {"id": rule.id, "name": rule.name}


def update_rule(rule_id: int, **kwargs) -> bool:
    """Update an existing rule."""
    from automation.models import AutomationRule

    rule = AutomationRule.query.get(rule_id)
    if not rule:
        return False

    if "name" in kwargs:
        rule.name = kwargs["name"]
    if "trigger_event" in kwargs:
        rule.trigger_event = kwargs["trigger_event"]
    if "conditions" in kwargs:
        rule.conditions_json = json.dumps(kwargs["conditions"])
    if "actions" in kwargs:
        rule.actions_json = json.dumps(kwargs["actions"])
    if "is_enabled" in kwargs:
        rule.is_enabled = kwargs["is_enabled"]

    db.session.commit()
    _refresh_rules_cache()
    return True


def delete_rule(rule_id: int) -> bool:
    """Delete a rule."""
    from automation.models import AutomationRule

    rule = AutomationRule.query.get(rule_id)
    if not rule:
        return False

    db.session.delete(rule)
    db.session.commit()
    _refresh_rules_cache()
    return True


def get_all_rules() -> list:
    """Get all rules for the admin UI."""
    from automation.models import AutomationRule

    rules = AutomationRule.query.order_by(AutomationRule.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "trigger_event": r.trigger_event,
            "conditions": json.loads(r.conditions_json) if r.conditions_json else [],
            "actions": json.loads(r.actions_json) if r.actions_json else [],
            "is_enabled": r.is_enabled,
            "execution_count": r.execution_count,
            "last_executed_at": r.last_executed_at.isoformat() if r.last_executed_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rules
    ]


# Available triggers and actions for the builder UI
AVAILABLE_TRIGGERS = [
    {"event": "user_registered", "label": "User Registered", "icon": "👤"},
    {"event": "course_enrolled", "label": "Course Enrolled", "icon": "📚"},
    {"event": "course_completed", "label": "Course Completed", "icon": "🎓"},
    {"event": "bite_completed", "label": "Lesson Completed", "icon": "📖"},
    {"event": "coding_submitted", "label": "Code Submitted", "icon": "💻"},
    {"event": "feedback_submitted", "label": "Feedback Submitted", "icon": "📝"},
    {"event": "certificate_generated", "label": "Certificate Generated", "icon": "🏆"},
    {"event": "ai_mentor_used", "label": "AI Mentor Used", "icon": "🤖"},
    {"event": "study_plan_created", "label": "Study Plan Created", "icon": "📅"},
]

AVAILABLE_ACTIONS = [
    {"action": "send_email", "label": "Send Email", "icon": "📧", "params": ["template"]},
    {"action": "award_badge", "label": "Award Badge", "icon": "🏅", "params": ["badge_name", "badge_icon", "description"]},
    {"action": "award_xp", "label": "Award XP", "icon": "⭐", "params": ["amount", "reason"]},
    {"action": "send_notification", "label": "Send Notification", "icon": "🔔", "params": ["title", "message", "type"]},
    {"action": "trigger_workflow", "label": "Trigger n8n Workflow", "icon": "⚡", "params": ["workflow_name"]},
    {"action": "create_timeline_event", "label": "Create Timeline Event", "icon": "📋", "params": ["title"]},
]

CONDITION_OPERATORS = ["equals", "not_equals", "greater_than", "less_than", "contains"]


# ── Private helpers ─────────────────────────────────────────────


def _evaluate_conditions(conditions: list, payload: dict) -> bool:
    """Evaluate whether all conditions are met."""
    if not conditions:
        return True  # No conditions = always match

    for cond in conditions:
        field = cond.get("field", "")
        operator = cond.get("operator", "equals")
        value = cond.get("value")

        actual_value = payload.get(field)
        if actual_value is None:
            return False

        if operator == "equals" and str(actual_value) != str(value):
            return False
        elif operator == "not_equals" and str(actual_value) == str(value):
            return False
        elif operator == "greater_than":
            try:
                if float(actual_value) <= float(value):
                    return False
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                if float(actual_value) >= float(value):
                    return False
            except (ValueError, TypeError):
                return False
        elif operator == "contains":
            if str(value).lower() not in str(actual_value).lower():
                return False

    return True


def _execute_actions(actions: list, payload: dict):
    """Execute the actions defined in a rule."""
    user_id = payload.get("user_id")

    for action_def in actions:
        action = action_def.get("action")
        params = action_def.get("params", {})

        try:
            if action == "send_email":
                _action_send_email(user_id, params)
            elif action == "award_badge":
                _action_award_badge(user_id, params)
            elif action == "award_xp":
                _action_award_xp(user_id, params)
            elif action == "send_notification":
                _action_send_notification(user_id, params)
            elif action == "trigger_workflow":
                _action_trigger_workflow(params, payload)
            elif action == "create_timeline_event":
                _action_create_timeline(user_id, params)
            else:
                logger.warning("Unknown action: %s", action)
        except Exception:
            logger.exception("Failed to execute action '%s'", action)


def _action_send_email(user_id, params):
    """Send email action."""
    if not user_id:
        return
    from models import User
    user = User.query.get(user_id)
    if user:
        from automation.services.email import send_email
        template = params.get("template", "emails/welcome.html")
        send_email(user.email, "Tarunsfxo LMS Notification", template=template, user=user)


def _action_award_badge(user_id, params):
    """Award badge action."""
    if not user_id:
        return
    from gamification import unlock_badge
    from models import User
    user = User.query.get(user_id)
    if user:
        unlock_badge(
            user,
            params.get("badge_name", "Custom Badge"),
            params.get("badge_icon", "🏅"),
            params.get("description", "Earned via automation rule"),
        )
        db.session.commit()


def _action_award_xp(user_id, params):
    """Award XP action."""
    if not user_id:
        return
    from gamification import award_xp
    from models import User
    user = User.query.get(user_id)
    if user:
        amount = int(params.get("amount", 10))
        reason = params.get("reason", "automation_rule")
        award_xp(user, amount, reason)


def _action_send_notification(user_id, params):
    """Send in-app notification action."""
    if not user_id:
        return
    from models import UserNotification
    notif = UserNotification(
        user_id=user_id,
        title=params.get("title", "Notification"),
        message=params.get("message", ""),
        type=params.get("type", "automation"),
    )
    db.session.add(notif)
    db.session.commit()


def _action_trigger_workflow(params, payload):
    """Trigger an n8n workflow action."""
    workflow_name = params.get("workflow_name")
    if workflow_name:
        from automation.queue import enqueue_workflow
        enqueue_workflow(workflow_name, payload)


def _action_create_timeline(user_id, params):
    """Create a timeline event action."""
    from automation.models import AutomationEvent
    event = AutomationEvent(
        user_id=user_id,
        event_type="automation_rule",
        title=params.get("title", "Automation Event"),
        source="builder",
    )
    db.session.add(event)
    db.session.commit()


def _update_rule_stats(rule_id: int):
    """Update execution count and last executed timestamp for a rule."""
    try:
        from automation.models import AutomationRule
        rule = AutomationRule.query.get(rule_id)
        if rule:
            rule.execution_count = (rule.execution_count or 0) + 1
            rule.last_executed_at = datetime.utcnow()
            db.session.commit()
    except Exception:
        pass
