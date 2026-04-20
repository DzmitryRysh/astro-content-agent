# astro-content-agent

Standalone **Astro Content Agent**: a FastAPI backend for content generation (posts/reels), draft lifecycle, diagnostics, publish readiness, dry-run publish checks, and optional Instagram publishing when external prerequisites are met.

## Operator workflow (high level)

1. **Generate** — create drafts (e.g. `POST /api/v1/drafts/generate-post`, strategy/astro routes as needed).
2. **Review** — inspect copy and media; approve or reject drafts.
3. **Readiness / dry-run** — validate configuration and publish preconditions without calling Meta (`GET /api/v1/admin/diagnostics`, `GET /api/v1/admin/publish-readiness/{draft_id}`, `POST /api/v1/publish/{draft_id}/dry-run`).
4. **Publish (optional)** — real Instagram publish only when tokens, `PUBLIC_BASE_URL`, and Meta access are ready (`POST /api/v1/publish/{draft_id}`, etc.).

Browser console for the same review/readiness/approve/reject flow: **`/operator/review`** (see [scripts/aca/REVIEW_FLOW.md](scripts/aca/REVIEW_FLOW.md)).

## Repository layout

| Path | Purpose |
|------|---------|
| `astro_content_agent/` | Python package: API routes, services, DB, repositories, schemas, tests, static operator UI assets |
| `scripts/aca/` | Operator docs (`REVIEW_FLOW.md`, `PUBLISH_READINESS.md`) and `README.md` for script/output policy |
| `assets/` | Local media root when `STORAGE_MODE=local` (served under `/media/...`) |
| `requirements.txt` | Python dependencies |
| `run.ps1` | Windows: create venv if needed, install deps, copy `.env` if missing, start uvicorn |
| `.env.example` | Environment template (copy to `.env`) |
| `.gitignore` | Ignores `.env`, `*.db`, caches, `.venv`, operator output dirs under `scripts/aca/` |

Runtime SQLite (`astro_content_agent.db`) is created according to `DATABASE_URL` when the app runs; it is gitignored by default.

## Local startup

**Option A — PowerShell (`run.ps1` from repo root):**

```powershell
.\run.ps1
```

**Option B — manual:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # if you do not already have .env
python -m uvicorn astro_content_agent.main:app --reload --host 127.0.0.1 --port 8000
```

**Health:**

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/v1/health`

## Main API and operator surfaces

| Surface | Path / pattern | Notes |
|--------|----------------|--------|
| Health | `GET /health`, `GET /api/v1/health` | Liveness |
| Drafts | `GET /api/v1/drafts`, `GET /api/v1/drafts/{draft_id}` | List / detail |
| Approve / reject | `POST /api/v1/drafts/{draft_id}/approve`, `POST /api/v1/drafts/{draft_id}/reject` | Body required for reject: `{"reason":"..."}` |
| Admin diagnostics | `GET /api/v1/admin/diagnostics` | `APP_ENV` `local`\|`dev`: open if `ADMIN_API_KEY` unset; otherwise `X-Admin-Key` required. `staging`\|`prod`: unset key → **503** (admin disabled). |
| Publish readiness (draft) | `GET /api/v1/admin/publish-readiness/{draft_id}` | Same admin rules as diagnostics |
| Publish dry-run | `POST /api/v1/publish/{draft_id}/dry-run` | JSON `{"instagram_account_id":"<uuid>"}` — no Meta call; **not** an admin route |
| Operator review (single JSON) | `GET /api/v1/admin/drafts/{draft_id}/review` | Same admin rules as diagnostics |
| Review console (static UI) | `GET /operator/review` | Mounted only for `APP_ENV` `local`\|`dev`, **or** when `ADMIN_API_KEY` is set (so staging/prod can opt in) |

Full publish and job/history routes live under `GET|POST /api/v1/publish/...` (see OpenAPI at `/docs` when the server is running).

## Environment / configuration

Copy `.env.example` to `.env` and adjust:

| Area | Variables (examples) | Purpose |
|------|----------------------|---------|
| Core | `APP_ENV`, `LOG_LEVEL`, `DATABASE_URL` | Runtime mode and database |
| AI | `OPENAI_API_KEY`, `OPENAI_MODEL` | Generation (optional in strict local flows that mock AI in tests) |
| Media | `ASSETS_DIR`, `STORAGE_MODE`, `PUBLIC_BASE_URL` | Local files and public URLs for `/media/...` |
| Admin | `ADMIN_API_KEY`, `APP_ENV` | `local`\|`dev` + empty key → admin open; `staging`\|`prod` + empty key → admin **503**; non-empty key → `X-Admin-Key` required |
| Instagram | `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_IG_USER_ID` | Token used for Graph calls; per-job `instagram_accounts.ig_user_id` still required in DB — see [PUBLISH_READINESS.md](scripts/aca/PUBLISH_READINESS.md) |
| Scheduler | `SCHEDULER_ENABLED`, timezone/hour settings | Background jobs when enabled |

**Real Instagram publish** still depends on Meta app approval, valid tokens, a **publicly reachable** `PUBLIC_BASE_URL` (not localhost for production), and correct DB rows. Dry-run and readiness endpoints are intended to surface blockers before any live publish.

## Testing

```powershell
python -m pytest -q
```

The suite under `astro_content_agent/tests` covers API routes, services, diagnostics, publish/dry-run paths, drafts, strategy/astro flows, and operator review helpers — largely with in-memory SQLite and mocked external AI/Instagram where appropriate. Run from the **repository root** so imports resolve.

## Further reading

- [scripts/aca/REVIEW_FLOW.md](scripts/aca/REVIEW_FLOW.md) — review surface, approve/reject, console URL, optional admin/dry-run calls  
- [scripts/aca/PUBLISH_READINESS.md](scripts/aca/PUBLISH_READINESS.md) — environment checks, dry-run, PowerShell examples  
- [scripts/aca/README.md](scripts/aca/README.md) — gitignored operator output directories under `scripts/aca/`
