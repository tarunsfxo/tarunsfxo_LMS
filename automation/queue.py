"""
automation.queue — Redis-backed reliable async dispatch
========================================================
Workflow triggers are pushed to a Redis queue.  A separate ``worker.py``
process picks them up and sends HTTP requests to n8n.  If n8n is offline
the job stays in the queue and is retried automatically.

In development (or if Redis is unreachable) the queue falls back to
synchronous HTTP dispatch so the system still functions.
"""

import json
import logging
from datetime import datetime

from flask import current_app

logger = logging.getLogger("automation.queue")

# Module-level state
_redis_conn = None
_rq_queue = None
_redis_available = False


def init_queue(app):
    """Initialise the Redis connection.  Called once from ``init_automation()``."""
    global _redis_conn, _rq_queue, _redis_available

    redis_url = app.config.get("REDIS_URL", "redis://localhost:6379/0")

    try:
        import redis as _redis
        from rq import Queue

        _redis_conn = _redis.from_url(redis_url, socket_connect_timeout=3)
        _redis_conn.ping()  # verify connection
        _rq_queue = Queue("automation", connection=_redis_conn)
        _redis_available = True
        logger.info("Redis connected at %s", redis_url)

    except Exception as exc:
        _redis_available = False
        logger.warning(
            "Redis unavailable (%s) — falling back to synchronous dispatch. "
            "Install redis and rq, or start a Redis server for production use.",
            exc,
        )


def enqueue_workflow(workflow_name: str, payload: dict):
    """Add a workflow dispatch job to the Redis queue.

    Falls back to synchronous HTTP if Redis is unavailable.
    """
    if _redis_available and _redis_conn is not None:
        try:
            # Publish to Redis Pub/Sub for n8n email notification workflows
            pubsub_message = {"event": workflow_name}
            pubsub_message.update(payload)
            _redis_conn.publish("automation", json.dumps(pubsub_message, default=str))
        except Exception:
            logger.exception("Failed to publish to Redis Pub/Sub")

    if _redis_available and _rq_queue is not None:
        try:
            _rq_queue.enqueue(
                "automation.client.dispatch_workflow",
                workflow_name,
                payload,
                retry=3,
                job_timeout="5m",
            )
            logger.debug("Enqueued workflow '%s' to Redis", workflow_name)
            return
        except Exception:
            logger.exception("Failed to enqueue to Redis, falling back to sync")

    # Fallback: synchronous dispatch
    try:
        from automation.client import dispatch_workflow
        dispatch_workflow(workflow_name, payload)
    except Exception:
        logger.exception("Synchronous dispatch also failed for '%s'", workflow_name)


def get_queue_status() -> dict:
    """Return current queue statistics."""
    if not _redis_available or _rq_queue is None:
        return {
            "available": False,
            "pending": 0,
            "active": 0,
            "failed": 0,
            "completed": 0,
        }

    try:
        from rq import Queue
        from rq.registry import FailedJobRegistry, FinishedJobRegistry, StartedJobRegistry

        failed_reg = FailedJobRegistry(queue=_rq_queue)
        finished_reg = FinishedJobRegistry(queue=_rq_queue)
        started_reg = StartedJobRegistry(queue=_rq_queue)

        return {
            "available": True,
            "pending": len(_rq_queue),
            "active": len(started_reg),
            "failed": len(failed_reg),
            "completed": len(finished_reg),
        }
    except Exception as exc:
        logger.warning("Could not read queue status: %s", exc)
        return {"available": False, "pending": 0, "active": 0, "failed": 0, "completed": 0}


def get_failed_jobs() -> list:
    """Return a list of failed jobs for admin review."""
    if not _redis_available or _rq_queue is None:
        return []

    try:
        from rq.registry import FailedJobRegistry

        failed_reg = FailedJobRegistry(queue=_rq_queue)
        jobs = []
        for job_id in failed_reg.get_job_ids():
            job = _rq_queue.fetch_job(job_id)
            if job:
                jobs.append({
                    "id": job.id,
                    "func_name": job.func_name,
                    "args": str(job.args),
                    "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
                    "exc_info": job.exc_info,
                })
        return jobs
    except Exception:
        return []


def retry_failed_job(job_id: str) -> bool:
    """Retry a specific failed job."""
    if not _redis_available or _rq_queue is None:
        return False

    try:
        from rq.registry import FailedJobRegistry

        failed_reg = FailedJobRegistry(queue=_rq_queue)
        failed_reg.requeue(job_id)
        return True
    except Exception:
        logger.exception("Failed to retry job %s", job_id)
        return False


def is_redis_available() -> bool:
    """Check if Redis is currently reachable."""
    return _redis_available
