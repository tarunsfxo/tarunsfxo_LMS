"""
automation.services.email — Pluggable Email Service
=====================================================
Supports console (dev), SMTP, and SendGrid providers.
Uses Jinja2 email templates.  Updates health metrics passively.
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app, render_template

logger = logging.getLogger("automation.services.email")


def send_email(to: str, subject: str, template: str = None, html_body: str = None, **template_vars) -> bool:
    """Send an email using the configured provider.

    Parameters
    ----------
    to : str
        Recipient email address.
    subject : str
        Email subject line.
    template : str, optional
        Template name (e.g. ``"emails/welcome.html"``).
    html_body : str, optional
        Raw HTML body (used if no template provided).
    **template_vars
        Variables to pass to the Jinja2 template.

    Returns
    -------
    bool
        True if the email was sent successfully.
    """
    try:
        # Render template if provided
        if template:
            try:
                from flask import has_request_context
                if not has_request_context():
                    base_url = current_app.config.get("APP_URL", "https://tarunsfxo-lms.onrender.com")
                    with current_app.test_request_context(base_url=base_url):
                        html_body = render_template(template, **template_vars)
                else:
                    html_body = render_template(template, **template_vars)
            except Exception as exc:
                logger.warning("Template '%s' render failed (%s), using raw body", template, exc)

        if not html_body:
            html_body = f"<p>{subject}</p>"

        provider = current_app.config.get("EMAIL_PROVIDER", "console")
        smtp_user = current_app.config.get("SMTP_USER", "")
        smtp_password = current_app.config.get("SMTP_PASSWORD", "")

        # If SMTP credentials exist, automatically dispatch via SMTP
        if smtp_user and smtp_password and provider != "sendgrid":
            provider = "smtp"

        if provider == "smtp":
            success = _send_smtp(to, subject, html_body)
        elif provider == "sendgrid":
            success = _send_sendgrid(to, subject, html_body)
        else:
            success = _send_console(to, subject, html_body)

        # Update health metrics passively
        try:
            from automation.health import update_health
            update_health("email", success=success)
        except Exception:
            pass

        return success

    except Exception as exc:
        logger.exception("Email send failed: to=%s, subject=%s", to, subject)
        try:
            from automation.health import update_health
            update_health("email", success=False, error=str(exc))
        except Exception:
            pass
        return False


# ── Providers ───────────────────────────────────────────────────


def _send_console(to: str, subject: str, html_body: str) -> bool:
    """Dev mode: log email to console instead of sending."""
    logger.warning(
        "\n"
        "╔══════════════════════════════════════════════════╗\n"
        "║            📧 EMAIL (Console Mode)              ║\n"
        "╠══════════════════════════════════════════════════╣\n"
        "║ To:      %-40s ║\n"
        "║ Subject: %-40s ║\n"
        "╠══════════════════════════════════════════════════╣\n"
        "║ Body: (HTML rendered in production)              ║\n"
        "║ %s\n"
        "╚══════════════════════════════════════════════════╝",
        to, subject[:40], html_body[:200],
    )
    return True


def _send_smtp(to: str, subject: str, html_body: str) -> bool:
    """Send email via SMTP."""
    host = current_app.config.get("SMTP_HOST", "smtp.gmail.com")
    port = int(current_app.config.get("SMTP_PORT", 587))
    user = current_app.config.get("SMTP_USER", "")
    password = current_app.config.get("SMTP_PASSWORD", "")
    from_addr = current_app.config.get("SMTP_FROM", user)

    if not user or not password:
        logger.warning("SMTP credentials not configured (user=%r, has_password=%s), falling back to console", user, bool(password))
        return _send_console(to, subject, html_body)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Tarunsfxo LMS <{from_addr}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        logger.info("Connecting to SMTP %s:%d as %s to send '%s' to %s", host, port, user, subject, to)
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(from_addr, [to], msg.as_string())
        logger.info("SMTP email successfully delivered to %s: %s", to, subject)
        return True
    except Exception as exc:
        logger.exception("SMTP send failed to %s: %s", to, exc)
        return False


def _send_sendgrid(to: str, subject: str, html_body: str) -> bool:
    """Send email via SendGrid API."""
    api_key = current_app.config.get("SENDGRID_API_KEY", "")
    from_email = current_app.config.get("SENDGRID_FROM", "noreply@tarunsfxo-lms.com")

    if not api_key:
        logger.warning("SendGrid API key not configured, falling back to console")
        return _send_console(to, subject, html_body)

    try:
        import httpx

        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": from_email, "name": "Tarunsfxo LMS"},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_body}],
        }

        with httpx.Client() as client:
            response = client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )

        if response.status_code < 300:
            logger.info("SendGrid email sent to %s: %s", to, subject)
            return True
        else:
            logger.warning("SendGrid failed: %s", response.text)
            return False

    except Exception:
        logger.exception("SendGrid send failed")
        return False
