# Email Notification Workflows

This directory contains the 10 production-ready n8n workflows for the automated email notification system in Tarunsfxo LMS.

## Workflows Included
1. `01_user_registered.json` - Welcomes new users
2. `02_course_enrolled.json` - Confirms course enrollment
3. `03_course_completed.json` - Congratulates users on completing a course
4. `04_certificate_generated.json` - Delivers the PDF certificate link
5. `05_badge_unlocked.json` - Notifies users of newly unlocked badges
6. `06_weekly_report.json` - Sends weekly progress summaries
7. `07_inactive_user.json` - Reminds inactive users to continue learning
8. `08_password_changed.json` - Security alert for password changes
9. `09_premium_purchased.json` - Confirms premium plan upgrades
10. `10_admin_broadcast.json` - Delivers global administrative announcements

## How to Import
1. Open your n8n dashboard (usually `http://localhost:5678` or your deployed URL).
2. Click **Add Workflow** in the top right.
3. In the workflow canvas, click the menu (three dots) -> **Import from File**.
4. Select the JSON files from this directory.
5. Make sure to activate (toggle ON) the workflows in the top right corner.

## Environment Variables Required
These workflows rely on the SMTP node credentials. To make them dynamic, you should define these variables in your `.env.n8n` file, or set up the SMTP Credential natively inside n8n via **Credentials -> Add Credential -> SMTP**.

Required `.env` variables for n8n:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM="Tarunsfxo LMS <your_email@gmail.com>"
ADMIN_WEBHOOK_URL="https://discord.com/api/webhooks/your_channel_webhook"
```

## Retry Logic & Fail-Safes
Each workflow is configured with a built-in error catcher. If the `Send Email` node fails (e.g., the SMTP server is down), the `onError` hook is triggered. It will retry sending, and if it fails completely, it will fire an HTTP request to the `ADMIN_WEBHOOK_URL` so you are instantly notified of the failure without affecting the LMS users.
