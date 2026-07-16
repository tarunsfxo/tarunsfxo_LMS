# Tarunsfxo LMS — n8n Workflows Setup Guide

This directory contains the importable JSON configurations for all 16 automation workflows of the Tarunsfxo LMS.

## How to Import Workflows into n8n

1. Open your n8n dashboard (e.g., `http://localhost:5678`).
2. Click on **Workflows** in the left sidebar and select **Add Workflow** (or **+ New**).
3. In the top-right corner of the workflow editor, click the three dots (`...`) and select **Import from File**.
4. Upload the corresponding `.json` file from this directory.
5. Save the workflow.

## Environment Variables Configuration

Make sure your n8n instance has the following environment variables configured (e.g., in your Docker Compose or n8n cloud settings):

* `LMS_API_BASE_URL`: The URL of your running Flask LMS backend (e.g., `http://host.docker.internal:5000` or production domain).
* `N8N_WEBHOOK_SECRET`: The shared webhook authentication key (must match the secret in `.env.n8n` or Flask `config.py`).
* `OPENAI_API_KEY`: Required for workflows that use OpenAI nodes (AI Mentor, Progress Report Summary, Career Resume, Recommendations).
* `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`: For email dispatch nodes.

## List of Workflows

1. **`01_student_registration.json`** — Triggers welcome email, logs activity, and sets up student profile.
2. **`02_course_enrollment.json`** — Sends enrollment confirmations and updates course registers.
3. **`03_daily_learning_reminder.json`** — Scheduled daily reminder for inactive learners.
4. **`04_course_completion.json`** — Orchestrates certificate issuance, badge unlock, and course recommendation.
5. **`05_coding_practice.json`** — Tracks coding exercises, updates leaderboards, and requests code feedback.
6. **`06_ai_mentor_logging.json`** — Handles conversation logging and analytics for AI Mentor interactions.
7. **`07_weekly_progress_report.json`** — Scheduled weekly cron generating progress cards and email digests.
8. **`08_feedback_intelligence.json`** — Sentiment and category analyzer for student feedback.
9. **`09_instructor_automation.json`** — Course publication announcements and student notification dispatch.
10. **`10_achievement_system.json`** — Evaluates milestone completions and unlocks badges.
11. **`11_smart_admin_dashboard.json`** — Scheduled analytics aggregator providing midnight administrative reports.
12. **`12_security_monitoring.json`** — Alerts admin upon detecting anomalous actions (e.g., failed logins).
13. **`13_resume_career_assistant.json`** — Automated resume content formatter and career role advisor.
14. **`14_ai_learning_recommendations.json`** — Synthesizes next learning steps based on progress and score matrices.
15. **`15_analytics_engine.json`** — Real-time telemetry processing pipeline.
16. **`16_study_plan_reminders.json`** — Dispatches personalized study goals based on active student study plans.
