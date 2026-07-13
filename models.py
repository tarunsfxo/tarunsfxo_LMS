from datetime import datetime, date
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    plan = db.Column(db.String(20), default="free")
    xp = db.Column(db.Integer, default=0)
    streak_count = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.Date, default=None)
    avatar_seed = db.Column(db.String(50), default="default")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    progress = db.relationship("Progress", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    quiz_attempts = db.relationship("QuizAttempt", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    certificates = db.relationship("Certificate", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    sessions = db.relationship("UserSession", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    badges = db.relationship("UserBadge", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    achievements = db.relationship("UserAchievement", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("UserNotification", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def latest_session(self):
        # We can import UserSession locally or use the class if defined earlier, but UserSession is defined at the end of the file.
        # However, we can use string ordering or just rely on the relationship.
        # Since it's dynamic, we can sort by enter_time.
        from models import UserSession
        return self.sessions.order_by(UserSession.enter_time.desc()).first()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

    def level(self):
        if self.xp < 250:
            return 1
        elif self.xp < 600:
            return 2
        elif self.xp < 1000:
            return 3
        return 4 + (self.xp - 1000) // 500

    def xp_to_next_level(self):
        current_lvl = self.level()
        if current_lvl == 1:
            return 250 - self.xp
        elif current_lvl == 2:
            return 600 - self.xp
        elif current_lvl == 3:
            return 1000 - self.xp
        else:
            next_lvl_xp = 1000 + (current_lvl - 3) * 500
            return next_lvl_xp - self.xp

    def update_streak(self):
        today = date.today()
        if self.last_active_date is None:
            self.streak_count = 1
        elif self.last_active_date == today:
            return
        elif (today - self.last_active_date).days == 1:
            self.streak_count += 1
        elif (today - self.last_active_date).days > 1:
            self.streak_count = 1
        self.last_active_date = today

    def completed_bite_ids(self):
        return [p.bite_id for p in self.progress.filter_by(completed=True)]

    def __repr__(self):
        return f"<User {self.username}>"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(50), default="code")
    color = db.Column(db.String(20), default="#6366f1")

    bites = db.relationship("Bite", backref="category", lazy="dynamic")
    courses = db.relationship("Course", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Bite(db.Model):
    __tablename__ = "bites"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False)
    summary = db.Column(db.String(300))
    content = db.Column(db.Text, nullable=False)
    code_snippet = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default="beginner")  # beginner/intermediate/advanced
    duration_minutes = db.Column(db.Integer, default=5)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), index=True)
    is_premium = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quiz_questions = db.relationship("QuizQuestion", backref="bite", lazy="dynamic", cascade="all, delete-orphan")
    progress_entries = db.relationship("Progress", backref="bite", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Bite {self.title}>"


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    bite_id = db.Column(db.Integer, db.ForeignKey("bites.id"), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    question = db.Column(db.String(300), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A/B/C/D
    explanation = db.Column(db.String(300))


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False)
    summary = db.Column(db.String(300))
    description = db.Column(db.Text)
    youtube_video_id = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), default="beginner")
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), index=True)
    is_premium = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quiz_questions = db.relationship("QuizQuestion", backref="course", lazy="dynamic", cascade="all, delete-orphan")
    progress_entries = db.relationship("CourseProgress", backref="course", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course {self.title}>"


class CourseProgress(db.Model):
    __tablename__ = "course_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uix_user_course"),)


class Progress(db.Model):
    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bite_id = db.Column(db.Integer, db.ForeignKey("bites.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    time_spent_seconds = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint("user_id", "bite_id", name="uix_user_bite"),)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bite_id = db.Column(db.Integer, db.ForeignKey("bites.id"), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_quiz_attempts_user_bite", "user_id", "bite_id"),
        db.Index("ix_quiz_attempts_user_course", "user_id", "course_id"),
    )


class XPLog(db.Model):
    __tablename__ = "xp_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("xp_logs", lazy="dynamic", cascade="all, delete-orphan"))

    __table_args__ = (db.Index("ix_xp_log_user_id", "user_id"),)

    def __repr__(self):
        return f"<XPLog user={self.user_id} {self.amount:+d} ({self.reason})>"


class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    cert_code = db.Column(db.String(40), unique=True, nullable=False)
    file_path = db.Column(db.String(255))
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    card_last4 = db.Column(db.String(4))
    status = db.Column(db.String(20), default="success")
    transaction_id = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserSession(db.Model):
    __tablename__ = "user_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    enter_time = db.Column(db.DateTime, default=datetime.utcnow)
    leave_time = db.Column(db.DateTime, nullable=True)
    activity = db.Column(db.String(150), nullable=True)

    def __repr__(self):
        return f"<UserSession user={self.user_id} activity='{self.activity}'>"

# --- Coding Practice Models ---

problem_tags = db.Table(
    'problem_tags',
    db.Column('problem_id', db.Integer, db.ForeignKey('coding_problems.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('coding_tags.id'), primary_key=True)
)

class CodingTag(db.Model):
    __tablename__ = "coding_tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<CodingTag {self.name}>"

class CodingProblem(db.Model):
    __tablename__ = "coding_problems"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), default="Easy") # Easy, Medium, Hard
    time_limit = db.Column(db.Float, default=1.0) # in seconds
    memory_limit = db.Column(db.Integer, default=128000) # in KB
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tags = db.relationship('CodingTag', secondary=problem_tags, lazy='subquery',
                           backref=db.backref('problems', lazy=True))
    test_cases = db.relationship("CodingTestCase", backref="problem", lazy="dynamic", cascade="all, delete-orphan")
    submissions = db.relationship("CodingSubmission", backref="problem", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CodingProblem {self.title}>"

class CodingTestCase(db.Model):
    __tablename__ = "coding_test_cases"

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("coding_problems.id"), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False)
    explanation = db.Column(db.Text, nullable=True) # Usually for visible sample test cases

    def __repr__(self):
        return f"<CodingTestCase problem={self.problem_id} hidden={self.is_hidden}>"

class CodingSubmission(db.Model):
    __tablename__ = "coding_submissions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey("coding_problems.id"), nullable=False)
    language = db.Column(db.String(20), nullable=False)
    code = db.Column(db.Text, nullable=False)
    verdict = db.Column(db.String(50), default="Pending") # Accepted, Wrong Answer, TLE, etc.
    runtime = db.Column(db.Float, nullable=True) # in seconds
    memory = db.Column(db.Integer, nullable=True) # in KB
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    judge0_token = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<CodingSubmission user={self.user_id} problem={self.problem_id} verdict={self.verdict}>"


class UserBadge(db.Model):
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    badge_icon = db.Column(db.String(50), nullable=False)
    badge_description = db.Column(db.String(255), nullable=True)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "badge_name", name="uix_user_badge"),
    )

    def __repr__(self):
        return f"<UserBadge user={self.user_id} badge='{self.badge_name}'>"


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    achievement_name = db.Column(db.String(100), nullable=False)
    achievement_description = db.Column(db.String(255), nullable=True)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "achievement_name", name="uix_user_achievement"),
    )

    def __repr__(self):
        return f"<UserAchievement user={self.user_id} achievement='{self.achievement_name}'>"


class UserNotification(db.Model):
    __tablename__ = "user_notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'level_up', 'badge', 'streak', 'course_completed', 'certificate'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserNotification user={self.user_id} type='{self.type}' read={self.is_read}>"
