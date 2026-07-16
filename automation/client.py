"""
automation.client — n8n HTTP Webhook Dispatcher
=================================================
Used by the Redis worker process (``worker.py``) to send HTTP POST requests
to n8n webhook endpoints.  Not called directly from Flask routes.

Features:
  • Retry: 3 attempts with exponential backoff (1 s → 2 s → 4 s)
  • Logs every execution to ``N8NWorkflowLog``
  • Updates ``HealthMetric`` for the n8n component passively
"""

import json
import logging
import time
from datetime import datetime

logger = logging.getLogger("automation.client")


def dispatch_workflow(workflow_name: str, payload: dict):
    """Dispatch a workflow to n8n via HTTP webhook.

    This function is typically called by the rq worker, but can also
    be called synchronously in dev mode.
    """
    import os

    # Read config from env (worker may not have Flask app context)
    base_url = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
    webhook_secret = os.environ.get("N8N_WEBHOOK_SECRET", "dev-webhook-secret")

    # Try to read workflow-specific URL from database, fall back to convention
    webhook_url = _get_webhook_url(workflow_name, base_url)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Secret": webhook_secret,
    }

    max_retries = 3
    retry_count = 0
    last_error = None
    start_time = time.time()

    for attempt in range(1, max_retries + 1):
        try:
            import httpx

            with httpx.Client(timeout=30.0) as client:
                response = client.post(webhook_url, json=payload, headers=headers)

            elapsed_ms = int((time.time() - start_time) * 1000)

            if response.status_code < 400:
                _log_execution(workflow_name, "success", payload, response.text, elapsed_ms, retry_count)
                _update_health("n8n", success=True, latency_ms=elapsed_ms)
                logger.info(
                    "Workflow '%s' dispatched successfully (%d ms, %d retries)",
                    workflow_name, elapsed_ms, retry_count,
                )
                return

            last_error = f"HTTP {response.status_code}: {response.text[:500]}"
            retry_count += 1
            logger.warning(
                "Workflow '%s' attempt %d failed: %s", workflow_name, attempt, last_error
            )

        except Exception as exc:
            last_error = str(exc)
            retry_count += 1
            logger.warning(
                "Workflow '%s' attempt %d error: %s", workflow_name, attempt, last_error
            )

        if attempt < max_retries:
            backoff = 2 ** (attempt - 1)  # 1s, 2s, 4s
            time.sleep(backoff)

    # All retries exhausted
    elapsed_ms = int((time.time() - start_time) * 1000)
    _log_execution(workflow_name, "failed", payload, None, elapsed_ms, retry_count, last_error)
    _update_health("n8n", success=False, error=last_error)
    logger.error("Workflow '%s' FAILED after %d retries: %s", workflow_name, max_retries, last_error)


def _get_webhook_url(workflow_name: str, base_url: str) -> str:
    """Get the webhook URL for a workflow.  Tries DB first, then convention."""
    try:
        # Try to read from app context / database
        from flask import current_app
        from automation.models import N8NWorkflowConfig

        config = N8NWorkflowConfig.query.filter_by(
            workflow_name=workflow_name, is_enabled=True
        ).first()
        if config and config.webhook_url:
            return config.webhook_url
    except Exception:
        pass  # No app context (running in worker) or table not yet created

    # Convention: base_url/webhook/<workflow_name>
    return f"{base_url}/webhook/{workflow_name}"


def _log_execution(workflow_name, status, payload, response_text, elapsed_ms, retry_count, error=None):
    """Log workflow execution to the database."""
    try:
        from app import create_app
        from automation.models import N8NWorkflowLog
        from extensions import db

        # Try existing app context first, create one if needed
        try:
            from flask import current_app
            _ = current_app.name  # test if context exists
            _do_log(workflow_name, status, payload, response_text, elapsed_ms, retry_count, error)
        except RuntimeError:
            # No app context — create one (worker process)
            app = create_app()
            with app.app_context():
                _do_log(workflow_name, status, payload, response_text, elapsed_ms, retry_count, error)
    except Exception:
        logger.exception("Failed to log workflow execution for '%s'", workflow_name)


def _do_log(workflow_name, status, payload, response_text, elapsed_ms, retry_count, error):
    """Actually write the log entry (must be called within app context)."""
    from automation.models import N8NWorkflowLog, N8NWorkflowConfig
    from extensions import db

    log = N8NWorkflowLog(
        workflow_name=workflow_name,
        status=status,
        payload_json=json.dumps(payload, default=str) if payload else None,
        response_json=response_text[:2000] if response_text else None,
        execution_time_ms=elapsed_ms,
        retry_count=retry_count,
        error_message=error,
        completed_at=datetime.utcnow() if status in ("success", "failed") else None,
    )
    db.session.add(log)

    # Update last_triggered_at on the workflow config
    config = N8NWorkflowConfig.query.filter_by(workflow_name=workflow_name).first()
    if config:
        config.last_triggered_at = datetime.utcnow()

    db.session.commit()


def _update_health(component: str, success: bool, latency_ms: int = 0, error: str = None):
    """Passively update health metrics from real operations."""
    try:
        from flask import current_app
        _ = current_app.name
        _do_update_health(component, success, latency_ms, error)
    except RuntimeError:
        try:
            from app import create_app
            app = create_app()
            with app.app_context():
                _do_update_health(component, success, latency_ms, error)
        except Exception:
            pass


def _do_update_health(component, success, latency_ms, error):
    """Actually update health metric (must be called within app context)."""
    from automation.models import HealthMetric
    from extensions import db

    metric = HealthMetric.query.filter_by(component=component).first()
    if not metric:
        metric = HealthMetric(component=component)
        db.session.add(metric)

    if success:
        metric.status = "up"
        metric.last_success_at = datetime.utcnow()
        # Rolling average latency
        if metric.avg_latency_ms:
            metric.avg_latency_ms = (metric.avg_latency_ms * 0.8) + (latency_ms * 0.2)
        else:
            metric.avg_latency_ms = latency_ms
    else:
        metric.status = "down"
        metric.last_failure_at = datetime.utcnow()
        metric.last_error = error[:500] if error else None

    metric.total_calls_today = (metric.total_calls_today or 0) + 1
    metric.updated_at = datetime.utcnow()
    db.session.commit()
