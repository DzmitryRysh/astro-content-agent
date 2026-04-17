from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.api.routes import drafts as drafts_routes
from astro_content_agent.api.routes import strategy as strategy_routes
from astro_content_agent.db.models import Draft
from astro_content_agent.db.session import get_db
from astro_content_agent.main import create_app
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.services.media.storage import LocalFileStorage
from astro_content_agent.tests.fakes.fake_openai import FakeOpenAIClient, default_responder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ai_runner() -> ResponsesRunner:
    prompts_root = Path(__file__).resolve().parents[1] / "services" / "ai" / "prompts"
    return ResponsesRunner(model="test", client=FakeOpenAIClient(default_responder), prompts_root=prompts_root)


@pytest.fixture()
def client_p4(db_session: Session, ai_runner: ResponsesRunner, tmp_path: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[strategy_routes.get_runner] = lambda: ai_runner
    app.dependency_overrides[drafts_routes.get_runner] = lambda: ai_runner
    app.dependency_overrides[drafts_routes.get_storage] = lambda: LocalFileStorage(
        assets_dir=tmp_path / "assets",
        public_base_url="http://testserver",
    )
    return TestClient(app)


def _make_draft(db: Session, brand_profile_id: str, draft_type: str = "post") -> Draft:
    """Helper: insert a minimal draft directly into the DB."""
    repo = DraftRepository()
    d = repo.create(
        db,
        brand_profile_id=brand_profile_id,
        content_plan_id=None,
        draft_type=draft_type,
        text="test caption",
        payload={"title": "T", "hook": "H", "caption": "C", "cta": "CTA", "hashtags": [], "metadata": {}},
    )
    db.commit()
    db.refresh(d)
    return d


# ---------------------------------------------------------------------------
# List / detail
# ---------------------------------------------------------------------------


def test_list_drafts_empty(client_p4: TestClient) -> None:
    resp = client_p4.get("/api/v1/drafts")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["total"] == 0


def test_list_drafts_with_filter(client_p4: TestClient, brand_profile, db_session: Session) -> None:
    _make_draft(db_session, brand_profile.id, "post")
    _make_draft(db_session, brand_profile.id, "reel")

    resp = client_p4.get(f"/api/v1/drafts?brand_profile_id={brand_profile.id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    resp2 = client_p4.get(f"/api/v1/drafts?brand_profile_id={brand_profile.id}&draft_type=post")
    assert resp2.json()["total"] == 1
    assert resp2.json()["items"][0]["draft_type"] == "post"


def test_get_draft_found(client_p4: TestClient, brand_profile, db_session: Session) -> None:
    d = _make_draft(db_session, brand_profile.id)
    resp = client_p4.get(f"/api/v1/drafts/{d.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == d.id
    assert body["status"] == "draft"
    assert body["payload"] is not None


def test_get_draft_not_found(client_p4: TestClient) -> None:
    resp = client_p4.get("/api/v1/drafts/does-not-exist")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Approval / rejection
# ---------------------------------------------------------------------------


def test_approve_draft(client_p4: TestClient, brand_profile, db_session: Session) -> None:
    d = _make_draft(db_session, brand_profile.id)
    resp = client_p4.post(f"/api/v1/drafts/{d.id}/approve")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["approved_at"] is not None


def test_approve_already_approved_returns_409(client_p4: TestClient, brand_profile, db_session: Session) -> None:
    d = _make_draft(db_session, brand_profile.id)
    client_p4.post(f"/api/v1/drafts/{d.id}/approve")
    resp2 = client_p4.post(f"/api/v1/drafts/{d.id}/approve")
    assert resp2.status_code == 409


def test_reject_draft_with_reason(client_p4: TestClient, brand_profile, db_session: Session) -> None:
    d = _make_draft(db_session, brand_profile.id)
    resp = client_p4.post(
        f"/api/v1/drafts/{d.id}/reject",
        json={"reason": "tone is too casual for this brand"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected"
    assert "casual" in body["rejection_reason"]


def test_reject_approved_draft_returns_409(client_p4: TestClient, brand_profile, db_session: Session) -> None:
    d = _make_draft(db_session, brand_profile.id)
    client_p4.post(f"/api/v1/drafts/{d.id}/approve")
    resp2 = client_p4.post(f"/api/v1/drafts/{d.id}/reject", json={"reason": "late"})
    assert resp2.status_code == 409


# ---------------------------------------------------------------------------
# Regenerate
# ---------------------------------------------------------------------------


def test_regenerate_post_draft_creates_new_draft(
    client_p4: TestClient, brand_profile, db_session: Session
) -> None:
    original = _make_draft(db_session, brand_profile.id, "post")
    resp = client_p4.post(
        f"/api/v1/drafts/{original.id}/regenerate",
        json={"day": "2026-04-03"},
    )
    assert resp.status_code == 200
    new_id = resp.json()["id"]
    assert new_id != original.id
    assert resp.json()["draft_type"] == "post"
    assert resp.json()["status"] == "draft"


def test_regenerate_reel_draft(client_p4: TestClient, brand_profile, db_session: Session) -> None:
    original = _make_draft(db_session, brand_profile.id, "reel")
    resp = client_p4.post(
        f"/api/v1/drafts/{original.id}/regenerate",
        json={"day": "2026-04-03"},
    )
    assert resp.status_code == 200
    assert resp.json()["draft_type"] == "reel"


def test_regenerate_carousel_returns_400(client_p4: TestClient, brand_profile, db_session: Session) -> None:
    original = _make_draft(db_session, brand_profile.id, "carousel")
    resp = client_p4.post(
        f"/api/v1/drafts/{original.id}/regenerate",
        json={"day": "2026-04-03"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Image generation (placeholder)
# ---------------------------------------------------------------------------


def test_generate_image_creates_asset_and_file(
    client_p4: TestClient, brand_profile, db_session: Session, tmp_path: Path
) -> None:
    d = _make_draft(db_session, brand_profile.id)
    resp = client_p4.post(f"/api/v1/drafts/{d.id}/generate-image")
    assert resp.status_code == 200
    body = resp.json()
    assert body["draft_id"] == d.id
    assert body["asset_type"] == "image"
    assert body["width"] == 1080
    # storage_path is now a relative key, not an absolute path
    assert not Path(body["storage_path"]).is_absolute()
    # public_url is a fully-qualified URL built from PUBLIC_BASE_URL + /media/ + key
    assert body["public_url"] is not None
    assert body["public_url"].startswith("http://testserver/media/")
    # file must exist on disk at assets_dir / storage_key
    assert (tmp_path / "assets" / body["storage_path"]).exists()
