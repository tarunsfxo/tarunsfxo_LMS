"""
automation.services.study_planner — AI Study Planner Service
==============================================================
Runs directly in Flask.  n8n only sends daily cron reminders.

Workflow:
  Student sets exam date + selects courses →
  Analyze incomplete content + quiz scores →
  Generate daily timetable →
  n8n cron sends daily reminder →
  If student misses a day → redistribute →
  Weekly review + adjustment
"""

import json
import logging
import math
from datetime import datetime, date, timedelta

from extensions import db

logger = logging.getLogger("automation.services.study_planner")


def create_plan(user, exam_name: str, exam_date: date, course_ids: list) -> dict:
    """Create a study plan for an upcoming exam.

    Returns the created plan as a dict.
    """
    from automation.models import StudyPlan, StudyPlanDay
    from models import Course, Bite, Progress

    # Calculate available study days
    today = date.today()
    if exam_date <= today:
        return {"error": "Exam date must be in the future."}

    days_available = (exam_date - today).days
    if days_available < 1:
        return {"error": "Need at least 1 day to create a plan."}

    # Gather incomplete content from target courses
    tasks = []
    for cid in course_ids:
        course = Course.query.get(cid)
        if not course:
            continue

        # Add course video lesson as a task
        tasks.append({
            "type": "course",
            "id": course.id,
            "title": f"Watch: {course.title}",
            "estimated_minutes": 30,
            "difficulty_weight": _difficulty_weight(course.difficulty),
        })

        # Add incomplete bites in the same category
        if course.category_id:
            bites = Bite.query.filter_by(category_id=course.category_id).all()
            completed_ids = set(
                p.bite_id for p in Progress.query.filter_by(
                    user_id=user.id, completed=True
                ).all()
            )

            for bite in bites:
                if bite.id not in completed_ids:
                    tasks.append({
                        "type": "bite",
                        "id": bite.id,
                        "title": f"Lesson: {bite.title}",
                        "estimated_minutes": bite.duration_minutes or 5,
                        "difficulty_weight": _difficulty_weight(bite.difficulty),
                    })

    if not tasks:
        return {"error": "No pending tasks found for selected courses."}

    # Sort tasks: easier first, harder later (progressive difficulty)
    tasks.sort(key=lambda t: t["difficulty_weight"])

    # Distribute tasks across days (roughly equal time per day)
    total_minutes = sum(t["estimated_minutes"] for t in tasks)
    minutes_per_day = max(15, math.ceil(total_minutes / days_available))

    day_plans = []
    task_idx = 0
    for day_offset in range(days_available):
        plan_date = today + timedelta(days=day_offset + 1)
        day_tasks = []
        day_minutes = 0

        while task_idx < len(tasks) and day_minutes < minutes_per_day:
            task = tasks[task_idx]
            day_tasks.append(task)
            day_minutes += task["estimated_minutes"]
            task_idx += 1

        if day_tasks:
            day_plans.append({
                "date": plan_date,
                "tasks": day_tasks,
            })

    # Save to database
    plan = StudyPlan(
        user_id=user.id,
        exam_name=exam_name,
        exam_date=exam_date,
        target_course_ids_json=json.dumps(course_ids),
        status="active",
        total_tasks=len(tasks),
        completed_tasks=0,
    )
    db.session.add(plan)
    db.session.flush()

    for dp in day_plans:
        plan_day = StudyPlanDay(
            plan_id=plan.id,
            date=dp["date"],
            tasks_json=json.dumps(dp["tasks"], default=str),
            completed=False,
        )
        db.session.add(plan_day)

    db.session.commit()

    # Fire background event
    try:
        from automation.trigger import fire
        fire("study_plan_created", user_id=user.id, plan_id=plan.id, exam_name=exam_name)
    except Exception:
        pass

    return {
        "plan_id": plan.id,
        "exam_name": exam_name,
        "exam_date": exam_date.isoformat(),
        "total_tasks": len(tasks),
        "total_days": len(day_plans),
        "minutes_per_day": minutes_per_day,
    }


def get_today_tasks(user) -> dict:
    """Get today's study plan tasks for the user."""
    from automation.models import StudyPlan, StudyPlanDay

    today = date.today()

    active_plans = StudyPlan.query.filter_by(
        user_id=user.id, status="active"
    ).all()

    results = []
    for plan in active_plans:
        day = StudyPlanDay.query.filter_by(
            plan_id=plan.id, date=today
        ).first()

        if day:
            tasks = json.loads(day.tasks_json) if day.tasks_json else []
            results.append({
                "plan_id": plan.id,
                "exam_name": plan.exam_name,
                "exam_date": plan.exam_date.isoformat(),
                "days_remaining": (plan.exam_date - today).days,
                "today_tasks": tasks,
                "today_completed": day.completed,
                "overall_progress": _calc_progress(plan),
            })

    return {"plans": results, "date": today.isoformat()}


