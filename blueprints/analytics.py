from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db, csrf
from models import Progress, QuizAttempt, Bite, Category, UserSession

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def analytics_page():
    return render_template("analytics.html")


@analytics_bp.route("/api/analytics/category-progress")
@login_required
def category_progress():
    categories = Category.query.all()
    labels, completed_counts, total_counts = [], [], []

    for cat in categories:
        total = Bite.query.filter_by(category_id=cat.id).count()
        completed = (
            Progress.query.join(Bite, Progress.bite_id == Bite.id)
            .filter(Progress.user_id == current_user.id, Progress.completed == True, Bite.category_id == cat.id)
            .count()
        )
        if total > 0:
            labels.append(cat.name)
            completed_counts.append(completed)
            total_counts.append(total)

    return jsonify({"labels": labels, "completed": completed_counts, "total": total_counts})


@analytics_bp.route("/api/analytics/weekly-activity")
@login_required
def weekly_activity():
    today = datetime.utcnow().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels = [d.strftime("%a") for d in days]
    counts = []

    for d in days:
        start = datetime.combine(d, datetime.min.time())
        end = start + timedelta(days=1)
        count = Progress.query.filter(
            Progress.user_id == current_user.id,
            Progress.completed == True,
            Progress.completed_at >= start,
            Progress.completed_at < end,
        ).count()
        counts.append(count)

    return jsonify({"labels": labels, "counts": counts})


@analytics_bp.route("/api/analytics/quiz-performance")
@login_required
def quiz_performance():
    attempts = (
        QuizAttempt.query.filter_by(user_id=current_user.id)
        .order_by(QuizAttempt.attempted_at.asc())
        .limit(15)
        .all()
    )
    labels = [a.attempted_at.strftime("%b %d") for a in attempts]
    scores = [round((a.score / a.total_questions) * 100) if a.total_questions else 0 for a in attempts]
    return jsonify({"labels": labels, "scores": scores})


@analytics_bp.route("/api/analytics/difficulty-breakdown")
@login_required
def difficulty_breakdown():
    completed_ids = current_user.completed_bite_ids()
    counts = {"beginner": 0, "intermediate": 0, "advanced": 0}
    if completed_ids:
        bites = Bite.query.filter(Bite.id.in_(completed_ids)).all()
        for b in bites:
            counts[b.difficulty] = counts.get(b.difficulty, 0) + 1
    return jsonify({"labels": list(counts.keys()), "counts": list(counts.values())})


@analytics_bp.route("/api/analytics/session/start", methods=["POST"])
@csrf.exempt
@login_required
def session_start():
    data = request.get_json() or {}
    activity = data.get("activity") or "Browsing"
    
    session_obj = UserSession(
        user_id=current_user.id,
        activity=activity,
        enter_time=datetime.utcnow()
    )
    db.session.add(session_obj)
    db.session.commit()
    
    return jsonify({"success": True, "session_id": session_obj.id})


@analytics_bp.route("/api/analytics/session/end", methods=["POST"])
@csrf.exempt
@login_required
def session_end():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    
    if session_id:
        session_obj = UserSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if session_obj:
            session_obj.leave_time = datetime.utcnow()
            db.session.commit()
            return jsonify({"success": True})
            
    return jsonify({"success": False}), 400


@analytics_bp.route("/api/analytics/gamification/dashboard")
@login_required
def gamification_dashboard():
    from models import UserBadge, UserAchievement, UserNotification
    
    badges_count = current_user.badges.count()
    achievements_count = current_user.achievements.count()
    
    unread_notifs = current_user.notifications.filter_by(is_read=False).order_by(UserNotification.created_at.desc()).all()
    notifs_data = [{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type
    } for n in unread_notifs]
    
    return jsonify({
        "xp": current_user.xp,
        "level": current_user.level(),
        "xp_to_next_level": current_user.xp_to_next_level(),
        "streak": current_user.streak_count,
        "badges_count": badges_count,
        "achievements_count": achievements_count,
        "notifications": notifs_data
    })


@analytics_bp.route("/api/analytics/gamification/badges")
@login_required
def gamification_badges():
    from models import UserBadge
    badges = current_user.badges.order_by(UserBadge.earned_at.desc()).all()
    return jsonify([{
        "name": b.badge_name,
        "icon": b.badge_icon,
        "description": b.badge_description,
        "earned_at": b.earned_at.strftime('%b %d, %Y')
    } for b in badges])


@analytics_bp.route("/api/analytics/gamification/achievements")
@login_required
def gamification_achievements():
    from models import UserAchievement
    achievements = current_user.achievements.order_by(UserAchievement.earned_at.desc()).all()
    return jsonify([{
        "name": a.achievement_name,
        "description": a.achievement_description,
        "earned_at": a.earned_at.strftime('%b %d, %Y')
    } for a in achievements])


@analytics_bp.route("/api/analytics/gamification/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def gamification_mark_notification_read(notif_id):
    from models import UserNotification
    notif = UserNotification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({"success": True})


@analytics_bp.route("/api/analytics/ai-insights", methods=["GET"])
@login_required
def get_ai_insights():
    """Calculates consistency score, focus score, productivity score, and estimated completion date."""
    from models import Progress, UserSession, Bite
    from extensions import db
    from datetime import datetime, timedelta
    
    # 1. Consistency (Active days in the last 7 days)
    today = datetime.utcnow().date()
    active_days = 0
    for i in range(7):
        day = today - timedelta(days=i)
        session_exists = UserSession.query.filter_by(user_id=current_user.id).filter(
            db.func.date(UserSession.enter_time) == day
        ).first()
        if session_exists:
            active_days += 1
    consistency_score = int((active_days / 7) * 100)
    
    # 2. Focus Score (Average session duration in minutes, capped at 100)
    sessions = UserSession.query.filter_by(user_id=current_user.id).all()
    total_duration = 0
    valid_sessions = 0
    for s in sessions:
        if s.exit_time:
            dur = (s.exit_time - s.enter_time).total_seconds() / 60
            if dur > 0:
                total_duration += dur
                valid_sessions += 1
    avg_duration = (total_duration / valid_sessions) if valid_sessions else 15
    focus_score = min(100, int(avg_duration * 5)) # scale to make it look like a score
    
    # 3. Productivity Score (XP divided by estimated study hours)
    study_hours = max(0.5, total_duration / 60)
    productivity_score = min(100, int(current_user.xp / study_hours))
    
    # 4. Predicted Completion Date
    total_bites = Bite.query.count() or 1
    completed_bites = Progress.query.filter_by(user_id=current_user.id, completed=True).count()
    remaining = total_bites - completed_bites
    
    completion_rate_per_day = completed_bites / max(1, (datetime.utcnow() - current_user.created_at).days)
    if completion_rate_per_day > 0:
        days_to_complete = remaining / completion_rate_per_day
    else:
        days_to_complete = remaining * 2  # assume 2 days per bite if no progress rate
        
    est_date = datetime.utcnow() + timedelta(days=days_to_complete)
    
    return jsonify({
        "consistency_score": consistency_score,
        "focus_score": focus_score,
        "productivity_score": productivity_score,
        "predicted_completion_date": est_date.strftime("%B %d, %Y"),
        "completed_lessons": completed_bites,
        "total_lessons": total_bites
    })

