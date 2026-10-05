"""
Production WSGI entrypoint.

Used by WSGI servers such as gunicorn:

    gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

Always boots the app with the "production" config regardless of any
FLASK_ENV value that may be present in the environment, so this is the
safe, explicit entrypoint for deployments.
"""
import os

os.environ.setdefault("FLASK_ENV", "production")

from app import create_app

app = create_app("production")

if __name__ == "__main__":
    app.run()
