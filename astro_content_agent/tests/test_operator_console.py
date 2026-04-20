from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.session import get_db
from astro_content_agent.main import create_app


def test_operator_review_console_serves_html() -> None:
    client = TestClient(create_app())
    r = client.get("/operator/review")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert b"Operator Review Console" in r.content


def test_operator_review_console_static_css() -> None:
    client = TestClient(create_app())
    r = client.get("/operator/review/static/console.css")
    assert r.status_code == 200
    assert b"--bg" in r.content


def test_operator_review_console_static_js() -> None:
    client = TestClient(create_app())
    r = client.get("/operator/review/static/console.js")
    assert r.status_code == 200
    assert b"loadReview" in r.content


def test_staging_without_admin_key_disables_admin_and_console(
    monkeypatch: pytest.MonkeyPatch, db_session: Session
) -> None:
    """Fail closed outside local/dev when no ADMIN_API_KEY; do not mount operator HTML."""
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("ADMIN_API_KEY", "")
    get_settings.cache_clear()
    try:
        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)
        assert client.get("/api/v1/admin/diagnostics").status_code == 503
        assert client.get("/operator/review").status_code == 404
    finally:
        get_settings.cache_clear()
