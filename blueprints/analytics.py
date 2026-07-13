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

