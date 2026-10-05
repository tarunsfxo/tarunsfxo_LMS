from models import Bite, Category, QuizQuestion, User


class TestAdminAccessControl:
    def test_admin_dashboard_requires_login(self, client):
        resp = client.get("/admin/", follow_redirects=True)
        assert resp.request.path == "/login"

    def test_admin_dashboard_blocks_non_admin(self, auth_client):
        resp = auth_client.get("/admin/", follow_redirects=True)
        assert resp.request.path == "/"

    def test_admin_dashboard_allows_admin(self, admin_client):
        resp = admin_client.get("/admin/")
        assert resp.status_code == 200


class TestAdminBites:
    def test_manage_bites_loads(self, admin_client, bite):
        resp = admin_client.get("/admin/bites")
        assert resp.status_code == 200
        assert b"List Comprehensions" in resp.data

    def test_create_bite(self, admin_client, category, db):
        resp = admin_client.post(
            "/admin/bites/create",
            data={
                "title": "New Bite",
                "summary": "Summary",
                "content": "Body",
                "code_snippet": "",
                "difficulty": "beginner",
                "duration_minutes": "5",
                "category_id": str(category.id),
                "order_index": "0",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert Bite.query.filter_by(title="New Bite").first() is not None

    def test_edit_bite(self, admin_client, bite, db):
        resp = admin_client.post(
            f"/admin/bites/{bite.id}/edit",
            data={
                "title": "Updated Title",
                "summary": bite.summary,
                "content": bite.content,
                "code_snippet": bite.code_snippet,
                "difficulty": bite.difficulty,
                "duration_minutes": "5",
                "category_id": str(bite.category_id),
                "order_index": "0",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        updated = Bite.query.get(bite.id)
        assert updated.title == "Updated Title"

    def test_delete_bite(self, admin_client, bite, db):
        bite_id = bite.id
        resp = admin_client.post(f"/admin/bites/{bite_id}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert Bite.query.get(bite_id) is None

    def test_non_admin_cannot_create_bite(self, auth_client, category):
        resp = auth_client.post(
            "/admin/bites/create",
            data={"title": "Hacked Bite", "category_id": str(category.id)},
            follow_redirects=True,
        )
        assert resp.request.path == "/"
        assert Bite.query.filter_by(title="Hacked Bite").first() is None


class TestAdminQuestions:
    def test_manage_questions_loads(self, admin_client, bite):
        resp = admin_client.get(f"/admin/bites/{bite.id}/questions")
        assert resp.status_code == 200

    def test_add_question(self, admin_client, bite, db):
        resp = admin_client.post(
            f"/admin/bites/{bite.id}/questions",
            data={
                "question": "What is 2+2?",
                "option_a": "3",
                "option_b": "4",
                "option_c": "5",
                "option_d": "6",
                "correct_option": "B",
                "explanation": "Basic math.",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert QuizQuestion.query.filter_by(question="What is 2+2?").first() is not None

    def test_delete_question(self, admin_client, quiz_question, db):
        qid = quiz_question.id
        resp = admin_client.post(f"/admin/questions/{qid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert QuizQuestion.query.get(qid) is None


class TestAdminCategories:
    def test_manage_categories_loads(self, admin_client, category):
        resp = admin_client.get("/admin/categories")
        assert resp.status_code == 200
        assert b"Python" in resp.data

    def test_create_category(self, admin_client, db):
        resp = admin_client.post(
            "/admin/categories",
            data={"name": "Rust", "icon": "code", "color": "#ff0000"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert Category.query.filter_by(name="Rust").first() is not None

    def test_delete_category(self, admin_client, category, db):
        cat_id = category.id
        resp = admin_client.post(f"/admin/categories/{cat_id}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert Category.query.get(cat_id) is None


class TestAdminUsers:
    def test_manage_users_loads(self, admin_client, user):
        resp = admin_client.get("/admin/users")
        assert resp.status_code == 200
        assert b"alice" in resp.data

    def test_toggle_admin_status(self, admin_client, user, db):
        assert user.is_admin is False
        resp = admin_client.post(f"/admin/users/{user.id}/toggle-admin", follow_redirects=True)
        assert resp.status_code == 200
        refreshed = User.query.get(user.id)
        assert refreshed.is_admin is True

    def test_cannot_toggle_own_admin_status(self, admin_client, admin_user, db):
        resp = admin_client.post(f"/admin/users/{admin_user.id}/toggle-admin", follow_redirects=True)
        assert resp.status_code == 200
        refreshed = User.query.get(admin_user.id)
        assert refreshed.is_admin is True  # unchanged

    def test_delete_user(self, admin_client, user, db):
        user_id = user.id
        resp = admin_client.post(f"/admin/users/{user_id}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert User.query.get(user_id) is None

    def test_cannot_delete_own_account(self, admin_client, admin_user, db):
        resp = admin_client.post(f"/admin/users/{admin_user.id}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert User.query.get(admin_user.id) is not None


class TestAdminPayments:
    def test_manage_payments_loads(self, admin_client):
        resp = admin_client.get("/admin/payments")
        assert resp.status_code == 200


class TestAdminXPLog:
    def test_manage_xp_log_loads(self, admin_client):
        resp = admin_client.get("/admin/xp-log")
        assert resp.status_code == 200

    def test_manage_xp_log_requires_admin(self, auth_client):
        resp = auth_client.get("/admin/xp-log", follow_redirects=True)
        assert resp.request.path == "/"

    def test_manage_xp_log_shows_entries(self, admin_client, auth_client, bite):
        auth_client.post(f"/bites/{bite.id}/complete")
        resp = admin_client.get("/admin/xp-log")
        assert resp.status_code == 200
        assert b"Bite complete" in resp.data