def mark_day_complete(plan_day_id: int, user_id: int) -> bool:
    """Mark a study plan day as completed."""
    from automation.models import StudyPlanDay, StudyPlan

    day = StudyPlanDay.query.get(plan_day_id)
    if not day:
        return False

    plan = StudyPlan.query.get(day.plan_id)
    if not plan or plan.user_id != user_id:
        return False

    day.completed = True
    plan.completed_tasks = StudyPlanDay.query.filter_by(
        plan_id=plan.id, completed=True
    ).count() + 1

    # Check if all days are done
    total_days = StudyPlanDay.query.filter_by(plan_id=plan.id).count()
    if plan.completed_tasks >= total_days:
        plan.status = "completed"

    db.session.commit()
    return True


def adjust_plan(plan_id: int, user_id: int) -> dict:
    """Redistribute missed day tasks across remaining days."""
    from automation.models import StudyPlan, StudyPlanDay

    plan = StudyPlan.query.get(plan_id)
    if not plan or plan.user_id != user_id or plan.status != "active":
        return {"error": "Plan not found or not active."}

    today = date.today()

    # Find missed (past, incomplete) days
    missed_days = StudyPlanDay.query.filter(
        StudyPlanDay.plan_id == plan_id,
        StudyPlanDay.date < today,
        StudyPlanDay.completed == False,
    ).all()

    if not missed_days:
        return {"message": "No missed days to redistribute."}

    # Collect all missed tasks
    missed_tasks = []
    for md in missed_days:
        tasks = json.loads(md.tasks_json) if md.tasks_json else []
        missed_tasks.extend(tasks)
        md.was_redistributed = True

    # Find remaining future days
    future_days = StudyPlanDay.query.filter(
        StudyPlanDay.plan_id == plan_id,
        StudyPlanDay.date >= today,
        StudyPlanDay.completed == False,
    ).order_by(StudyPlanDay.date.asc()).all()

    if not future_days:
        return {"error": "No remaining days to redistribute to."}

    # Distribute missed tasks evenly across future days
    tasks_per_day = math.ceil(len(missed_tasks) / len(future_days))
    idx = 0
    for fd in future_days:
        existing = json.loads(fd.tasks_json) if fd.tasks_json else []
        added = missed_tasks[idx:idx + tasks_per_day]
        existing.extend(added)
        fd.tasks_json = json.dumps(existing, default=str)
        fd.was_redistributed = True
        idx += tasks_per_day

    db.session.commit()

    return {
        "redistributed_tasks": len(missed_tasks),
        "across_days": len(future_days),
    }


def get_user_plans(user_id: int) -> list:
    """Get all study plans for a user."""
    from automation.models import StudyPlan

    plans = StudyPlan.query.filter_by(user_id=user_id).order_by(
        StudyPlan.created_at.desc()
    ).all()

    return [
        {
            "id": p.id,
            "exam_name": p.exam_name,
            "exam_date": p.exam_date.isoformat(),
            "status": p.status,
            "total_tasks": p.total_tasks,
            "completed_tasks": p.completed_tasks,
            "progress": _calc_progress(p),
            "created_at": p.created_at.isoformat(),
        }
        for p in plans
    ]


def get_plan_details(plan_id: int, user_id: int) -> dict:
    """Get detailed plan with all days."""
    from automation.models import StudyPlan, StudyPlanDay

    plan = StudyPlan.query.get(plan_id)
    if not plan or plan.user_id != user_id:
        return None

    days = StudyPlanDay.query.filter_by(plan_id=plan_id).order_by(
        StudyPlanDay.date.asc()
    ).all()

    return {
        "id": plan.id,
        "exam_name": plan.exam_name,
        "exam_date": plan.exam_date.isoformat(),
        "status": plan.status,
        "total_tasks": plan.total_tasks,
        "completed_tasks": plan.completed_tasks,
        "progress": _calc_progress(plan),
        "days": [
            {
                "id": d.id,
                "date": d.date.isoformat(),
                "tasks": json.loads(d.tasks_json) if d.tasks_json else [],
                "completed": d.completed,
                "was_redistributed": d.was_redistributed,
            }
            for d in days
        ],
    }


# ── Private helpers ─────────────────────────────────────────────


def _difficulty_weight(difficulty: str) -> int:
    """Map difficulty to a sortable weight."""
    return {"beginner": 1, "intermediate": 2, "advanced": 3, "easy": 1, "medium": 2, "hard": 3}.get(
        (difficulty or "beginner").lower(), 1
    )


def _calc_progress(plan) -> int:
    """Calculate overall plan progress as percentage."""
    if plan.total_tasks <= 0:
        return 0
    return min(100, round((plan.completed_tasks / plan.total_tasks) * 100))
