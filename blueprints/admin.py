from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from slugify_helper import slugify
from extensions import db
from models import User, Bite, Category, QuizQuestion, Payment, Certificate, Progress, XPLog, UserSession, Course, CourseProgress

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_users": User.query.count(),
        "total_bites": Bite.query.count(),
        "total_categories": Category.query.count(),
        "total_revenue": db.session.query(db.func.sum(Payment.amount)).filter_by(status="success").scalar() or 0,
        "total_certificates": Certificate.query.count(),
        "completed_bites": Progress.query.filter_by(completed=True).count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html", stats=stats, recent_users=recent_users, recent_payments=recent_payments)


@admin_bp.route("/bites")
@login_required
@admin_required
def manage_bites():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()
    category_filter = request.args.get("category_id", "", type=str)
    per_page = 15

    query = Bite.query
    if search:
        query = query.filter(Bite.title.ilike(f"%{search}%"))
    if category_filter:
        query = query.filter(Bite.category_id == int(category_filter))
    query = query.order_by(Bite.order_index.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    categories = Category.query.all()
    return render_template(
        "admin/bites.html",
        bites=pagination.items,
        pagination=pagination,
        categories=categories,
        search=search,
        category_filter=category_filter,
    )


@admin_bp.route("/bites/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_bite():
    categories = Category.query.all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        bite = Bite(
            title=title,
            slug=slugify(title) + "-" + str(Bite.query.count() + 1),
            summary=request.form.get("summary", "").strip(),
            content=request.form.get("content", "").strip(),
            code_snippet=request.form.get("code_snippet", "").strip(),
            difficulty=request.form.get("difficulty", "beginner"),
            duration_minutes=int(request.form.get("duration_minutes", 5) or 5),
            category_id=request.form.get("category_id") or None,
            is_premium=bool(request.form.get("is_premium")),
            order_index=int(request.form.get("order_index", 0) or 0),
        )
        db.session.add(bite)
        db.session.commit()
        flash("Bite created successfully.", "success")
        return redirect(url_for("admin.manage_bites"))
    return render_template("admin/bite_form.html", categories=categories, bite=None)


@admin_bp.route("/bites/<int:bite_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_bite(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    categories = Category.query.all()
    if request.method == "POST":
        bite.title = request.form.get("title", bite.title).strip()
        bite.summary = request.form.get("summary", "").strip()
        bite.content = request.form.get("content", "").strip()
        bite.code_snippet = request.form.get("code_snippet", "").strip()
        bite.difficulty = request.form.get("difficulty", bite.difficulty)
        bite.duration_minutes = int(request.form.get("duration_minutes", 5) or 5)
        bite.category_id = request.form.get("category_id") or None
        bite.is_premium = bool(request.form.get("is_premium"))
        bite.order_index = int(request.form.get("order_index", 0) or 0)
        db.session.commit()
        flash("Bite updated successfully.", "success")
        return redirect(url_for("admin.manage_bites"))
    return render_template("admin/bite_form.html", categories=categories, bite=bite)


@admin_bp.route("/bites/<int:bite_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_bite(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    db.session.delete(bite)
    db.session.commit()
    flash("Bite deleted.", "info")
    return redirect(url_for("admin.manage_bites"))


@admin_bp.route("/bites/<int:bite_id>/questions", methods=["GET", "POST"])
@login_required
@admin_required
def manage_questions(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    if request.method == "POST":
        q = QuizQuestion(
            bite_id=bite.id,
            question=request.form.get("question", "").strip(),
            option_a=request.form.get("option_a", "").strip(),
            option_b=request.form.get("option_b", "").strip(),
            option_c=request.form.get("option_c", "").strip(),
            option_d=request.form.get("option_d", "").strip(),
            correct_option=request.form.get("correct_option", "A").upper(),
            explanation=request.form.get("explanation", "").strip(),
        )
        db.session.add(q)
        db.session.commit()
        flash("Question added.", "success")
        return redirect(url_for("admin.manage_questions", bite_id=bite.id))
    return render_template("admin/questions.html", bite=bite)


@admin_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_question(question_id):
    q = QuizQuestion.query.get_or_404(question_id)
    bite_id = q.bite_id
    course_id = q.course_id
    db.session.delete(q)
    db.session.commit()
    flash("Question removed.", "info")
    if course_id:
        return redirect(url_for("admin.manage_course_questions", course_id=course_id))
    return redirect(url_for("admin.manage_questions", bite_id=bite_id))


def extract_youtube_id(url):
    import re
    match = re.search(r'(?:v=|youtu\.be\/|\/embed\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else url


@admin_bp.route("/courses")
@login_required
@admin_required
def manage_courses():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()
    category_filter = request.args.get("category_id", "", type=str)
    per_page = 15

    query = Course.query
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))
    if category_filter:
        query = query.filter(Course.category_id == int(category_filter))
    query = query.order_by(Course.order_index.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    categories = Category.query.all()
    return render_template(
        "admin/courses.html",
        courses=pagination.items,
        pagination=pagination,
        categories=categories,
        search=search,
        category_filter=category_filter,
    )


@admin_bp.route("/courses/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_course():
    categories = Category.query.all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        raw_url = request.form.get("youtube_url", "").strip()
        course = Course(
            title=title,
            slug=slugify(title) + "-" + str(Course.query.count() + 1),
            summary=request.form.get("summary", "").strip(),
            description=request.form.get("description", "").strip(),
            youtube_video_id=extract_youtube_id(raw_url),
            difficulty=request.form.get("difficulty", "beginner"),
            category_id=request.form.get("category_id") or None,
            is_premium=bool(request.form.get("is_premium")),
            order_index=int(request.form.get("order_index", 0) or 0),
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created successfully.", "success")
        return redirect(url_for("admin.manage_courses"))
    return render_template("admin/course_form.html", categories=categories, course=None)


@admin_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    categories = Category.query.all()
    if request.method == "POST":
        course.title = request.form.get("title", course.title).strip()
        course.summary = request.form.get("summary", "").strip()
        course.description = request.form.get("description", "").strip()
        raw_url = request.form.get("youtube_url", "").strip()
        if raw_url:
            course.youtube_video_id = extract_youtube_id(raw_url)
        course.difficulty = request.form.get("difficulty", course.difficulty)
        course.category_id = request.form.get("category_id") or None
        course.is_premium = bool(request.form.get("is_premium"))
        course.order_index = int(request.form.get("order_index", 0) or 0)
        db.session.commit()
        flash("Course updated successfully.", "success")
        return redirect(url_for("admin.manage_courses"))
    return render_template("admin/course_form.html", categories=categories, course=course)


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("admin.manage_courses"))


@admin_bp.route("/courses/<int:course_id>/questions", methods=["GET", "POST"])
@login_required
@admin_required
def manage_course_questions(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == "POST":
        q = QuizQuestion(
            course_id=course.id,
            question=request.form.get("question", "").strip(),
            option_a=request.form.get("option_a", "").strip(),
            option_b=request.form.get("option_b", "").strip(),
            option_c=request.form.get("option_c", "").strip(),
            option_d=request.form.get("option_d", "").strip(),
            correct_option=request.form.get("correct_option", "A").upper(),
            explanation=request.form.get("explanation", "").strip(),
        )
        db.session.add(q)
        db.session.commit()
        flash("Question added.", "success")
        return redirect(url_for("admin.manage_course_questions", course_id=course.id))
    return render_template("admin/course_questions.html", course=course)




@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def manage_categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = Category(
            name=name,
            slug=slugify(name),
            icon=request.form.get("icon", "code").strip(),
            color=request.form.get("color", "#6366f1").strip(),
        )
        db.session.add(category)
        db.session.commit()
        flash("Category created.", "success")
        return redirect(url_for("admin.manage_categories"))
    categories = Category.query.all()
    return render_template("admin/categories.html", categories=categories)


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_category(category_id):
    cat = Category.query.get_or_404(category_id)
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.manage_categories"))


@admin_bp.route("/users")
@login_required
@admin_required
def manage_users():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()
    plan_filter = request.args.get("plan", "").strip()
    per_page = 20

    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    if plan_filter:
        query = query.filter(User.plan == plan_filter)
    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        search=search,
        plan_filter=plan_filter,
    )


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot change your own admin status.", "warning")
        return redirect(url_for("admin.manage_users"))
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"Updated admin status for {user.username}.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account here.", "warning")
        return redirect(url_for("admin.manage_users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/payments")
@login_required
@admin_required
def manage_payments():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = (
        Payment.query.order_by(Payment.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return render_template("admin/payments.html", payments=pagination.items, pagination=pagination)


@admin_bp.route("/xp-log")
@login_required
@admin_required
def manage_xp_log():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = (
        XPLog.query.order_by(XPLog.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return render_template("admin/xp_log.html", logs=pagination.items, pagination=pagination)


@admin_bp.route("/sessions")
@login_required
@admin_required
def manage_sessions():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = (
        UserSession.query.order_by(UserSession.enter_time.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return render_template("admin/sessions.html", sessions=pagination.items, pagination=pagination)


# --- Coding Practice Admin Routes ---
from models import CodingProblem, CodingTestCase, CodingSubmission

@admin_bp.route("/coding")
@admin_bp.route("/coding/<path:path>")
@login_required
@admin_required
def coding_admin(path=""):
    # This will serve the React admin application
    return render_template("admin_coding_app.html")

@admin_bp.route("/api/coding/problems", methods=["GET"])
@login_required
@admin_required
def api_admin_get_problems():
    problems = CodingProblem.query.order_by(CodingProblem.created_at.desc()).all()
    return jsonify([{
        "id": p.id,
        "title": p.title,
        "slug": p.slug,
        "difficulty": p.difficulty,
        "is_published": p.is_published
    } for p in problems])


@admin_bp.route("/api/coding/problems/create", methods=["POST"])
@login_required
@admin_required
def api_admin_create_problem():
    """Create a new coding problem with test cases from the admin UI."""
    from slugify_helper import slugify
    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"success": False, "error": "Title is required."}), 400

    # Build a unique slug
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while CodingProblem.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    problem = CodingProblem(
        title=title,
        slug=slug,
        description=(data.get("description") or "").strip(),
        difficulty=data.get("difficulty", "Easy"),
        time_limit=float(data.get("time_limit", 2.0)),
        is_published=bool(data.get("is_published", False)),
    )

    # Tags
    for tag_name in data.get("tags", []):
        tag_name = tag_name.strip()
        if not tag_name:
            continue
        tag = CodingTag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = CodingTag(name=tag_name)
            db.session.add(tag)
        problem.tags.append(tag)

    db.session.add(problem)
    db.session.flush()  # get problem.id before committing

    # Test cases
    for tc in data.get("test_cases", []):
        test_case = CodingTestCase(
            problem_id=problem.id,
            input_data=tc.get("input_data", ""),
            expected_output=tc.get("expected_output", ""),
            is_hidden=bool(tc.get("is_hidden", False)),
        )
        db.session.add(test_case)

    db.session.commit()
    return jsonify({"success": True, "id": problem.id, "slug": problem.slug})


@admin_bp.route("/api/coding/students", methods=["GET"])
@login_required
@admin_required
def api_admin_get_students():
    students = User.query.all()
    results = []
    for s in students:
        submissions = CodingSubmission.query.filter_by(user_id=s.id).all()
        solved = len(set(sub.problem_id for sub in submissions if sub.verdict == "Accepted"))
        if len(submissions) > 0:
            results.append({
                "id": s.id,
                "username": s.username,
                "email": s.email,
                "total_solved": solved,
                "total_submissions": len(submissions)
            })
    return jsonify(results)
