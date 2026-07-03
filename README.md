# tarunsfxo LMS – Micro-Learning for Developers

A full-stack Flask web application for bite-sized developer learning: short lessons ("bites"), quizzes, XP/streak gamification, PDF certificates, a fake payment flow, an admin panel, and a Chart.js analytics dashboard with a lightweight rule-based "AI" recommendation engine.

## Tech Stack

- **Frontend:** HTML5, CSS3 (custom design system, no framework), Vanilla JavaScript, Chart.js
- **Backend:** Python 3.11+, Flask, Flask-Login
- **Database:** MySQL 8 (via SQLAlchemy + PyMySQL)
- **PDF Generation:** ReportLab (certificates)
- **Auth:** Flask-Login with hashed passwords (Werkzeug)

## Features

- User registration/login with sessions, "remember me", and admin roles
- Bites: short lessons with markdown-free rich content, code snippets, difficulty levels, categories, and premium gating
- Quizzes per bite with instant scoring and explanations
- XP, levels, and daily streak tracking
- Personalized recommendations (`recommend.py`) using category affinity + difficulty progression + popularity fallback — no external ML dependency required
- PDF certificate generation per category once a completion threshold is met (ReportLab, `certificates.py`)
- Fake payment / checkout flow with simulated card validation and transaction history (`blueprints/payment.py`) — **no real payments are processed**
- Analytics dashboard (`templates/analytics.html` + `static/js/analytics.js`) with four Chart.js visualizations backed by JSON API endpoints
- Full admin panel: manage bites, quiz questions, categories, users, and view payments
- Leaderboard ranked by XP

## Project Structure

```
tarunsfxo_lms/
├── app.py                  # Application factory + CLI commands
├── config.py                # Environment-based configuration
├── extensions.py            # Shared db / login_manager instances
├── models.py                 # SQLAlchemy models
├── recommend.py              # Rule-based recommendation engine
├── certificates.py           # ReportLab PDF certificate generator
├── seed.py                   # Sample data seeder (categories, bites, quizzes, users)
├── slugify_helper.py         # Tiny slug utility (no external dependency)
├── schema.sql                 # Raw MySQL schema (mirrors models.py)
├── requirements.txt
├── .env.example
├── blueprints/
│   ├── auth.py               # Register / login / logout
│   ├── main.py                # Home, dashboard, bites, quiz, profile, leaderboard
│   ├── payment.py             # Pricing, fake checkout, billing history
│   ├── certificate.py         # Certificate eligibility + generation + download
│   ├── analytics.py           # Analytics page + JSON chart APIs
│   └── admin.py               # Admin panel routes
├── templates/
│   ├── base.html, index.html, login.html, register.html, dashboard.html,
│   │   bites_list.html, bite_detail.html, pricing.html, checkout.html,
│   │   payment_success.html, billing_history.html, certificates.html,
│   │   analytics.html, profile.html, leaderboard.html, 404.html, 500.html
│   └── admin/
│       ├── base_admin.html, dashboard.html, bites.html, bite_form.html,
│       │   questions.html, categories.html, users.html, payments.html
├── static/
│   ├── css/style.css
│   └── js/main.js, bite.js, analytics.js
└── certificates/             # Generated PDF certificates land here
```

## Setup Instructions

### 1. Clone & create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# edit .env with your MySQL credentials
```

### 3. Create the MySQL database

Either let SQLAlchemy create tables automatically, or run the raw schema:

```bash
mysql -u root -p < schema.sql
```

### 4. Initialize and seed the database

```bash
export FLASK_APP=app.py        # Windows: set FLASK_APP=app.py
flask init-db                  # creates all tables
flask seed-db                  # populates categories, bites, quizzes, demo users
```

This creates two accounts:
- **Admin:** `admin@tarunsfxo.com` / `Admin@123`
- **Demo user:** `demo@tarunsfxo.com` / `Demo@123`

### 5. Run the development server

```bash
python app.py
```

Visit `http://localhost:5000`.

## Key Routes

| Route | Description |
|---|---|
| `/` | Landing page |
| `/register`, `/login`, `/logout` | Authentication |
| `/bites` | Browse/filter bites |
| `/bites/<slug>` | Bite detail + quiz |
| `/dashboard` | Personalized dashboard with recommendations |
| `/pricing`, `/checkout/<plan>` | Fake payment flow |
| `/certificates` | Generate/download PDF certificates |
| `/analytics` | Chart.js analytics dashboard |
| `/leaderboard` | XP leaderboard |
| `/admin` | Admin panel (admin users only) |

## Notes on the Fake Payment System

The checkout flow in `blueprints/payment.py` performs basic client-side-style validation (16-digit card number, CVV length, expiry format) and then "processes" a transaction by generating a random transaction ID and storing a `Payment` record. **No real payment gateway is integrated** — this is intentionally a simulation for demo/portfolio purposes.

## Notes on the Recommendation Engine

`recommend.py` implements a transparent, dependency-free scoring algorithm:
1. Builds a category-affinity score per user from completed bites and quiz performance.
2. Estimates the user's skill level from the difficulty of bites already completed.
3. Scores uncompleted bites using affinity + difficulty match + a popularity fallback for cold-start (new) users.
4. Returns the top N bites, backfilling with default-ordered bites if not enough candidates score well.

This keeps the project fully self-contained and runnable without external ML services or API keys.

## Running Tests

The project ships with a full `pytest` suite (`tests/`) covering auth, bites/quizzes, admin, payments, and analytics. Tests run against an isolated in-memory SQLite database (see `config.py: TestingConfig`) so no MySQL instance or `.env` file is needed to run them.

