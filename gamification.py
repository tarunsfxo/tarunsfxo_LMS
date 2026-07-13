from extensions import db
from models import User, XPLog, UserBadge, UserAchievement, UserNotification, Progress, CourseProgress, QuizAttempt, CodingSubmission
from datetime import datetime, date

def award_xp(user, amount, reason):
    """Securely awards XP on the server, logs transaction, handles level-up notifications."""
    if amount <= 0:
        return False
        
    old_level = user.level()
    user.xp += amount
    
    # Log the transaction
    log = XPLog(user_id=user.id, amount=amount, reason=reason)
    db.session.add(log)
    
    # Check level up
    new_level = user.level()
    if new_level > old_level:
        # Create Level Up Notification
        notif = UserNotification(
            user_id=user.id,
            title="Level Up! 🏆",
            message=f"Congratulations! You leveled up from Level {old_level} to Level {new_level}!",
            type="level_up"
        )
        db.session.add(notif)
        
        # Auto-unlock level milestones badges
        if new_level >= 2:
            unlock_badge(user, "Level 2 Explorer", "🎯", "Reached Level 2 of progression.")
        if new_level >= 5:
            unlock_badge(user, "Level 5 Master", "👑", "Reached Level 5 of progression.")
            
    # Trigger checks for other badges/achievements
    check_badge_milestones(user)
    check_achievement_milestones(user)
    
    db.session.commit()
    return True

def unlock_badge(user, badge_name, icon, description):
    """Unlocks a badge for a user if they don't already have it."""
    existing = UserBadge.query.filter_by(user_id=user.id, badge_name=badge_name).first()
    if not existing:
        badge = UserBadge(
            user_id=user.id,
            badge_name=badge_name,
            badge_icon=icon,
            badge_description=description
        )
        db.session.add(badge)
        
        # Create Badge Notification
        notif = UserNotification(
            user_id=user.id,
            title="New Badge Unlocked! 🏅",
            message=f"You earned the '{badge_name}' badge!",
            type="badge"
        )
        db.session.add(notif)
        return True
    return False

def unlock_achievement(user, achievement_name, description):
    """Unlocks an achievement for a user if they don't already have it."""
    existing = UserAchievement.query.filter_by(user_id=user.id, achievement_name=achievement_name).first()
    if not existing:
        achievement = UserAchievement(
            user_id=user.id,
            achievement_name=achievement_name,
            achievement_description=description
        )
        db.session.add(achievement)
        
        # Create Achievement Notification
        notif = UserNotification(
            user_id=user.id,
            title="Achievement Unlocked! 🌟",
            message=f"Unlocked: {achievement_name}",
            type="achievement"
        )
        db.session.add(notif)
        return True
    return False

def check_badge_milestones(user):
    """Checks for automatic badge unlocks based on user statistics."""
    # 1. Lesson Milestones
    completed_lessons = Progress.query.filter_by(user_id=user.id, completed=True).count()
    if completed_lessons >= 1:
        unlock_badge(user, "First Lesson", "📖", "Completed your very first lesson.")
    if completed_lessons >= 10:
        unlock_badge(user, "Learning Enthusiast", "📚", "Completed 10 lessons.")

    # 2. XP Milestones
    if user.xp >= 1000:
        unlock_badge(user, "1,000 XP Club", "✨", "Earned a total of 1,000 XP.")
    if user.xp >= 5000:
        unlock_badge(user, "5,000 XP Legend", "🔮", "Earned a total of 5,000 XP.")

    # 3. Streak Milestones
    if user.streak_count >= 7:
        unlock_badge(user, "7-Day Streak", "🔥", "Maintained a consecutive 7-day learning streak.")
    if user.streak_count >= 30:
        unlock_badge(user, "30-Day Streak", "🌋", "Maintained a consecutive 30-day learning streak.")

    # 4. Quiz Milestones
    quiz_attempts = QuizAttempt.query.filter_by(user_id=user.id).count()
    if quiz_attempts >= 5:
        unlock_badge(user, "Quiz Master", "📝", "Completed at least 5 quiz attempts.")

    # 5. Coding Milestones
    accepted_coding = CodingSubmission.query.filter_by(user_id=user.id, verdict="Accepted").count()
    if accepted_coding >= 1:
        unlock_badge(user, "Coding Novice", "👾", "Solved your first coding problem.")
    if accepted_coding >= 10:
        unlock_badge(user, "Coding Expert", "⚡", "Solved 10 coding problems.")

def check_achievement_milestones(user):
    """Checks for automatic achievement unlocks."""
    completed_lessons = Progress.query.filter_by(user_id=user.id, completed=True).count()
    completed_courses = CourseProgress.query.filter_by(user_id=user.id, completed=True).count()
    accepted_coding = CodingSubmission.query.filter_by(user_id=user.id, verdict="Accepted").count()
    
    if completed_lessons >= 50:
        unlock_achievement(user, "Micro-Learning Champ", "Completed 50 lessons/bites across the platform.")
    if completed_courses >= 1:
        unlock_achievement(user, "First Graduate", "Successfully completed your first full video course.")
    if accepted_coding >= 25:
        unlock_achievement(user, "Algorithm Solver", "Solved 25 coding challenges on the workspace.")
    if user.streak_count >= 30:
        unlock_achievement(user, "Consistency King", "Kept your learning streak active for 30 consecutive days.")
