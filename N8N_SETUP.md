# Tarunsfxo LMS — n8n Automation Engine Setup Guide

This document describes how to launch and configure the n8n automation and Redis queuing system.

## Requirements
* Docker & Docker Compose
* Python 3.x
* Redis (handled automatically by Docker Compose for local environments)

---

## 1. Setup Local Infrastructure

Start n8n and Redis containers using the provided Docker Compose file:

```bash
docker-compose -f docker-compose.n8n.yml up -d
```

Verify that both containers are running:
* **n8n UI**: [http://localhost:5678](http://localhost:5678)
* **Redis**: Port `6379` (local listener)

---

## 2. Configuration Setup

Copy the environment parameters from `.env.n8n` into your system environment or append them to your primary `.env` file:

```bash
cat .env.n8n >> .env
```

Ensure `REDIS_URL`, `N8N_WEBHOOK_SECRET`, and `N8N_BASE_URL` match your development or production setup.

---

## 3. Install Dependencies & Database Migrations

Install the new Python packages required by the queuing and signaling layers:

```bash
pip install -r requirements.txt
```

Run database migrations to initialize the new logging, analytics, and study planning tables:

```bash
flask db init      # If migrations folder is not initialized yet
flask db migrate -m "add automation tables"
flask db upgrade
```

---

## 4. Run background worker

To process the Redis Queue asynchronous triggers in the background, run the worker process in a separate terminal:

```bash
python worker.py
```

This worker listens on the `automation` Redis channel, captures `automation.trigger.fire()` events, and forwards them to n8n.

---

## 5. Webhook Authorization Security

All webhook endpoints under `/n8n/webhook/*` are secured using a header verification mechanism. Make sure the header `X-Webhook-Secret` sent by n8n HTTP Request nodes matches the `N8N_WEBHOOK_SECRET` environment variable defined in your Flask backend.
