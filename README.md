# astro-content-agent (staging scaffold)

This staged folder is a conservative extraction scaffold for splitting the Astro Content Agent out of the Money Compass repository.

It is intentionally additive and reversible: nothing is moved or deleted from the current repo.

## Intended standalone root layout

- `astro_content_agent/` (package, API, services, repos, schemas, tests)
- `scripts/aca/` (ops/validation/seed scripts)
- `assets/aca_e2e/` (sample test image fixture)
- `astro_content_agent.db` (local sqlite runtime DB; optional, can be recreated)
- `.env` (local runtime config; copy from `.env.example`)
- `README.md`
- `requirements.txt`
- `run.ps1`

## What to copy into the standalone repo

From current Money Compass repo:

- `backend/astro_content_agent/**`
- `backend/scripts/aca/**`
- `backend/assets/aca_e2e/**`
- `backend/astro_content_agent.db` (optional seed DB snapshot)

## Quick start (standalone)

1. `cd astro-content-agent`
2. `python -m venv .venv`
3. `.venv\Scripts\activate` (PowerShell: `.\.venv\Scripts\Activate.ps1`)
4. `pip install -r requirements.txt`
5. `Copy-Item .env.example .env`
6. `python -m uvicorn astro_content_agent.main:app --reload --host 127.0.0.1 --port 8000`
7. Health checks:
   - `http://127.0.0.1:8000/health`
   - `http://127.0.0.1:8000/api/v1/health`

## Verify suite (standalone)

- `python -m pytest -q astro_content_agent/tests`
- `python scripts/aca/seed_brand_profile.py`
- `python scripts/aca/generate_today.py`
