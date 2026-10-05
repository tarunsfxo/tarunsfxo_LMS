from models import Payment


class TestPricing:
    def test_pricing_page_loads_publicly(self, client):
        resp = client.get("/pricing")
        assert resp.status_code == 200


class TestCheckout:
    def test_checkout_requires_login(self, client):
        resp = client.get("/checkout/pro", follow_redirects=True)
        assert resp.request.path == "/login"

    def test_checkout_invalid_plan_redirects(self, auth_client):
        resp = auth_client.get("/checkout/doesnotexist", follow_redirects=True)
        assert resp.request.path == "/pricing"

    def test_checkout_free_plan_sets_plan_directly(self, auth_client, user, db):
        resp = auth_client.get("/checkout/free", follow_redirects=True)
        assert resp.status_code == 200
        assert resp.request.path == "/dashboard"

    def test_checkout_pro_plan_get_loads_form(self, auth_client):
        resp = auth_client.get("/checkout/pro")
        assert resp.status_code == 200

    def test_checkout_pro_plan_valid_payment_succeeds(self, auth_client, user, db):
        resp = auth_client.post(
            "/checkout/pro",
            data={
                "card_number": "4111111111111111",
                "card_name": "Alice Doe",
                "expiry": "12/29",
                "cvv": "123",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        payment = Payment.query.filter_by(user_id=user.id).first()
        assert payment is not None
        assert payment.plan == "pro"
        assert payment.card_last4 == "1111"

    def test_checkout_invalid_card_number_rejected(self, auth_client, db):
        resp = auth_client.post(
            "/checkout/pro",
            data={
                "card_number": "123",
                "card_name": "Alice Doe",
                "expiry": "12/29",
                "cvv": "123",
            },
        )
        assert resp.status_code == 200
        assert Payment.query.count() == 0

    def test_checkout_invalid_cvv_rejected(self, auth_client, db):
        resp = auth_client.post(
            "/checkout/pro",
            data={
                "card_number": "4111111111111111",
                "card_name": "Alice Doe",
                "expiry": "12/29",
                "cvv": "12",
            },
        )
        assert resp.status_code == 200
        assert Payment.query.count() == 0


class TestBillingHistory:
    def test_billing_history_requires_login(self, client):
        resp = client.get("/billing/history", follow_redirects=True)
        assert resp.request.path == "/login"

    def test_billing_history_loads(self, auth_client):
        resp = auth_client.get("/billing/history")
        assert resp.status_code == 200


class TestAnalyticsAPIs:
    def test_analytics_page_requires_login(self, client):
        resp = client.get("/analytics", follow_redirects=True)
        assert resp.request.path == "/login"

    def test_analytics_page_loads(self, auth_client):
        resp = auth_client.get("/analytics")
        assert resp.status_code == 200

    def test_category_progress_api(self, auth_client, bite):
        resp = auth_client.get("/api/analytics/category-progress")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "labels" in data and "completed" in data and "total" in data

    def test_weekly_activity_api(self, auth_client):
        resp = auth_client.get("/api/analytics/weekly-activity")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["labels"]) == 7
        assert len(data["counts"]) == 7

    def test_quiz_performance_api(self, auth_client):
        resp = auth_client.get("/api/analytics/quiz-performance")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "labels" in data and "scores" in data

    def test_difficulty_breakdown_api(self, auth_client):
        resp = auth_client.get("/api/analytics/difficulty-breakdown")
        assert resp.status_code == 200
        data = resp.get_json()
        assert set(data["labels"]) == {"beginner", "intermediate", "advanced"}

    def test_analytics_apis_require_login(self, client):
        for path in [
            "/api/analytics/category-progress",
            "/api/analytics/weekly-activity",
            "/api/analytics/quiz-performance",
            "/api/analytics/difficulty-breakdown",
        ]:
            resp = client.get(path, follow_redirects=True)
            assert resp.request.path == "/login"