```bash
pip install -r requirements.txt
pytest                  # run the full suite
pytest -v                # verbose per-test output (already default via pytest.ini)
pytest tests/test_auth.py            # run a single test file
pytest -k "test_login"               # run tests matching a keyword
pytest --maxfail=1                   # stop on first failure
```

`tests/conftest.py` provides the `app`, `client`, and seeded-data fixtures shared across test modules. `TestingConfig` disables CSRF (`WTF_CSRF_ENABLED = False`) so form-posting tests don't need to manage tokens.

## Environment Variables

All variables are read in `config.py`. Copy `.env.example` to `.env` and adjust as needed:

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes (prod) | `change-this-to-a-random-secret-key` | Flask session signing key — set a unique random value in production |
| `FLASK_ENV` | No | `development` | `development` or `production`; controls debug behaviour |
| `DB_USER` | Yes* | `root` | MySQL username |
| `DB_PASSWORD` | Yes* | `password` | MySQL password |
| `DB_HOST` | Yes* | `localhost` | MySQL host |
| `DB_PORT` | Yes* | `3306` | MySQL port |
| `DB_NAME` | Yes* | `tarunsfxo_lms_db` | MySQL database name |
| `DATABASE_URL` | No | — | Full SQLAlchemy URL; overrides all `DB_*` vars above when set |
| `SUPABASE_DB_URL` | No | — | Alternate Postgres URL for Supabase; used when `DATABASE_URL` is not set |
| `SUPABASE_URL` | No | — | Optional Supabase project URL for client-side integration |
| `SUPABASE_ANON_KEY` | No | — | Optional public Supabase anon key for frontend use only |

\* Not required if `DATABASE_URL` is set directly, and not used at all when running the test suite (which always uses in-memory SQLite regardless of `.env`).

## Architecture Overview

tarunsfxo LMS follows the **Flask application-factory + blueprints** pattern:

- **`app.py`** — `create_app()` builds the Flask app, registers extensions (`db`, `login_manager`, `csrf`) from `extensions.py`, registers all blueprints, sets up error handlers (`404.html`/`500.html`), and exposes `flask init-db` / `flask seed-db` CLI commands.
- **`config.py`** — environment-driven `Config`, `DevelopmentConfig`, and `TestingConfig` classes; selects DB URL, secret key, pagination sizes, and gamification constants (XP per bite/quiz).
- **`extensions.py`** — single shared instances of `SQLAlchemy`, `LoginManager`, and `CSRFProtect`, imported by every blueprint/model to avoid circular imports.
- **`models.py`** — all SQLAlchemy ORM models (`User`, `Category`, `Bite`, `QuizQuestion`, `Progress`, `QuizAttempt`, `Certificate`, `Payment`) plus small domain helper methods (`User.level()`, `User.completed_bite_ids()`, `User.update_streak()`).
- **`blueprints/`** — one blueprint per feature area (`auth`, `main`, `payment`, `certificate`, `analytics`, `admin`); each owns its own routes and keeps view logic thin, delegating business logic to `recommend.py` / `certificates.py` where appropriate.
- **`recommend.py`** — pure-function recommendation engine, decoupled from Flask request context except for the `User`/`Bite` ORM objects it's given, which keeps it independently testable and cheap to call from multiple views.
- **`certificates.py`** — ReportLab PDF generation, isolated from the certificate *routes* in `blueprints/certificate.py` so the rendering logic can be unit-tested without HTTP.
- **`templates/`** — server-rendered Jinja2, `base.html` as the shared layout, `templates/admin/` as a parallel namespace with its own `base_admin.html`.
- **`static/js/`** — small, dependency-free vanilla JS modules (`main.js` for shared helpers like CSRF-aware fetch wrappers, `bite.js` for quiz/completion interactions, `analytics.js` for Chart.js rendering) — no build step required.
- **`tests/`** — one file per feature area, mirroring the `blueprints/` structure, plus `conftest.py` for shared fixtures.

Request flow for a typical authenticated page (e.g. `/dashboard`): `app.py` routes the request via the `main` blueprint → `blueprints/main.py:dashboard()` queries `models.py` ORM objects → calls `recommend.py:recommend_bites()` for personalized suggestions → renders `templates/dashboard.html`.

## License

This project is provided as a learning/demo template. Feel free to adapt it for your own portfolio or coursework.

## Production Deployment

tarunsfxo LMS ships with a dedicated production entrypoint and process file:

- **`wsgi.py`** — forces the `production` config regardless of `FLASK_ENV`, so it's safe to point any WSGI server at it directly.
- **`Procfile`** — `web: gunicorn -w 4 -b 0.0.0.0:$PORT wsgi:app`, ready for Heroku/Render-style platforms.
- `gunicorn` is included in `requirements.txt`.

To run in production locally:

```bash
export FLASK_ENV=production
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export SESSION_COOKIE_SECURE=true   # only when served over HTTPS
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

Notes:
- `create_app("production")` **refuses to start** if `SECRET_KEY` is left at its insecure default — you must set a unique value.
- Session/remember cookies are always `HttpOnly` + `SameSite=Lax`; set `SESSION_COOKIE_SECURE=true` once the app is served over HTTPS (it also enables `Strict-Transport-Security`).
- A small `after_request` hook adds `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` headers on every response.
- `ProxyFix` is applied automatically in production so `X-Forwarded-For`/`-Proto`/`-Host` headers from a reverse proxy (nginx, a PaaS load balancer, etc.) are honored.
- Warnings and errors are written to `logs/tarunsfxo_lms.log` (rotating, 5 × 1 MB) when running in production without `DEBUG`.
- `config.py` auto-loads a `.env` file via `python-dotenv` if present — useful for local production-mode testing without exporting every variable manually.
