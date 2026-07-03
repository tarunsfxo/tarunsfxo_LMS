import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from config import config_map
from extensions import db, login_manager, csrf
from models import User


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    if config_name == "production":
        if app.config["SECRET_KEY"] == "tarunsfxo-lms-super-secret-key-2024":
            raise RuntimeError(
                "Refusing to start in production with the default SECRET_KEY. "
                "Set the SECRET_KEY environment variable to a unique random value."
            )
        try:
            from werkzeug.middleware.proxy_fix import ProxyFix

            app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
        except ImportError:
            pass

        if not app.debug and not app.testing:
            os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
            file_handler = RotatingFileHandler(
                os.path.join(os.path.dirname(__file__), "logs", "tarunsfxo_lms.log"),
                maxBytes=1_048_576,
                backupCount=5,
            )
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
            )
            file_handler.setLevel(logging.WARNING)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.WARNING)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    os.makedirs(app.config["CERTIFICATES_FOLDER"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from blueprints.auth import auth_bp
    from blueprints.main import main_bp
    from blueprints.payment import payment_bp
    from blueprints.certificate import certificate_bp
    from blueprints.analytics import analytics_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(certificate_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_year": datetime.utcnow().year, "app_name": "tarunsfxo LMS"}

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("seed-db")
    def seed_db():
        """Seed the database with sample data."""
        from seed import run_seed
        run_seed()
        print("Database seeded successfully.")

    @app.cli.command("bootstrap-db")
    def bootstrap_db():
        """Create tables and seed sample data only when the database is empty."""
        from models import Category
        from seed import seed_sample_data

        db.create_all()
        if Category.query.first():
            print("Database already contains seed data; skipping sample seed.")
            return

        seed_sample_data()
        print("Database bootstrapped successfully.")

    # Automatically create database tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False), host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
