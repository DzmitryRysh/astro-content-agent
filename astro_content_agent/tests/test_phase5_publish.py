from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.api.routes import publish as publish_routes
from astro_content_agent.db.models import Asset, Draft, InstagramAccount
from astro_content_agent.core.config import Settings, get_settings
from astro_content_agent.db.session import get_db
from astro_content_agent.main import create_app
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.repositories.publish_jobs import PublishJobRepository
from astro_content_agent.services.instagram.publisher import PublisherService
from astro_content_agent.services.media.storage import LocalFileStorage
from astro_content_agent.tests.fakes.fake_instagram import FakeInstagramClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_account(db: Session) -> InstagramAccount:
    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test Account",
        ig_user_id="ig-user-123",
        access_token="fake-token",
        is_active=1,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


def _make_approved_draft(db: Session, brand_profile_id: str) -> Draft:
    repo = DraftRepository()
    d = repo.create(
        db,
        brand_profile_id=brand_profile_id,
        content_plan_id=None,
        draft_type="post",
        text="caption text",
        payload={
            "title": "Title",
            "hook": "Hook",
            "caption": "Caption text",
            "cta": "Follow for more",
            "hashtags": ["#astro"],
            "metadata": {},
        },
    )
    db.commit()
    db.refresh(d)
    repo.approve(db, d)
    db.commit()
    db.refresh(d)
    return d


def _make_draft_not_approved(db: Session, brand_profile_id: str) -> Draft:
    repo = DraftRepository()
    d = repo.create(
        db,
        brand_profile_id=brand_profile_id,
        content_plan_id=None,
        draft_type="post",
        text="caption text",
        payload={
            "title": "Title",
            "hook": "Hook",
            "caption": "Caption",
            "cta": "CTA",
            "hashtags": [],
            "metadata": {},
        },
    )
    db.commit()
    db.refresh(d)
    return d


def _make_asset(db: Session, draft: Draft, storage_path: str = "/tmp/placeholder.png") -> Asset:
    repo = AssetRepository()
    a = repo.create(
        db,
        brand_profile_id=draft.brand_profile_id,
        draft_id=draft.id,
        asset_type="image",
        storage_path=storage_path,
        mime_type="image/png",
        width=1080,
        height=1080,
    )
    db.commit()
    db.refresh(a)
    return a


@pytest.fixture()
def ig_client() -> FakeInstagramClient:
    return FakeInstagramClient()


