from datetime import date, timedelta

from models import User


class TestIndexAndErrors:
    def test_index_loads(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_404_page(self, client):
        resp = client.get("/this-route-does-not-exist")
        assert resp.status_code == 404


class TestUserModel:
    def test_password_hashing(self, db):
        u = User(username="dave", email="dave@example.com")
        u.set_password("mysecret")
        assert u.password_hash != "mysecret"
        assert u.check_password("mysecret") is True
        assert u.check_password("wrong") is False

    def test_level_calculation(self, db):
        u = User(username="eve", email="eve@example.com", xp=250)
        assert u.level() == 2
        assert u.xp_to_next_level() == 350

    def test_update_streak_first_login(self, db):
        u = User(username="frank", email="frank@example.com")
        assert u.last_active_date is None
        u.update_streak()
        assert u.streak_count == 1
        assert u.last_active_date == date.today()

    def test_update_streak_consecutive_day(self, db):
        u = User(username="grace", email="grace@example.com")
        u.last_active_date = date.today() - timedelta(days=1)
        u.streak_count = 3
        u.update_streak()
        assert u.streak_count == 4

    def test_update_streak_broken(self, db):
        u = User(username="hank", email="hank@example.com")
        u.last_active_date = date.today() - timedelta(days=5)
        u.streak_count = 10
        u.update_streak()
        assert u.streak_count == 1

    def test_update_streak_same_day_noop(self, db):
        u = User(username="iris", email="iris@example.com")
        u.last_active_date = date.today()
        u.streak_count = 2
        u.update_streak()
        assert u.streak_count == 2
