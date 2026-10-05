from models import User


class TestRegister:
    def test_register_page_loads(self, client):
        resp = client.get("/register")
        assert resp.status_code == 200

    def test_register_creates_user(self, client, db):
        resp = client.post(
            "/register",
            data={
                "username": "bob",
                "email": "bob@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert User.query.filter_by(username="bob").first() is not None

    def test_register_rejects_short_username(self, client):
        resp = client.post(
            "/register",
            data={
                "username": "ab",
                "email": "ab@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        assert resp.status_code == 200
        assert User.query.filter_by(username="ab").first() is None

    def test_register_rejects_mismatched_passwords(self, client):
        resp = client.post(
            "/register",
            data={
                "username": "carl",
                "email": "carl@example.com",
                "password": "secret123",
                "confirm_password": "different",
            },
        )
        assert resp.status_code == 200
        assert User.query.filter_by(username="carl").first() is None

    def test_register_rejects_duplicate_username(self, client, user):
        resp = client.post(
            "/register",
            data={
                "username": "alice",
                "email": "another@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        assert resp.status_code == 200
        assert User.query.filter_by(email="another@example.com").first() is None

    def test_register_redirects_if_already_authenticated(self, auth_client):
        resp = auth_client.get("/register")
        assert resp.status_code == 302


class TestLogin:
    def test_login_page_loads(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_login_with_username_succeeds(self, client, user):
        resp = client.post(
            "/login",
            data={"identifier": "alice", "password": "password123"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"dashboard" in resp.request.path.encode() or resp.request.path == "/dashboard"

    def test_login_with_email_succeeds(self, client, user):
        resp = client.post(
            "/login",
            data={"identifier": "alice@example.com", "password": "password123"},
            follow_redirects=True,
        )
        assert resp.request.path == "/dashboard"

    def test_login_with_wrong_password_fails(self, client, user):
        resp = client.post(
            "/login",
            data={"identifier": "alice", "password": "wrongpass"},
            follow_redirects=True,
        )
        assert resp.request.path == "/login"

    def test_login_with_unknown_user_fails(self, client):
        resp = client.post(
            "/login",
            data={"identifier": "nobody", "password": "whatever"},
            follow_redirects=True,
        )
        assert resp.request.path == "/login"

    def test_login_updates_streak(self, client, user, db):
        assert user.streak_count == 0
        client.post(
            "/login",
            data={"identifier": "alice", "password": "password123"},
        )
        refreshed = User.query.filter_by(username="alice").first()
        assert refreshed.streak_count == 1


class TestLogout:
    def test_logout_requires_login(self, client):
        resp = client.get("/logout", follow_redirects=True)
        assert resp.request.path == "/login"

    def test_logout_clears_session(self, auth_client):
        resp = auth_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200
        # Dashboard should now redirect to login since session is cleared
        dash = auth_client.get("/dashboard", follow_redirects=True)
        assert dash.request.path == "/login"
