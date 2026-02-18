# ida

This repository now contains the first implementation step for the Android-first safety platform:

- Product plan: `docs/app-plan.md`
- Backend API prototype: `backend/`

## Quick start (backend prototype)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Current API endpoints

- `GET /health`
- `POST /v1/reports`
- `GET /v1/reports`
- `GET /v1/reports/{report_id}`
- `GET /v1/alerts`
- `POST /v1/subscriptions`
- `GET /v1/subscriptions/{subscription_id}/alerts`

> Note: this is an in-memory prototype to start development. It now includes a basic area subscription mechanism for danger notifications. Next step is persistent storage (PostgreSQL/PostGIS), auth, encryption-at-rest, and moderation workflows.
