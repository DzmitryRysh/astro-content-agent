from __future__ import annotations

from astro_content_agent.main import create_app
from fastapi.testclient import TestClient


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
