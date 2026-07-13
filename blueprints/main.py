from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_required, current_user
from extensions import db, csrf
from models import Bite, Category, Progress, QuizQuestion, QuizAttempt, User, XPLog, Course, CourseProgress
from recommend import recommend_bites
from config import Config

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    categories = Category.query.all()
    total_bites = Bite.query.count()
    total_users = User.query.count()
    featured = Bite.query.order_by(Bite.order_index.asc()).limit(6).all()
    return render_template(
        "index.html",
        categories=categories,
        total_bites=total_bites,
        total_users=total_users,
        featured=featured,
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    completed_ids = current_user.completed_bite_ids()
    recommendations = recommend_bites(current_user, limit=4, completed_ids=completed_ids)

    # Fetch recent quiz attempts with bite info
    recent_attempts = (
        db.session.query(QuizAttempt, Bite)
        .join(Bite, QuizAttempt.bite_id == Bite.id)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(5)
        .all()
    )

    total_bites = Bite.query.count()
    progress_pct = round((len(completed_ids) / total_bites) * 100) if total_bites else 0

    # Build per-category progress
    categories = Category.query.all()
    cat_progress = []
    for cat in categories:
        cat_bites = cat.bites.all()
        cat_total = len(cat_bites)
        if cat_total == 0:
            continue
        cat_done = sum(1 for b in cat_bites if b.id in completed_ids)
        cat_pct = round((cat_done / cat_total) * 100)
        cat_progress.append({
            "name": cat.name,
            "color": cat.color,
            "slug": cat.slug,
            "done": cat_done,
            "total": cat_total,
            "pct": cat_pct,
        })

    return render_template(
        "dashboard.html",
        completed_count=len(completed_ids),
        total_bites=total_bites,
        progress_pct=progress_pct,
        recommendations=recommendations,
        recent_attempts=recent_attempts,
        cat_progress=cat_progress,
    )


@main_bp.route("/bites")
def bites_list():
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("category")
    difficulty = request.args.get("difficulty")
    search = request.args.get("q", "").strip()

    query = Bite.query
    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(Bite.title.ilike(f"%{search}%"))

    pagination = query.order_by(Bite.order_index.asc()).paginate(
        page=page, per_page=Config.BITES_PER_PAGE, error_out=False
    )
    categories = Category.query.all()
    completed_ids = current_user.completed_bite_ids() if current_user.is_authenticated else []

    return render_template(
        "bites_list.html",
        pagination=pagination,
        bites=pagination.items,
        categories=categories,
        completed_ids=completed_ids,
        active_category=category_slug,
        active_difficulty=difficulty,
        search=search,
    )


@main_bp.route("/bites/<slug>")
def bite_detail(slug):
    bite = Bite.query.filter_by(slug=slug).first_or_404()

    if bite.is_premium and current_user.is_authenticated and current_user.plan == "free":
        flash("This bite is part of our Premium track. Please upgrade your plan.", "warning")
        return redirect(url_for("payment.pricing"))
    if bite.is_premium and not current_user.is_authenticated:
        flash("Please log in to access premium content.", "warning")
        return redirect(url_for("auth.login"))

    questions = bite.quiz_questions.all()
    is_completed = False
    if current_user.is_authenticated:
        progress = Progress.query.filter_by(user_id=current_user.id, bite_id=bite.id).first()
        is_completed = bool(progress and progress.completed)

    related = (
        Bite.query.filter(Bite.category_id == bite.category_id, Bite.id != bite.id)
        .limit(3)
        .all()
    )

    return render_template(
        "bite_detail.html", bite=bite, questions=questions, is_completed=is_completed, related=related
    )


@main_bp.route("/bites/<int:bite_id>/complete", methods=["POST"])
@csrf.exempt
@login_required
def complete_bite(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    progress = Progress.query.filter_by(user_id=current_user.id, bite_id=bite.id).first()

    if not progress:
        progress = Progress(user_id=current_user.id, bite_id=bite.id)
        db.session.add(progress)

    newly_completed = not progress.completed
    progress.completed = True
    progress.completed_at = datetime.utcnow()

    if newly_completed:
        from gamification import award_xp
        current_user.update_streak()
        award_xp(current_user, Config.XP_PER_BITE, "bite_complete")

    db.session.commit()

    # ── Auto-generate certificate if category is now fully complete ──
    certificate_issued = False
    cert_category = None
    if newly_completed and bite.category_id:
        from models import Certificate
        from certificates import generate_certificate_code, generate_certificate_pdf
        from flask import current_app

        category = bite.category
        total_in_cat = Bite.query.filter_by(category_id=category.id).count()
        completed_in_cat = (
            Progress.query.join(Bite, Progress.bite_id == Bite.id)
            .filter(
                Progress.user_id == current_user.id,
                Progress.completed == True,
                Bite.category_id == category.id,
            )
            .count()
        )

        already_issued = Certificate.query.filter_by(
            user_id=current_user.id, category_id=category.id
        ).first()

        if total_in_cat > 0 and completed_in_cat >= total_in_cat and not already_issued:
            cert_code = generate_certificate_code()
            _, filename = generate_certificate_pdf(
                current_app.config["CERTIFICATES_FOLDER"],
                current_user.username,
                category.name,
                cert_code,
                completed_in_cat,
            )
            cert = Certificate(
                user_id=current_user.id,
                category_id=category.id,
                cert_code=cert_code,
                file_path=filename,
            )
            db.session.add(cert)
            from gamification import award_xp
            award_xp(current_user, 25, "certificate_earned")
            db.session.commit()
            certificate_issued = True
            cert_category = category.name

    return jsonify(
        {
            "success": True,
            "xp": current_user.xp,
            "level": current_user.level(),
            "streak": current_user.streak_count,
            "certificate_issued": certificate_issued,
            "cert_category": cert_category,
        }
    )



@main_bp.route("/bites/<int:bite_id>/uncomplete", methods=["POST"])
@csrf.exempt
@login_required
def uncomplete_bite(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    progress = Progress.query.filter_by(user_id=current_user.id, bite_id=bite.id).first()

    if progress and progress.completed:
        progress.completed = False
        progress.completed_at = None
        db.session.commit()

    return jsonify({"success": True})


@main_bp.route("/bites/<int:bite_id>/quiz", methods=["POST"])
@csrf.exempt
@login_required
def submit_quiz(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    questions = bite.quiz_questions.all()
    data = request.get_json() or {}
    answers = data.get("answers", {})

    is_first_attempt = (
        QuizAttempt.query.filter_by(user_id=current_user.id, bite_id=bite.id).first() is None
    )

    score = 0
    results = []
    for q in questions:
        selected = answers.get(str(q.id))
        correct = selected == q.correct_option
        if correct:
            score += 1
            if is_first_attempt:
                from gamification import award_xp
                award_xp(current_user, Config.XP_PER_QUIZ_CORRECT, "quiz_correct")
        results.append(
            {
                "question_id": q.id,
                "correct": correct,
                "correct_option": q.correct_option,
                "explanation": q.explanation,
            }
        )

    if is_first_attempt and score == len(questions) and len(questions) > 0:
        from gamification import award_xp
        award_xp(current_user, 20, "quiz_perfect_bonus")

    attempt = QuizAttempt(
        user_id=current_user.id, bite_id=bite.id, score=score, total_questions=len(questions)
    )
    db.session.add(attempt)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "score": score,
            "total": len(questions),
            "xp": current_user.xp,
            "xp_awarded": is_first_attempt,
            "results": results,
        }
    )


@main_bp.route("/profile")
@login_required
def profile():
    completed_ids = current_user.completed_bite_ids()
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    avg_score = 0
    if attempts:
        avg_score = round(
            sum(a.score / a.total_questions for a in attempts if a.total_questions) / len(attempts) * 100
        )
    return render_template(
        "profile.html",
        completed_count=len(completed_ids),
        attempts_count=len(attempts),
        avg_score=avg_score,
        certificates=current_user.certificates.all(),
    )


@main_bp.route("/leaderboard")
def leaderboard():
    top_users = User.query.order_by(User.xp.desc()).limit(20).all()
    return render_template("leaderboard.html", top_users=top_users)


@main_bp.route("/courses")
def courses_list():
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("category")
    difficulty = request.args.get("difficulty")
    search = request.args.get("q", "").strip()

    query = Course.query
    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))

    pagination = query.order_by(Course.order_index.asc()).paginate(
        page=page, per_page=Config.BITES_PER_PAGE, error_out=False
    )
    categories = Category.query.all()
    completed_ids = []
    if current_user.is_authenticated:
        completed_ids = [p.course_id for p in CourseProgress.query.filter_by(user_id=current_user.id, completed=True).all()]

    return render_template(
        "courses_list.html",
        pagination=pagination,
        courses=pagination.items,
        categories=categories,
        completed_ids=completed_ids,
        active_category=category_slug,
        active_difficulty=difficulty,
        search=search,
    )


