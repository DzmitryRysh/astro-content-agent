from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.db.models import AstroSignal


def test_calculate_day_persists_and_returns_payload(client: TestClient, brand_profile, db_session: Session) -> None:
    day = date(2026, 4, 3)
    resp = client.post(
        "/api/v1/astro/calculate-day",
        json={"brand_profile_id": brand_profile.id, "day": day.isoformat()},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["brand_profile_id"] == brand_profile.id
    assert body["signal_date"] == day.isoformat()
    assert body["engine_version"] == "v1.real"
    assert body["payload"]["day"] == day.isoformat()
    assert 1 <= len(body["payload"]["signals"]) <= 5

    rec = db_session.get(AstroSignal, body["id"])
    assert rec is not None
    assert rec.signal_date == day.isoformat()


def test_get_today_generates_when_missing(client: TestClient, brand_profile) -> None:
    resp = client.get(f"/api/v1/astro/today?brand_profile_id={brand_profile.id}&day=2026-04-03")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["signal_date"] == "2026-04-03"


def test_get_today_404_when_missing_and_generate_disabled(client: TestClient, brand_profile) -> None:
    resp = client.get(
        f"/api/v1/astro/today?brand_profile_id={brand_profile.id}&day=2026-04-04&generate_if_missing=false"
    )
    assert resp.status_code == 404


def test_astro_404_when_brand_profile_missing(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/astro/calculate-day",
        json={"brand_profile_id": "missing-brand", "day": "2026-04-03"},
    )
    assert resp.status_code == 404

