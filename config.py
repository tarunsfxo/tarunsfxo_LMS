import os
from datetime import timedelta
from urllib.parse import urlparse, urlunparse, quote

basedir = os.path.abspath(os.path.dirname(__file__))

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(basedir, ".env"))
except ImportError:  # python-dotenv is optional at runtime if env vars are set another way
    pass


def normalize_database_url(url):
    """Normalize postgres:// → postgresql:// and re-encode any special chars in password."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Re-parse and re-encode so special chars in password (like @) are handled correctly
    try:
        parsed = urlparse(url)
        if parsed.password:
            # Decode any existing percent-encoding, then re-encode safely
            from urllib.parse import unquote
            raw_password = unquote(parsed.password)
            encoded_password = quote(raw_password, safe="")
            netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            url = urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        pass
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "tarunsfxo-lms-super-secret-key-2024")

    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "tarunsfxo_lms_db")
    SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL")

    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.environ.get(
            "DATABASE_URL",
            SUPABASE_DB_URL or f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 280, "pool_pre_ping": True}

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB request body cap

    CERTIFICATES_FOLDER = os.path.join(basedir, "certificates")
    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

    BITES_PER_PAGE = 9
    XP_PER_BITE = 10
    XP_PER_QUIZ_CORRECT = 5
    STREAK_BONUS_XP = 15

    # Fake payment plans
    PLANS = {
        "free": {"name": "Free", "price": 0, "bites_limit": 10},
        "pro": {"name": "Pro", "price": 9, "bites_limit": None},
        "team": {"name": "Team", "price": 29, "bites_limit": None},
    }


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
