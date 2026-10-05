"""
automation.health — Passive Health Monitoring
===============================================
Health metrics are collected **passively** from real operations — never by
polling external services.  This means no wasted API calls.

When the n8n client dispatches a workflow → it updates the n8n HealthMetric.
When the AI Mentor calls OpenAI → it updates the openai HealthMetric.
When the email service sends → it updates the email HealthMetric.

The ``/n8n/health`` endpoint simply reads the latest cached metrics from the
``health_metrics`` table.
"""

import logging
from datetime import datetime

logger = logging.getLogger("automation.health")


def init_health(app):
    """Initialise health metric records for all known components.

    Called once from ``init_automation()``.
    """
    with app.app_context():
        from automation.models import HealthMetric
        from extensions import db

        try:
            components = ["n8n", "redis", "openai", "email"]
            for component in components:
                existing = HealthMetric.query.filter_by(component=component).first()
                if not existing:
                    metric = HealthMetric(
                        component=component,
                        status="unknown",
                        updated_at=datetime.utcnow(),
                    )
                    db.session.add(metric)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.debug("Health metrics already initialised or table does not exist: %s", exc)


def update_health(component: str, success: bool, latency_ms: float = 0, error: str = None):
    """Update health metrics for a component.  Called from service code.

    Parameters
    ----------
    component : str
        One of: ``n8n``, ``redis``, ``openai``, ``email``.
    success : bool
        Whether the operation succeeded.
    latency_ms : float
        How long the operation took in milliseconds.
    error : str, optional
        Error message if the operation failed.
    """
    try:
        from automation.models import HealthMetric
        from extensions import db

        metric = HealthMetric.query.filter_by(component=component).first()
        if not metric:
            metric = HealthMetric(component=component)
            db.session.add(metric)

        now = datetime.utcnow()

        if success:
            metric.status = "up"
            metric.last_success_at = now
            # Exponential moving average for latency
            if metric.avg_latency_ms and metric.avg_latency_ms > 0:
                metric.avg_latency_ms = (metric.avg_latency_ms * 0.8) + (latency_ms * 0.2)
            else:
                metric.avg_latency_ms = latency_ms
        else:
            metric.status = "down"
            metric.last_failure_at = now
            if error:
                metric.last_error = error[:500]

        metric.total_calls_today = (metric.total_calls_today or 0) + 1
        metric.updated_at = now

        db.session.commit()
    except Exception:
        logger.debug("Could not update health metric for '%s'", component)
        try:
            from extensions import db
            db.session.rollback()
        except Exception:
            pass


def get_health_status() -> dict:
    """Read the current health status from cached metrics."""
    try:
        from automation.models import HealthMetric

        metrics = HealthMetric.query.all()
        components = {}

        for m in metrics:
            components[m.component] = {
                "status": m.status or "unknown",
                "last_success": m.last_success_at.isoformat() if m.last_success_at else None,
                "last_failure": m.last_failure_at.isoformat() if m.last_failure_at else None,
                "last_error": m.last_error,
                "avg_latency_ms": round(m.avg_latency_ms, 1) if m.avg_latency_ms else 0,
                "total_calls_today": m.total_calls_today or 0,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }

        # Check Redis separately (can do a quick ping)
        from automation.queue import is_redis_available
        if "redis" in components:
            components["redis"]["queue_available"] = is_redis_available()
            if is_redis_available():
                components["redis"]["status"] = "up"
                from automation.queue import get_queue_status
                components["redis"].update(get_queue_status())

        # Overall status
        statuses = [c.get("status", "unknown") for c in components.values()]
        if all(s == "up" for s in statuses):
            overall = "healthy"
        elif any(s == "down" for s in statuses):
            overall = "degraded"
        else:
            overall = "unknown"

        return {
            "status": overall,
            "components": components,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "components": {},
            "timestamp": datetime.utcnow().isoformat(),
        }
