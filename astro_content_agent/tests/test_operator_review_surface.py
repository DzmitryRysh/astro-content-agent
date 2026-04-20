from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.core.config import Settings, get_settings
from astro_content_agent.db.models import Draft, InstagramAccount
from astro_content_agent.db.session import get_db
from astro_content_agent.main import create_app
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.services.drafts.review_surface import build_draft_operator_review


def _make_post_draft(db: Session, brand_profile_id: str, *, status: str = "draft") -> Draft:
    repo = DraftRepository()
    d = repo.create(
        db,
        brand_profile_id=brand_profile_id,
        content_plan_id=None,
        draft_type="post",
        text="legacy text",
        payload={
            "title": "My Title",
            "hook": "Stop scrolling",
            "caption": "Body copy here.",
            "cta": "Follow for more",
            "hashtags": ["#one", "#two"],
            "metadata": {},
        },
    )
    db.commit()
    db.refresh(d)
    if status == "approved":
        repo.approve(db, d)
        db.commit()
        db.refresh(d)
    return d


def _attach_asset(db: Session, draft: Draft, key: str = "bp/d/x.png") -> None:
    AssetRepository().create(
        db,
        brand_profile_id=draft.brand_profile_id,
        draft_id=draft.id,
        asset_type="image",
        storage_path=key,
        mime_type="image/png",
        width=1080,
        height=1080,
    )
    db.commit()


def _make_ig(db: Session) -> InstagramAccount:
    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Op Test",
        ig_user_id="17841400000000000",
        access_token="tok",
        is_active=1,
    )
    db.add(acc)
    db.commit()
    return acc


@pytest.fixture()
def client_review(db_session: Session, tmp_path: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    fake = Settings(
        _env_file=None,
        SCHEDULER_ENABLED=False,
        APP_ENV="local",
        OPENAI_API_KEY="sk-test",
        PUBLIC_BASE_URL="https://review.example.com",
        STORAGE_MODE="local",
        ASSETS_DIR=str(tmp_path / "assets"),
        INSTAGRAM_ACCESS_TOKEN="dummy-token",
    )
    app.dependency_overrides[get_settings] = lambda: fake
    return TestClient(app)


def test_build_review_returns_none_for_missing_draft(db_session: Session, tmp_path: Path) -> None:
    s = Settings(
        _env_file=None,
        SCHEDULER_ENABLED=False,
        APP_ENV="local",
        OPENAI_API_KEY="sk",
        PUBLIC_BASE_URL="https://x.com",
        ASSETS_DIR=str(tmp_path / "a"),
        INSTAGRAM_ACCESS_TOKEN="t",
    )
    assert build_draft_operator_review(db_session, draft_id="missing", settings=s) is None


def test_build_review_extracts_post_fields(db_session: Session, brand_profile, tmp_path: Path) -> None:
    draft = _make_post_draft(db_session, brand_profile.id, status="approved")
    _attach_asset(db_session, draft)
    s = Settings(
        _env_file=None,
        SCHEDULER_ENABLED=False,
        APP_ENV="local",
        OPENAI_API_KEY="sk",
        PUBLIC_BASE_URL="https://x.com",
        ASSETS_DIR=str(tmp_path / "a"),
        INSTAGRAM_ACCESS_TOKEN="t",
    )
    body = build_draft_operator_review(db_session, draft_id=draft.id, settings=s)
    assert body is not None
    assert body.hook == "Stop scrolling"
    assert body.caption == "Body copy here."
    assert body.cta == "Follow for more"
    assert body.title == "My Title"
    assert "#one" in body.hashtags_preview
    assert body.primary_asset_storage_key == "bp/d/x.png"
    assert body.primary_image_public_url.startswith("https://x.com/media/")
    assert body.publish_readiness_ready is True
    assert body.dry_run is not None
    assert "/media/" in body.dry_run.image_url


def test_admin_review_endpoint_404(client_review: TestClient) -> None:
    r = client_review.get("/api/v1/admin/drafts/does-not-exist/review")
    assert r.status_code == 404


def test_admin_review_endpoint_ok(client_review: TestClient, brand_profile, db_session: Session) -> None:
    draft = _make_post_draft(db_session, brand_profile.id, status="draft")
    _attach_asset(db_session, draft)
    acc = _make_ig(db_session)

    r = client_review.get(
        f"/api/v1/admin/drafts/{draft.id}/review",
        params={"instagram_account_id": acc.id},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["draft_id"] == draft.id
    assert data["hook"] == "Stop scrolling"
    assert data["actions"]["approve"] == f"/api/v1/drafts/{draft.id}/approve"
    assert data["actions"]["publish_dry_run"] == f"/api/v1/publish/{draft.id}/dry-run"
    assert data["dry_run"]["ig_user_id"] == "17841400000000000"
    names = {c["name"] for c in data["publish_readiness_checks"]}
    assert "instagram_account" in names
