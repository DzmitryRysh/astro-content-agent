# Operator review / approval flow (v1)

Use this flow to review generated copy, approve or reject, and see publish readiness (including dry-run preview) before any live Instagram call.

## 0. Browser console (no Postman)

With the API running (e.g. `uvicorn astro_content_agent.main:app`), open:

**`/operator/review`** (e.g. `http://127.0.0.1:8000/operator/review`)

Enter draft id, optional `X-Admin-Key` and Instagram account id, then **Load review**. Approve / reject call the same JSON APIs as below.

## 1. Review surface (single GET)

Returns hook, caption, CTA, hashtags, primary image public URL and storage key, approval fields, full publish readiness checks, dry-run simulation (same as `POST .../dry-run`), and resolved action paths.

```http
GET /api/v1/admin/drafts/{draft_id}/review
GET /api/v1/admin/drafts/{draft_id}/review?instagram_account_id={uuid}
```

- Optional `instagram_account_id`: validates the Instagram account row and fills `dry_run.ig_user_id` when present.
- If `ADMIN_API_KEY` is set, send header `X-Admin-Key`.

## 2. Approve or reject (unchanged public routes)

```http
POST /api/v1/drafts/{draft_id}/approve
POST /api/v1/drafts/{draft_id}/reject
Content-Type: application/json

{"reason": "…"}   # required for reject
```

Re-fetch the review surface after approve to see updated `status` and readiness.

## 3. Extra checks (optional)

- `GET /api/v1/admin/diagnostics` — environment and storage.
- `POST /api/v1/publish/{draft_id}/dry-run` — same simulation without admin key; body `{"instagram_account_id":"…"}`.

See [PUBLISH_READINESS.md](./PUBLISH_READINESS.md) for env vars and dry-run details.
