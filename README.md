# Airbnb Cleaning & Maintenance Micro‑SaaS (MVP)

A FastAPI + SQLite MVP connecting Airbnb hosts with vetted cleaners and maintenance providers. Supports scheduling by bookings, standardized checklists, photo evidence, and host ratings. Built to minimize turnover friction and protect 5‑star cleanliness.

## Quick Start
- Create venv and install deps:
  - `python3 -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Init DB (auto on first run). Create media folder (auto):
  - `mkdir -p media`
- Run dev server:
  - `uvicorn app.main:app --reload`

## Project Structure
- `app/main.py` – FastAPI app, routers, startup tasks
- `app/database.py` – SQLAlchemy engine, SessionLocal, Base
- `app/models.py` – SQLAlchemy models (Users, Hosts, Cleaners, Properties, CleaningJobs, ChecklistItems, Ratings)
- `app/schemas.py` – Pydantic request/response models
- `app/routers/jobs.py` – Job creation/claiming/checklists/photos/ratings
- `app/routers/auth.py` – Registration/login, simple token auth (Bearer)
- `app/services/scheduler.py` – Async reminder stubs (no external APIs)
- `app/services/pms_stub.py` – `get_upcoming_bookings` mocked function

## Authentication
- Register: `POST /auth/register` (email, password, role: host|cleaner|admin)
- Login: `POST /auth/login` → returns token
- Use token: `Authorization: Bearer <token>`

## Notes & Integrations (stubs)
- External PMS (Airbnb/PMS), smart‑lock access codes, and payments are stubbed in services/* with clear TODOs.
- Background reminders use an asyncio queue stub; replace with Celery or a hosted queue in production.

## Testing
- Explore docs: GET `/docs`
- Create a Host, a Property, schedule a job for a mocked booking, claim as Cleaner, tick checklist, upload photos, and submit a rating.
