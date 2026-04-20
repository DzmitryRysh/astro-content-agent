# Publish readiness and dry-run (no Meta call)

Use these while **Meta/Facebook developer access** or **public asset URLs** are still pending. Nothing here performs a real Instagram publish.

For a **single operator payload** (copy + image URL + readiness + dry-run), see [REVIEW_FLOW.md](./REVIEW_FLOW.md).

## Environment variables (visibility)

| Variable | Role |
|----------|------|
| `INSTAGRAM_ACCESS_TOKEN` | Server-wide Graph API token; required for `POST /api/v1/publish/{draft_id}` (real publish). |
| `INSTAGRAM_IG_USER_ID` | Optional env hint; each publish job uses `instagram_accounts.ig_user_id` from the database. |
| `PUBLIC_BASE_URL` | Base for `/media/...` asset URLs; Instagram must reach this host (not localhost in production). |
| `ASSETS_DIR` | Local storage root when `STORAGE_MODE=local`. |
| `STORAGE_MODE` | Expected `local` for this standalone build. |

## HTTP checks (from repo root, server running)

1. **Global diagnostics** (admin key if configured):  
   `GET /api/v1/admin/diagnostics`  
   Includes OpenAI, storage, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_IG_USER_ID`, DB Instagram rows, asset URL sample, `ASSETS_DIR`.

2. **Per-draft readiness** (admin):  
   `GET /api/v1/admin/publish-readiness/{draft_id}`  
   Optional query: `instagram_account_id=<uuid>` to validate the account row (`ig_user_id`, active).  
   Optional: `simulate=true` to include `image_url` and caption excerpt (same as dry-run body below).

3. **Dry-run publish** (no admin key, **no** `INSTAGRAM_ACCESS_TOKEN` required):  
   `POST /api/v1/publish/{draft_id}/dry-run`  
   JSON: `{"instagram_account_id":"<uuid>"}`  
   Response: `PublishReadinessReport` with `checks`, `ready`, and `simulation` (Graph payload preview).

## PowerShell examples

```powershell
# Diagnostics (set X-Admin-Key if ADMIN_API_KEY is set)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/admin/diagnostics" -Headers @{ "X-Admin-Key" = $env:ADMIN_API_KEY }

# Dry-run (replace ids)
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/v1/publish/<draft_id>/dry-run" -ContentType "application/json" -Body '{"instagram_account_id":"<account_uuid>"}'
```

## Real publish

When Meta is ready: set `INSTAGRAM_ACCESS_TOKEN`, ensure `PUBLIC_BASE_URL` is publicly reachable, then `POST /api/v1/publish/{draft_id}` as today.
