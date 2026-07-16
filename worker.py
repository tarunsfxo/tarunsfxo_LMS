"""
Tarunsfxo LMS — Redis Queue Worker
==================================
Runs alongside the main Flask application to process background tasks
asynchronously and reliably.

Usage:
    python worker.py
"""

import sys
import logging
from redis import Redis
from rq import Queue, Worker, Connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("worker")

# Read REDIS_URL from env or configuration
REDIS_URL = "redis://localhost:6379/0"


def run_worker():
    logger.info("Starting Tarunsfxo LMS Automation Worker...")
    try:
        redis_conn = Redis.from_url(REDIS_URL)
        # Test connection
        redis_conn.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as exc:
        logger.error("Could not connect to Redis at %s: %s", REDIS_URL, exc)
        logger.error("Please ensure the Redis service is running.")
        sys.exit(1)

    # Establish the connection and start the worker
    with Connection(redis_conn):
        worker = Worker([Queue("automation")])
        worker.work()


if __name__ == "__main__":
    run_worker()
