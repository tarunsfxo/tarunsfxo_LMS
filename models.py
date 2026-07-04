from datetime import datetime, date
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

    def level(self):
        return (self.xp // 100) + 1

    def xp_to_next_level(self):
        return 100 - (self.xp % 100)

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
    bite_id = db.Column(db.Integer, db.ForeignKey("bites.id"), nullable=False)
    question = db.Column(db.String(300), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A/B/C/D
    explanation = db.Column(db.String(300))


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
    bite_id = db.Column(db.Integer, db.ForeignKey("bites.id"), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.Index("ix_quiz_attempts_user_bite", "user_id", "bite_id"),)


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
