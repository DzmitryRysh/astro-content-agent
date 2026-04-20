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
    - ``APP_ENV`` in ``("local", "dev")`` and ``ADMIN_API_KEY`` unset/empty:
      guard disabled — requests pass without header (local developer default).
    - ``APP_ENV`` in ``("staging", "prod")`` with ``ADMIN_API_KEY`` unset/empty:
      admin routes are disabled → 503 until a key is configured (fail closed).
    - ``ADMIN_API_KEY`` configured (any ``APP_ENV``):
        - Missing header  → 401 Unauthorized
        - Wrong key value → 403 Forbidden
        - Correct key     → passes
    """
    configured_key = (settings.admin_api_key or "").strip() or None
    relaxed_env = settings.app_env in ("local", "dev")

    if not configured_key:
        if relaxed_env:
            return
        raise HTTPException(
            status_code=503,
            detail=(
                f"Admin routes are disabled: set ADMIN_API_KEY when APP_ENV is '{settings.app_env}'. "
                "Refusing open admin access outside local/dev."
            ),
        )

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
