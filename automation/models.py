"""
automation.models — New database models for the automation subsystem
=====================================================================
These define **new tables only**.  Existing tables (users, courses, bites,
progress, etc.) are NEVER modified.

Tables created:
  • n8n_workflow_logs        — every workflow execution
  • n8n_workflow_configs     — workflow settings & webhook URLs
  • automation_events        — student + AI activity timeline
  • feedback_analyses        — sentiment analysis results (no duplicate feedback table)
  • weekly_reports           — slim: summary + pdf_url + generated_at
  • career_recommendations   — AI-generated career data
  • ai_mentor_conversations  — chat history with source tracking
  • study_plans              — AI Study Planner
  • study_plan_days          — daily items within a study plan
  • security_alerts          — security monitoring
  • health_metrics           — cached component health (no live polling)
  • automation_analytics     — pre-computed analytics snapshots
  • automation_rules         — Automation Builder IF/THEN rules
  • learning_schedules       — per-student schedule entries
"""

from datetime import datetime
from extensions import db


class N8NWorkflowLog(db.Model):
    """Logs every n8n workflow trigger and its outcome."""
    __tablename__ = "n8n_workflow_logs"

    id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="queued")  # queued/running/success/failed/retrying
    payload_json = db.Column(db.Text)
    response_json = db.Column(db.Text)
    execution_time_ms = db.Column(db.Integer)
    retry_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<N8NWorkflowLog {self.workflow_name} status={self.status}>"


class N8NWorkflowConfig(db.Model):
    """Stores configuration for each n8n workflow."""
    __tablename__ = "n8n_workflow_configs"

    id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(100), unique=True, nullable=False)
    webhook_url = db.Column(db.String(500))
    is_enabled = db.Column(db.Boolean, default=True)
    cron_expression = db.Column(db.String(50))  # for scheduled workflows
    description = db.Column(db.String(300))
    last_triggered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<N8NWorkflowConfig {self.workflow_name} enabled={self.is_enabled}>"


class AutomationEvent(db.Model):
    """Activity timeline entries — both student-facing and admin-facing."""
    __tablename__ = "automation_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    event_type = db.Column(db.String(80), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    detail = db.Column(db.Text)
    source = db.Column(db.String(30), default="flask")  # flask/n8n/openai/local_search
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("automation_events", lazy="dynamic"))

    def __repr__(self):
        return f"<AutomationEvent {self.event_type} user={self.user_id}>"


class FeedbackAnalysis(db.Model):
    """Sentiment analysis results — links to course, no duplicate feedback table."""
    __tablename__ = "feedback_analyses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), index=True)
    original_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars
    sentiment = db.Column(db.String(20))  # positive/neutral/negative
    category = db.Column(db.String(50))  # content/instructor/platform/other
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("feedback_analyses", lazy="dynamic"))
    course = db.relationship("Course", backref=db.backref("feedback_analyses", lazy="dynamic"))

    def __repr__(self):
        return f"<FeedbackAnalysis user={self.user_id} sentiment={self.sentiment}>"


class WeeklyReport(db.Model):
    """Slim weekly report — summary text + PDF URL only."""
    __tablename__ = "weekly_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    week_start = db.Column(db.Date, nullable=False)
    summary = db.Column(db.String(500))  # short text summary
    pdf_url = db.Column(db.String(500))
    learning_hours = db.Column(db.Float, default=0)
    quizzes_taken = db.Column(db.Integer, default=0)
    avg_quiz_score = db.Column(db.Float, default=0)
    bites_completed = db.Column(db.Integer, default=0)
    coding_solved = db.Column(db.Integer, default=0)
    xp_earned = db.Column(db.Integer, default=0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("weekly_reports", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("user_id", "week_start", name="uix_user_week_report"),
    )

    def __repr__(self):
        return f"<WeeklyReport user={self.user_id} week={self.week_start}>"


class CareerRecommendation(db.Model):
    """AI-generated career and resume data."""
    __tablename__ = "career_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    resume_url = db.Column(db.String(500))
    recommendations_json = db.Column(db.Text)  # JSON: roles, projects, certifications, interview_questions
    skills_json = db.Column(db.Text)  # JSON: extracted skills from completed courses
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("career_recommendations", lazy="dynamic"))

    def __repr__(self):
        return f"<CareerRecommendation user={self.user_id}>"


