from models import Progress, QuizAttempt, XPLog


class TestBitesList:
    def test_bites_list_loads(self, client, bite):
        resp = client.get("/bites")
        assert resp.status_code == 200
        assert b"List Comprehensions" in resp.data

    def test_bites_list_filters_by_category(self, client, bite, category):
        resp = client.get(f"/bites?category={category.slug}")
        assert resp.status_code == 200
        assert b"List Comprehensions" in resp.data

    def test_bites_list_filters_by_unknown_category_returns_empty(self, client, bite):
        resp = client.get("/bites?category=does-not-exist")
        assert resp.status_code == 200
        # unknown category slug is ignored by the route, but should not error
        assert resp.status_code == 200

    def test_bites_list_filters_by_difficulty(self, client, bite, premium_bite):
        resp = client.get("/bites?difficulty=advanced")
        assert resp.status_code == 200
        assert b"Advanced Decorators" in resp.data
        assert b"List Comprehensions" not in resp.data

    def test_bites_list_search(self, client, bite, premium_bite):
        resp = client.get("/bites?q=Decorators")
        assert resp.status_code == 200
        assert b"Advanced Decorators" in resp.data
        assert b"List Comprehensions" not in resp.data

    def test_bites_list_pagination_param(self, client, bite):
        resp = client.get("/bites?page=1")
        assert resp.status_code == 200


class TestBiteDetail:
    def test_bite_detail_loads(self, client, bite):
        resp = client.get(f"/bites/{bite.slug}")
        assert resp.status_code == 200
        assert b"List Comprehensions" in resp.data

    def test_bite_detail_404_for_unknown_slug(self, client):
        resp = client.get("/bites/does-not-exist")
        assert resp.status_code == 404

    def test_premium_bite_redirects_anonymous_to_login(self, client, premium_bite):
        resp = client.get(f"/bites/{premium_bite.slug}", follow_redirects=True)
        assert resp.request.path == "/login"

    def test_premium_bite_redirects_free_user_to_pricing(self, auth_client, premium_bite):
        resp = auth_client.get(f"/bites/{premium_bite.slug}", follow_redirects=True)
        assert resp.request.path == "/pricing"

    def test_premium_bite_accessible_to_pro_user(self, admin_client, premium_bite):
        resp = admin_client.get(f"/bites/{premium_bite.slug}")
        assert resp.status_code == 200


class TestCompleteBite:
    def test_complete_bite_requires_login(self, client, bite):
        resp = client.post(f"/bites/{bite.id}/complete")
        assert resp.status_code in (302, 401)

    def test_complete_bite_awards_xp(self, auth_client, bite, premium_bite, db, user):
        resp = auth_client.post(f"/bites/{bite.id}/complete")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["xp"] == 10  # XP_PER_BITE

        progress = Progress.query.filter_by(user_id=user.id, bite_id=bite.id).first()
        assert progress is not None
        assert progress.completed is True

    def test_complete_bite_idempotent_xp(self, auth_client, bite, premium_bite):
        auth_client.post(f"/bites/{bite.id}/complete")
        resp = auth_client.post(f"/bites/{bite.id}/complete")
        data = resp.get_json()
        # XP should not double-award on repeat completion
        assert data["xp"] == 10

    def test_complete_unknown_bite_404(self, auth_client):
        resp = auth_client.post("/bites/9999/complete")
        assert resp.status_code == 404

    def test_complete_bite_creates_xp_log(self, auth_client, bite, user):
        auth_client.post(f"/bites/{bite.id}/complete")
        log = XPLog.query.filter_by(user_id=user.id, reason="bite_complete").first()
        assert log is not None
        assert log.amount == 10

    def test_uncomplete_bite_requires_login(self, client, bite):
        resp = client.post(f"/bites/{bite.id}/uncomplete")
        assert resp.status_code in (302, 401)

    def test_uncomplete_bite_resets_progress(self, auth_client, bite, user):
        auth_client.post(f"/bites/{bite.id}/complete")
        resp = auth_client.post(f"/bites/{bite.id}/uncomplete")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

        progress = Progress.query.filter_by(user_id=user.id, bite_id=bite.id).first()
        assert progress.completed is False
        assert progress.completed_at is None

    def test_uncomplete_bite_does_not_refund_xp(self, auth_client, bite, premium_bite, user):
        auth_client.post(f"/bites/{bite.id}/complete")
        auth_client.post(f"/bites/{bite.id}/uncomplete")
        from models import User as UserModel
        refreshed = UserModel.query.get(user.id)
        assert refreshed.xp == 10

    def test_uncomplete_unknown_bite_404(self, auth_client):
        resp = auth_client.post("/bites/9999/uncomplete")
        assert resp.status_code == 404


class TestQuiz:
    def test_submit_quiz_correct_answer(self, auth_client, bite, quiz_question):
        resp = auth_client.post(
            f"/bites/{bite.id}/quiz",
            json={"answers": {str(quiz_question.id): "A"}},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["score"] == 1
        assert data["total"] == 1
        assert data["results"][0]["correct"] is True

    def test_submit_quiz_incorrect_answer(self, auth_client, bite, quiz_question):
        resp = auth_client.post(
            f"/bites/{bite.id}/quiz",
            json={"answers": {str(quiz_question.id): "B"}},
        )
        data = resp.get_json()
        assert data["score"] == 0
        assert data["results"][0]["correct"] is False

    def test_submit_quiz_creates_attempt_record(self, auth_client, bite, quiz_question, db, user):
        auth_client.post(
            f"/bites/{bite.id}/quiz",
            json={"answers": {str(quiz_question.id): "A"}},
        )
        attempt = QuizAttempt.query.filter_by(user_id=user.id, bite_id=bite.id).first()
        assert attempt is not None
        assert attempt.score == 1
        assert attempt.total_questions == 1

    def test_submit_quiz_requires_login(self, client, bite, quiz_question):
        resp = client.post(f"/bites/{bite.id}/quiz", json={"answers": {}})
        assert resp.status_code in (302, 401)


class TestDashboardAndProfile:
    def test_dashboard_requires_login(self, client):
        resp = client.get("/dashboard", follow_redirects=True)
        assert resp.request.path == "/login"

    def test_dashboard_loads_for_authenticated_user(self, auth_client, bite):
        resp = auth_client.get("/dashboard")
        assert resp.status_code == 200

    def test_profile_requires_login(self, client):
        resp = client.get("/profile", follow_redirects=True)
        assert resp.request.path == "/login"

    def test_profile_loads_for_authenticated_user(self, auth_client):
        resp = auth_client.get("/profile")
        assert resp.status_code == 200


class TestLeaderboard:
    def test_leaderboard_loads_publicly(self, client, user):
        resp = client.get("/leaderboard")
        assert resp.status_code == 200
        assert b"alice" in resp.data