@main_bp.route("/courses/<slug>")
def course_detail(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()

    if course.is_premium and current_user.is_authenticated and current_user.plan == "free":
        flash("This course is part of our Premium track. Please upgrade your plan.", "warning")
        return redirect(url_for("payment.pricing"))
    if course.is_premium and not current_user.is_authenticated:
        flash("Please log in to access premium content.", "warning")
        return redirect(url_for("auth.login"))

    questions = course.quiz_questions.all()
    is_completed = False
    completed_course_ids = []
    if current_user.is_authenticated:
        progress = CourseProgress.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        is_completed = bool(progress and progress.completed)
        completed_course_ids = [p.course_id for p in CourseProgress.query.filter_by(user_id=current_user.id, completed=True).all()]

    # Fetch all courses in this category to build the learning path sidebar
    category_courses = []
    next_course = None
    if course.category_id:
        category_courses = Course.query.filter_by(category_id=course.category_id).order_by(Course.order_index.asc()).all()
        # Find next course
        for i, c in enumerate(category_courses):
            if c.id == course.id and i + 1 < len(category_courses):
                next_course = category_courses[i + 1]
                break

    return render_template(
        "course_detail.html", 
        course=course, 
        questions=questions, 
        is_completed=is_completed, 
        category_courses=category_courses,
        next_course=next_course,
        completed_course_ids=completed_course_ids
    )


@main_bp.route("/courses/<int:course_id>/complete", methods=["POST"])
@csrf.exempt
@login_required
def complete_course(course_id):
    course = Course.query.get_or_404(course_id)
    data = request.get_json() or {}
    answers = data.get("answers", {})

    progress = CourseProgress.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not progress:
        progress = CourseProgress(user_id=current_user.id, course_id=course.id)
        db.session.add(progress)

    newly_completed = not progress.completed
    progress.completed = True
    progress.completed_at = datetime.utcnow()

    xp_awarded = 0
    if newly_completed:
        # Give 300 XP for course completion
        course_xp = 300
        xp_awarded += course_xp
        current_user.update_streak()
        from gamification import award_xp
        award_xp(current_user, course_xp, "course_complete")

    # Grade Quiz
    questions = course.quiz_questions.all()
    score = 0
    total = len(questions)
    
    if total > 0:
        for q in questions:
            if answers.get(str(q.id)) == q.correct_option:
                score += 1
                xp_awarded += Config.XP_PER_QUIZ_CORRECT
                from gamification import award_xp
                award_xp(current_user, Config.XP_PER_QUIZ_CORRECT, "quiz_correct")

        if score == total and total > 0:
            from gamification import award_xp
            award_xp(current_user, 20, "quiz_perfect_bonus")
            xp_awarded += 20

        attempt = QuizAttempt(
            user_id=current_user.id,
            course_id=course.id,
            score=score,
            total_questions=total,
            attempted_at=datetime.utcnow(),
        )
        db.session.add(attempt)

    db.session.commit()

    return jsonify({
        "success": True,
        "score": score,
        "total": total,
        "xp_awarded": xp_awarded
    })
