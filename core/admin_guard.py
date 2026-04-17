from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from astro_content_agent.core.config import Settings, get_settings

_header_scheme = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin_key(
    x_admin_key: str | None = Security(_header_scheme),
    settings: Settings = Depends(get_settings),
) -> None:
    """Dependency that enforces the ADMIN_API_KEY header on admin routes.

    Behavior:
    - If ADMIN_API_KEY is not configured (None/empty), the guard is disabled
      and all requests pass. This keeps local development friction-free.
    - If ADMIN_API_KEY is configured:
        - Missing header  → 401 Unauthorized
        - Wrong key value → 403 Forbidden
        - Correct key     → passes
    """
    configured_key = settings.admin_api_key

    if not configured_key:
        # Guard disabled — open access (local dev default).
        return

    if x_admin_key is None:
        raise HTTPException(
            status_code=401,
            detail="X-Admin-Key header is required for admin endpoints.",
        )

    if x_admin_key != configured_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid X-Admin-Key.",
        )
