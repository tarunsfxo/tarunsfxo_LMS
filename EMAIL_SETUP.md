# Email Automation Setup Guide

This guide explains how to configure and deploy the n8n automated email notification system for Tarunsfxo LMS.

## 1. Configure Environment Variables
You must provide your SMTP credentials so n8n can send HTML emails on your behalf.
Open your `.env.n8n` file and populate the following values:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM="Tarunsfxo LMS <your_email@gmail.com>"
ADMIN_WEBHOOK_URL="https://discord.com/api/webhooks/your_channel_webhook"
```

*Note: If you use Gmail, you must generate an "App Password" rather than using your real account password.*

## 2. Import the Workflows into n8n
We have generated 10 robust workflows that include retry logic, error handling, and SMTP configuration.
1. Start n8n and open your dashboard.
2. Go to **Workflows**.
3. For each JSON file in the `n8n_workflows/email_notifications/` directory:
   - Click **Add Workflow** -> **Import from File**.
   - Select the JSON file.
   - Click the toggle switch in the top right corner to **Activate** it.

## 3. Configure the Internal Render Endpoint
The workflows rely on an internal Flask endpoint (`/api/internal/render-email`) to turn Jinja templates into raw HTML that n8n can send. Ensure your Docker network allows n8n to reach the Flask container (usually via `http://web:5000/api/internal/render-email`). 

If you are running everything locally on your host machine (without Docker), update the "Render HTML (Flask)" node in each workflow to point to `http://localhost:5000/api/internal/render-email`.

## 4. Setting up Cron Jobs (Weekly Reports & Inactive Users)
To automatically trigger the Weekly Report and Inactive User emails, add the following to your server's `crontab`:

```bash
# Run weekly reports every Sunday at 9 AM
0 9 * * 0 cd /path/to/lms && flask trigger-weekly-reports

# Run inactive user checks every day at 10 AM
0 10 * * * cd /path/to/lms && flask trigger-inactive-users
```

These commands will query the database and publish the events to the Redis queue, which n8n will immediately pick up and process.
