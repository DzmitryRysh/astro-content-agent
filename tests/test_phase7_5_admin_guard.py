from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.session import get_db
from astro_content_agent.main import create_app


def _fake_settings(admin_api_key: str | None):
    """Return a minimal settings-like object with the given admin_api_key."""
    s = MagicMock()
    s.admin_api_key = admin_api_key
    return s


def _client_with_key(db_session: Session, configured_key: str | None) -> TestClient:
    """Build a TestClient with ADMIN_API_KEY wired to configured_key."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: _fake_settings(configured_key)
    return TestClient(app)


VALID_PAYLOAD = {"name": "Guard Test Brand"}


# ---------------------------------------------------------------------------
# Guard disabled (no key configured) — default local dev behaviour
# ---------------------------------------------------------------------------


def test_admin_open_when_no_key_configured(client: TestClient) -> None:
    """When ADMIN_API_KEY is not set, all admin requests pass without a header."""
    resp = client.get("/api/v1/admin/brand-profile")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Guard enabled — missing header → 401
# ---------------------------------------------------------------------------


def test_admin_missing_header_returns_401(db_session: Session) -> None:
    c = _client_with_key(db_session, "secret-key")
    resp = c.get("/api/v1/admin/brand-profile")
    assert resp.status_code == 401
    assert "X-Admin-Key" in resp.json()["detail"]


def test_admin_missing_header_on_post_returns_401(db_session: Session) -> None:
    c = _client_with_key(db_session, "secret-key")
    resp = c.post("/api/v1/admin/brand-profile", json=VALID_PAYLOAD)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Guard enabled — wrong key → 403
# ---------------------------------------------------------------------------


def test_admin_wrong_key_returns_403(db_session: Session) -> None:
    c = _client_with_key(db_session, "secret-key")
    resp = c.get("/api/v1/admin/brand-profile", headers={"X-Admin-Key": "wrong-key"})
    assert resp.status_code == 403
    assert "Invalid" in resp.json()["detail"]


def test_admin_wrong_key_on_post_returns_403(db_session: Session) -> None:
    c = _client_with_key(db_session, "secret-key")
    resp = c.post(
        "/api/v1/admin/brand-profile",
        json=VALID_PAYLOAD,
        headers={"X-Admin-Key": "not-right"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Guard enabled — correct key → passes
# ---------------------------------------------------------------------------


def test_admin_correct_key_allows_get(db_session: Session) -> None:
    c = _client_with_key(db_session, "secret-key")
    resp = c.get("/api/v1/admin/brand-profile", headers={"X-Admin-Key": "secret-key"})
    assert resp.status_code == 200


def test_admin_correct_key_allows_create(db_session: Session) -> None:
    c = _client_with_key(db_session, "secret-key")
    resp = c.post(
        "/api/v1/admin/brand-profile",
        json=VALID_PAYLOAD,
        headers={"X-Admin-Key": "secret-key"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Guard Test Brand"


def test_admin_correct_key_allows_content_pillars(db_session: Session) -> None:
    c = _client_with_key(db_session, "my-key")
    bp = c.post(
        "/api/v1/admin/brand-profile",
        json={"name": "Pillar Brand"},
        headers={"X-Admin-Key": "my-key"},
    ).json()
    bp_id = bp["id"]

    resp = c.post(
        "/api/v1/admin/content-pillars",
        json={
            "brand_profile_id": bp_id,
            "pillars": [{"brand_profile_id": bp_id, "name": "Pillar 1"}],
        },
        headers={"X-Admin-Key": "my-key"},
    )
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Unit: guard dependency logic in isolation
# ---------------------------------------------------------------------------


def test_guard_passes_when_no_key_configured() -> None:
    from fastapi import HTTPException
    from astro_content_agent.core.admin_guard import require_admin_key

    settings = _fake_settings(None)
    # Should not raise
    require_admin_key(x_admin_key=None, settings=settings)


def test_guard_passes_when_empty_key_configured() -> None:
    from astro_content_agent.core.admin_guard import require_admin_key

    settings = _fake_settings("")
    require_admin_key(x_admin_key=None, settings=settings)


def test_guard_raises_401_on_missing_header() -> None:
    from fastapi import HTTPException
    from astro_content_agent.core.admin_guard import require_admin_key

    settings = _fake_settings("real-key")
    with pytest.raises(HTTPException) as exc_info:
        require_admin_key(x_admin_key=None, settings=settings)
    assert exc_info.value.status_code == 401


def test_guard_raises_403_on_wrong_key() -> None:
    from fastapi import HTTPException
    from astro_content_agent.core.admin_guard import require_admin_key

    settings = _fake_settings("real-key")
    with pytest.raises(HTTPException) as exc_info:
        require_admin_key(x_admin_key="wrong-key", settings=settings)
    assert exc_info.value.status_code == 403


def test_guard_passes_on_correct_key() -> None:
    from astro_content_agent.core.admin_guard import require_admin_key

    settings = _fake_settings("real-key")
    # Should not raise
    require_admin_key(x_admin_key="real-key", settings=settings)