@pytest.fixture()
def client_p5(db_session: Session, ig_client: FakeInstagramClient, tmp_path: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[publish_routes.get_ig_client] = lambda: ig_client
    # Provide a real LocalFileStorage so get_storage() resolves cleanly in tests.
    app.dependency_overrides[publish_routes.get_storage] = lambda: LocalFileStorage(
        assets_dir=tmp_path / "assets",
        public_base_url="http://testserver",
    )
    return TestClient(app)


@pytest.fixture()
def client_publish_dry_run(db_session: Session, tmp_path: Path) -> TestClient:
    """App client without INSTAGRAM_ACCESS_TOKEN — for dry-run endpoint tests."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    fake = Settings(
        _env_file=None,
        SCHEDULER_ENABLED=False,
        APP_ENV="local",
        OPENAI_API_KEY="sk-test",
        PUBLIC_BASE_URL="http://testserver",
        STORAGE_MODE="local",
        ASSETS_DIR=str(tmp_path / "assets"),
        INSTAGRAM_ACCESS_TOKEN=None,
    )
    app.dependency_overrides[get_settings] = lambda: fake
    return TestClient(app)


# ---------------------------------------------------------------------------
# Unit-level: PublisherService
# ---------------------------------------------------------------------------


def test_create_job_requires_approved_draft(db_session: Session, brand_profile, ig_client) -> None:
    draft = _make_draft_not_approved(db_session, brand_profile.id)
    account = _make_account(db_session)
    svc = PublisherService(ig_client=ig_client)

    with pytest.raises(PublisherService.DraftNotApprovedError):
        svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)


def test_create_job_rejects_missing_account(db_session: Session, brand_profile, ig_client) -> None:
    draft = _make_approved_draft(db_session, brand_profile.id)
    svc = PublisherService(ig_client=ig_client)

    with pytest.raises(PublisherService.AccountNotFoundError):
        svc.create_job(db_session, draft_id=draft.id, instagram_account_id="missing")


def test_execute_job_fails_when_ig_user_id_missing(
    db_session: Session, brand_profile, ig_client: FakeInstagramClient
) -> None:
    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="No IG id",
        ig_user_id=None,
        access_token="tok",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()
    draft = _make_approved_draft(db_session, brand_profile.id)
    _make_asset(db_session, draft)
    svc = PublisherService(ig_client=ig_client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=acc.id)
    result = svc.execute_job(db_session, job_id=job.id)
    assert result.succeeded is False
    assert result.error is not None
    assert "ig_user_id" in result.error.lower()


def test_successful_publish_flow(db_session: Session, brand_profile, ig_client) -> None:
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    svc = PublisherService(ig_client=ig_client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)
    result = svc.execute_job(db_session, job_id=job.id)

    assert result.succeeded is True
    assert result.published_post is not None
    assert result.published_post.ig_media_id is not None
    assert result.publish_job.status == "succeeded"
    assert result.publish_job.external_publish_id is not None
    assert len(ig_client.container_calls) == 1
    assert len(ig_client.publish_calls) == 1


def test_failed_publish_marks_job_retryable(db_session: Session, brand_profile) -> None:
    failing_client = FakeInstagramClient(fail_on_publish=True)
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    svc = PublisherService(ig_client=failing_client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)
    result = svc.execute_job(db_session, job_id=job.id)

    assert result.succeeded is False
    # 1 attempt < MAX_ATTEMPTS(3): job goes back to queued for retry
    assert result.publish_job.status == "queued"
    assert result.publish_job.last_error is not None
    assert result.published_post is None


def test_container_creation_failure_marks_job_retryable(db_session: Session, brand_profile) -> None:
    failing_client = FakeInstagramClient(fail_on_container=True)
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    svc = PublisherService(ig_client=failing_client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)
    result = svc.execute_job(db_session, job_id=job.id)

    assert result.succeeded is False
    assert result.publish_job.status == "queued"


def test_retry_skips_container_creation_when_container_id_stored(db_session: Session, brand_profile) -> None:
    """If container_id is already saved (prior attempt), step 1 is skipped on retry."""
    client = FakeInstagramClient(container_id_override="saved-container-id")
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    svc = PublisherService(ig_client=client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)

    # Manually pre-set container_id as if a prior attempt already created it
    job_repo = PublishJobRepository()
    job_repo.store_container_id(db_session, job, container_id="saved-container-id")
    db_session.commit()

    result = svc.execute_job(db_session, job_id=job.id)

    assert result.succeeded is True
    # Container creation was skipped — zero calls
    assert len(client.container_calls) == 0
    # But publish was called with the pre-saved container_id
    assert client.publish_calls[0]["container_id"] == "saved-container-id"


def test_permanently_failed_after_max_attempts(db_session: Session, brand_profile) -> None:
    failing_client = FakeInstagramClient(fail_on_publish=True)
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    svc = PublisherService(ig_client=failing_client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)

    # Simulate 3 failed attempts to exhaust MAX_ATTEMPTS
    for _ in range(3):
        result = svc.execute_job(db_session, job_id=job.id)

    assert result.publish_job.status == "failed"


# ---------------------------------------------------------------------------
# API-level: publish endpoints
# ---------------------------------------------------------------------------


def test_publish_now_endpoint_succeeds(client_p5: TestClient, brand_profile, db_session: Session) -> None:
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    resp = client_p5.post(
        f"/api/v1/publish/{draft.id}",
        json={"instagram_account_id": account.id},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["succeeded"] is True
    assert body["publish_job"]["status"] == "succeeded"
    assert body["published_post"]["ig_media_id"] is not None


def test_publish_now_rejects_unapproved_draft(client_p5: TestClient, brand_profile, db_session: Session) -> None:
    draft = _make_draft_not_approved(db_session, brand_profile.id)
    account = _make_account(db_session)

    resp = client_p5.post(
        f"/api/v1/publish/{draft.id}",
        json={"instagram_account_id": account.id},
    )
    assert resp.status_code == 409


def test_schedule_publish_creates_queued_job(client_p5: TestClient, brand_profile, db_session: Session) -> None:
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)

    resp = client_p5.post(
        f"/api/v1/publish/{draft.id}/schedule",
        json={
            "instagram_account_id": account.id,
            "scheduled_for": "2026-04-10T10:00:00Z",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "queued"
    assert body["scheduled_for"] is not None


def test_list_publish_jobs(client_p5: TestClient, brand_profile, db_session: Session) -> None:
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    client_p5.post(f"/api/v1/publish/{draft.id}", json={"instagram_account_id": account.id})

    resp = client_p5.get("/api/v1/publish/jobs")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_publish_dry_run_returns_simulation_without_meta_token(
    client_publish_dry_run: TestClient, brand_profile, db_session: Session
) -> None:
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft, storage_path="brand/draft/image.png")

    resp = client_publish_dry_run.post(
        f"/api/v1/publish/{draft.id}/dry-run",
        json={"instagram_account_id": account.id},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["simulation"] is not None
    assert body["simulation"]["image_url"].startswith("http://testserver/media/")
    assert body["instagram_account_id"] == account.id
    names = {c["name"] for c in body["checks"]}
    assert "publish_instagram_token" in names


def test_publish_dry_run_errors_when_account_missing_ig_user_id(
    client_publish_dry_run: TestClient, brand_profile, db_session: Session
) -> None:
    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="X",
        ig_user_id=None,
        access_token="t",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()
    draft = _make_approved_draft(db_session, brand_profile.id)
    _make_asset(db_session, draft)

    resp = client_publish_dry_run.post(
        f"/api/v1/publish/{draft.id}/dry-run",
        json={"instagram_account_id": acc.id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is False
    assert any(c["name"] == "instagram_account_ig_user_id" and c["status"] == "error" for c in body["checks"])


def test_publish_history(client_p5: TestClient, brand_profile, db_session: Session) -> None:
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    client_p5.post(f"/api/v1/publish/{draft.id}", json={"instagram_account_id": account.id})

    resp = client_p5.get("/api/v1/publish/history")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
    assert resp.json()["items"][0]["ig_media_id"] is not None
