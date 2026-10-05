import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import create_app
from extensions import db as _db
from models import User, Category, Bite, QuizQuestion


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def category(db):
    cat = Category(name="Python", slug="python", icon="code", color="#6366f1")
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture()
def bite(db, category):
    b = Bite(
        title="List Comprehensions",
        slug="list-comprehensions",
        summary="Learn list comprehensions.",
        content="Full content body about list comprehensions.",
        code_snippet="[x for x in range(10)]",
        difficulty="beginner",
        duration_minutes=5,
        category_id=category.id,
        is_premium=False,
        order_index=1,
    )
    db.session.add(b)
    db.session.commit()
    return b


@pytest.fixture()
def premium_bite(db, category):
    b = Bite(
        title="Advanced Decorators",
        slug="advanced-decorators",
        summary="Deep dive into decorators.",
        content="Full content body about decorators.",
        code_snippet="def deco(f): return f",
        difficulty="advanced",
        duration_minutes=15,
        category_id=category.id,
        is_premium=True,
        order_index=2,
    )
    db.session.add(b)
    db.session.commit()
    return b


@pytest.fixture()
def quiz_question(db, bite):
    q = QuizQuestion(
        bite_id=bite.id,
        question="What does [x for x in range(3)] produce?",
        option_a="[0, 1, 2]",
        option_b="[1, 2, 3]",
        option_c="(0, 1, 2)",
        option_d="None",
        correct_option="A",
        explanation="range(3) yields 0, 1, 2.",
    )
    db.session.add(q)
    db.session.commit()
    return q


@pytest.fixture()
def user(db):
    u = User(username="alice", email="alice@example.com", plan="free")
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def admin_user(db):
    u = User(username="admin", email="admin@example.com", plan="pro", is_admin=True)
    u.set_password("adminpass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def auth_client(client, user):
    client.post(
        "/login",
        data={"identifier": "alice", "password": "password123"},
        follow_redirects=True,
    )
    return client


@pytest.fixture()
def admin_client(client, admin_user):
    client.post(
        "/login",
        data={"identifier": "admin", "password": "adminpass123"},
        follow_redirects=True,
    )
    return client