class AIMentorConversation(db.Model):
    """AI Mentor chat history with source tracking."""
    __tablename__ = "ai_mentor_conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(30), nullable=False)  # course_notes/cached_answer/quiz_notes/openai/fallback
    response_time_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("ai_mentor_conversations", lazy="dynamic"))

    def __repr__(self):
        return f"<AIMentorConversation user={self.user_id} source={self.source}>"


class StudyPlan(db.Model):
    """AI Study Planner — exam-targeted study plan."""
    __tablename__ = "study_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    exam_name = db.Column(db.String(200), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    target_course_ids_json = db.Column(db.Text)  # JSON array of course IDs
    status = db.Column(db.String(20), default="active")  # active/completed/paused
    total_tasks = db.Column(db.Integer, default=0)
    completed_tasks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("study_plans", lazy="dynamic"))
    days = db.relationship("StudyPlanDay", backref="plan", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StudyPlan user={self.user_id} exam={self.exam_name} status={self.status}>"


class StudyPlanDay(db.Model):
    """Individual day within a study plan."""
    __tablename__ = "study_plan_days"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("study_plans.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    tasks_json = db.Column(db.Text)  # JSON array: [{type, id, title, estimated_minutes}]
    completed = db.Column(db.Boolean, default=False)
    was_redistributed = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint("plan_id", "date", name="uix_plan_day"),
    )

    def __repr__(self):
        return f"<StudyPlanDay plan={self.plan_id} date={self.date} done={self.completed}>"


class SecurityAlert(db.Model):
    """Security monitoring alerts."""
    __tablename__ = "security_alerts"

    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # failed_login/suspicious_activity/api_abuse/spam/fake_account
    severity = db.Column(db.String(20), nullable=False, default="medium")  # low/medium/high/critical
    detail = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    ip_address = db.Column(db.String(50))
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("security_alerts", lazy="dynamic"))

    def __repr__(self):
        return f"<SecurityAlert {self.alert_type} severity={self.severity}>"


class HealthMetric(db.Model):
    """Cached health data — updated passively from real operations, not polled."""
    __tablename__ = "health_metrics"

    id = db.Column(db.Integer, primary_key=True)
    component = db.Column(db.String(30), unique=True, nullable=False)  # n8n/redis/openai/email
    status = db.Column(db.String(20), default="unknown")  # up/down/degraded/unknown
    last_success_at = db.Column(db.DateTime)
    last_failure_at = db.Column(db.DateTime)
    last_error = db.Column(db.Text)
    avg_latency_ms = db.Column(db.Float, default=0)
    total_calls_today = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<HealthMetric {self.component} status={self.status}>"


class AutomationAnalytics(db.Model):
    """Pre-computed analytics snapshots."""
    __tablename__ = "automation_analytics"

    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False, index=True)
    metric_value = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), default="daily")  # hourly/daily/weekly/monthly
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AutomationAnalytics {self.metric_name}={self.metric_value}>"


class AutomationRule(db.Model):
    """Automation Builder — IF/THEN rules created by admins."""
    __tablename__ = "automation_rules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    trigger_event = db.Column(db.String(80), nullable=False, index=True)
    conditions_json = db.Column(db.Text)  # JSON: [{field, operator, value}]
    actions_json = db.Column(db.Text)  # JSON: [{action, params}]
    is_enabled = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    execution_count = db.Column(db.Integer, default=0)
    last_executed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", backref=db.backref("automation_rules", lazy="dynamic"))

    def __repr__(self):
        return f"<AutomationRule '{self.name}' trigger={self.trigger_event}>"


class LearningSchedule(db.Model):
    """Per-student learning schedule entries."""
    __tablename__ = "learning_schedules"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    scheduled_date = db.Column(db.Date, nullable=False)
    bite_id = db.Column(db.Integer, db.ForeignKey("bites.id"))
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    status = db.Column(db.String(20), default="pending")  # pending/completed/skipped
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("learning_schedules", lazy="dynamic"))

    def __repr__(self):
        return f"<LearningSchedule user={self.user_id} date={self.scheduled_date}>"
