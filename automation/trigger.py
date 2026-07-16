"""
automation.trigger — Explicit event dispatch
=============================================
Existing blueprints call ``fire()`` at the *exact* point where a meaningful
event occurs (registration, course completion, etc.).

    from automation.trigger import fire
    fire("course_completed", user_id=1, course_id=5, score=8, total=10)

The call is:
  • **Non-blocking** — enqueues to Redis in a background thread.
  • **Fail-safe**    — wrapped in try/except; cannot crash the caller.
  • **Idempotent**   — duplicate events within 5 s are silently dropped.
"""

import logging
import threading
import time
import json
import hashlib
from datetime import datetime

from flask import current_app

logger = logging.getLogger("automation.trigger")

# Simple in-memory deduplication cache (event_hash → timestamp)
_recent_events: dict[str, float] = {}
_DEDUP_WINDOW = 5.0  # seconds


def _event_hash(event_name: str, kwargs: dict) -> str:
    """Create a short hash for deduplication."""
    raw = f"{event_name}:{json.dumps(kwargs, sort_keys=True, default=str)}"
    return hashlib.md5(raw.encode()).hexdigest()


def _cleanup_cache():
    """Remove expired entries from the dedup cache."""
    now = time.time()
    expired = [k for k, ts in _recent_events.items() if now - ts > _DEDUP_WINDOW]
    for k in expired:
        _recent_events.pop(k, None)


def _dispatch(app, event_name: str, payload: dict):
    """Background worker that pushes the event to the automation pipeline."""
    with app.app_context():
        try:
            # 1. Log as an AutomationEvent (student activity timeline)
            from automation.models import AutomationEvent
            from extensions import db

            event = AutomationEvent(
                user_id=payload.get("user_id"),
                event_type=event_name,
                title=_human_title(event_name),
                detail=json.dumps(payload, default=str),
                source="flask",
            )
            db.session.add(event)
            db.session.commit()

            # 2. Evaluate Automation Builder rules
            from automation.builder import evaluate_rules
            evaluate_rules(event_name, payload)

            # 3. Enqueue for n8n dispatch (via Redis)
            if app.config.get("N8N_ENABLED"):
                from automation.queue import enqueue_workflow
                enqueue_workflow(event_name, payload)

        except Exception:
            logger.exception("Error dispatching event '%s'", event_name)


def _human_title(event_name: str) -> str:
    """Convert event_name to a human-readable title."""
    titles = {
        "user_registered": "New User Registration",
        "course_enrolled": "Course Enrolled",
        "course_completed": "Course Completed",
        "bite_completed": "Lesson Completed",
        "coding_submitted": "Code Submitted",
        "feedback_submitted": "Feedback Submitted",
        "course_uploaded": "New Course Published",
        "ai_mentor_used": "AI Mentor Interaction",
        "study_plan_created": "Study Plan Created",
        "certificate_generated": "Certificate Generated",
        "achievement_earned": "Achievement Earned",
    }
    return titles.get(event_name, event_name.replace("_", " ").title())


def fire(event_name: str, **kwargs):
    """Fire an automation event.  Safe to call from anywhere.

    This function returns immediately.  Processing happens in a background
    thread so the caller (e.g. the registration route) is never delayed.

    Parameters
    ----------
    event_name : str
        One of the defined event names (``user_registered``, ``course_completed``, …).
    **kwargs
        Arbitrary payload data (``user_id``, ``course_id``, ``score``, …).
    """
    try:
        # Deduplication
        _cleanup_cache()
        h = _event_hash(event_name, kwargs)
        if h in _recent_events:
            return  # duplicate within window — skip
        _recent_events[h] = time.time()

        # Add timestamp to payload
        kwargs["_event"] = event_name
        kwargs["_timestamp"] = datetime.utcnow().isoformat()

        # Dispatch in background thread
        app = current_app._get_current_object()
        t = threading.Thread(target=_dispatch, args=(app, event_name, kwargs), daemon=True)
        t.start()

    except Exception:
        # Absolute last resort — never crash the caller
        logger.exception("fire() failed for event '%s'", event_name)
