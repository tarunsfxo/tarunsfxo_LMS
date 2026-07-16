"""
Tarunsfxo LMS — Automation Package
===================================
Central automation integration for n8n workflows, AI services, and background
task management.  The single entry point ``init_automation(app)`` is called
from ``app.py`` once — it handles blueprint registration, Redis setup, model
imports, and health metric collection.

Design principles:
  • Non-invasive — never modifies existing tables or routes.
  • Fail-safe   — if Redis / n8n / OpenAI are offline the LMS keeps working.
  • Modular     — each sub-module can be disabled independently.
"""

import logging

logger = logging.getLogger("automation")


def init_automation(app):
    """Initialise the entire automation subsystem.

    Called once from ``create_app()`` in ``app.py``:

        from automation import init_automation
        init_automation(app)
    """

    # 1. Load automation-specific config defaults
    app.config.setdefault("N8N_ENABLED", True)
    app.config.setdefault("N8N_BASE_URL", "http://localhost:5678")
    app.config.setdefault("N8N_WEBHOOK_SECRET", "dev-webhook-secret")
    app.config.setdefault("REDIS_URL", "redis://localhost:6379/0")
    app.config.setdefault("OPENAI_API_KEY", "")
    app.config.setdefault("OPENAI_MODEL", "gpt-4o-mini")
    app.config.setdefault("EMAIL_PROVIDER", "console")

    # 2. Import automation models so Flask-Migrate / db.create_all() can see them
    from automation import models as _models  # noqa: F401

    # 3. Initialise Redis connection (graceful fallback if unavailable)
    from automation.queue import init_queue
    init_queue(app)

    # 4. Initialise health metric collector
    from automation.health import init_health
    init_health(app)

    # 5. Initialise Automation Builder rule engine
    from automation.builder import init_builder
    init_builder(app)

    # 6. Register the n8n blueprint
    from blueprints.n8n import n8n_bp
    app.register_blueprint(n8n_bp)

    logger.info("Automation subsystem initialised (n8n_enabled=%s)", app.config["N8N_ENABLED"])
