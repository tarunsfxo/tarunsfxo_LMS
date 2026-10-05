"""add automation tables

Revision ID: 21c97ed9f68f
Revises: None
Create Date: 2026-07-17 00:16:37.773903

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21c97ed9f68f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. n8n_workflow_logs
    op.create_table('n8n_workflow_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('response_json', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_n8n_workflow_logs_workflow_name', 'n8n_workflow_logs', ['workflow_name'], unique=False)
    op.create_index('ix_n8n_workflow_logs_created_at', 'n8n_workflow_logs', ['created_at'], unique=False)

    # 2. n8n_workflow_configs
    op.create_table('n8n_workflow_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_name', sa.String(length=100), nullable=False),
        sa.Column('webhook_url', sa.String(length=500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('cron_expression', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=300), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_name')
    )

    # 3. automation_events
    op.create_table('automation_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=30), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automation_events_user_id', 'automation_events', ['user_id'], unique=False)
    op.create_index('ix_automation_events_event_type', 'automation_events', ['event_type'], unique=False)
    op.create_index('ix_automation_events_created_at', 'automation_events', ['created_at'], unique=False)

    # 4. feedback_analyses
    op.create_table('feedback_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_feedback_analyses_user_id', 'feedback_analyses', ['user_id'], unique=False)
    op.create_index('ix_feedback_analyses_course_id', 'feedback_analyses', ['course_id'], unique=False)

    # 5. weekly_reports
    op.create_table('weekly_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=True),
        sa.Column('pdf_url', sa.String(length=500), nullable=True),
        sa.Column('learning_hours', sa.Float(), nullable=True),
        sa.Column('quizzes_taken', sa.Integer(), nullable=True),
        sa.Column('avg_quiz_score', sa.Float(), nullable=True),
        sa.Column('bites_completed', sa.Integer(), nullable=True),
        sa.Column('coding_solved', sa.Integer(), nullable=True),
        sa.Column('xp_earned', sa.Integer(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'week_start', name='uix_user_week_report')
    )
    op.create_index('ix_weekly_reports_user_id', 'weekly_reports', ['user_id'], unique=False)

    # 6. career_recommendations
    op.create_table('career_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resume_url', sa.String(length=500), nullable=True),
        sa.Column('recommendations_json', sa.Text(), nullable=True),
        sa.Column('skills_json', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_career_recommendations_user_id', 'career_recommendations', ['user_id'], unique=False)

    # 7. ai_mentor_conversations
    op.create_table('ai_mentor_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=30), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_mentor_conversations_user_id', 'ai_mentor_conversations', ['user_id'], unique=False)
    op.create_index('ix_ai_mentor_conversations_created_at', 'ai_mentor_conversations', ['created_at'], unique=False)

    # 8. study_plans
    op.create_table('study_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('exam_name', sa.String(length=200), nullable=False),
        sa.Column('exam_date', sa.Date(), nullable=False),
        sa.Column('target_course_ids_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('total_tasks', sa.Integer(), nullable=True),
        sa.Column('completed_tasks', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_study_plans_user_id', 'study_plans', ['user_id'], unique=False)

    # 9. study_plan_days
    op.create_table('study_plan_days',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('tasks_json', sa.Text(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('was_redistributed', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['study_plans.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'date', name='uix_plan_day')
    )
    op.create_index('ix_study_plan_days_plan_id', 'study_plan_days', ['plan_id'], unique=False)

    # 10. security_alerts
    op.create_table('security_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_security_alerts_user_id', 'security_alerts', ['user_id'], unique=False)
    op.create_index('ix_security_alerts_created_at', 'security_alerts', ['created_at'], unique=False)

    # 11. health_metrics
    op.create_table('health_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('avg_latency_ms', sa.Float(), nullable=True),
        sa.Column('total_calls_today', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('component')
    )

    # 12. automation_analytics
    op.create_table('automation_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automation_analytics_metric_name', 'automation_analytics', ['metric_name'], unique=False)
    op.create_index('ix_automation_analytics_recorded_at', 'automation_analytics', ['recorded_at'], unique=False)

    # 13. automation_rules
    op.create_table('automation_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('trigger_event', sa.String(length=80), nullable=False),
        sa.Column('conditions_json', sa.Text(), nullable=True),
        sa.Column('actions_json', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=True),
        sa.Column('last_executed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automation_rules_trigger_event', 'automation_rules', ['trigger_event'], unique=False)

    # 14. learning_schedules
    op.create_table('learning_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('bite_id', sa.Integer(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['bite_id'], ['bites.id'], ),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_schedules_user_id', 'learning_schedules', ['user_id'], unique=False)

    # 15. Create index in quiz_attempts
    try:
        with op.batch_alter_table('quiz_attempts', schema=None) as batch_op:
            batch_op.create_index('ix_quiz_attempts_user_course', ['user_id', 'course_id'], unique=False)
    except Exception:
        pass


def downgrade():
    try:
        with op.batch_alter_table('quiz_attempts', schema=None) as batch_op:
            batch_op.drop_index('ix_quiz_attempts_user_course')
    except Exception:
        pass

    op.drop_table('learning_schedules')
    op.drop_table('automation_rules')
    op.drop_table('automation_analytics')
    op.drop_table('health_metrics')
    op.drop_table('security_alerts')
    op.drop_table('study_plan_days')
    op.drop_table('study_plans')
    op.drop_table('ai_mentor_conversations')
    op.drop_table('career_recommendations')
    op.drop_table('weekly_reports')
    op.drop_table('feedback_analyses')
    op.drop_table('automation_events')
    op.drop_table('n8n_workflow_configs')
    op.drop_table('n8n_workflow_logs')
