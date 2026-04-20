from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.core.config import Settings, get_settings
from astro_content_agent.db.models import Draft, InstagramAccount
from astro_content_agent.db.session import get_db
from astro_content_agent.main import create_app
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.services.diagnostics.checker import DiagnosticsService
from astro_content_agent.services.media.storage import LocalFileStorage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(**overrides) -> Settings:
    """Build a minimal Settings with sensible test defaults."""
    base = dict(
        _env_file=None,
        DATABASE_URL="sqlite:///:memory:",
        SCHEDULER_ENABLED=False,
        APP_ENV="local",
        OPENAI_API_KEY="sk-test",
        PUBLIC_BASE_URL="http://localhost:8000",
        STORAGE_MODE="local",
        ADMIN_API_KEY="",
        INSTAGRAM_ACCESS_TOKEN="dummy-token",
    )
    base.update(overrides)
    return Settings(**base)  # type: ignore[call-arg]


def _make_draft(db: Session, brand_profile_id: str, draft_type: str = "post", status: str = "draft") -> Draft:
    repo = DraftRepository()
    d = repo.create(
        db,
        brand_profile_id=brand_profile_id,
        content_plan_id=None,
        draft_type=draft_type,
        text="test",
        payload={"title": "T", "hook": "H", "caption": "C", "cta": "CTA", "hashtags": [], "metadata": {}},
    )
    db.commit()
    db.refresh(d)
    if status == "approved":
        repo.approve(db, d)
        db.commit()
        db.refresh(d)
    return d


def _make_asset(db: Session, draft: Draft, key: str = "bp/draft/placeholder.png") -> None:
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


def _make_ig_account(db: Session, *, with_token: bool = True) -> InstagramAccount:
    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test Acc",
        ig_user_id="ig-123",
        access_token="tok" if with_token else None,
        is_active=1,
    )
    db.add(acc)
    db.commit()
    return acc


@pytest.fixture()
def svc() -> DiagnosticsService:
    return DiagnosticsService()


# ---------------------------------------------------------------------------
# Unit: config checks
# ---------------------------------------------------------------------------


def test_openai_key_missing_local_is_warning(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(OPENAI_API_KEY=None, APP_ENV="local")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "openai_api_key")
    assert check.status == "warning"


def test_openai_key_missing_staging_is_error(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(OPENAI_API_KEY=None, APP_ENV="staging")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "openai_api_key")
    assert check.status == "error"


def test_openai_key_set_is_ok(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(OPENAI_API_KEY="sk-real")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "openai_api_key")
    assert check.status == "ok"


def test_admin_key_missing_local_is_ok(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(ADMIN_API_KEY=None, APP_ENV="local")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "admin_api_key")
    assert check.status == "ok"


def test_admin_key_missing_staging_is_warning(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(ADMIN_API_KEY=None, APP_ENV="staging")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "admin_api_key")
    assert check.status == "warning"


def test_admin_key_set_is_ok(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(ADMIN_API_KEY="mysecret")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "admin_api_key")
    assert check.status == "ok"


def test_public_base_url_localhost_is_warning(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(PUBLIC_BASE_URL="http://localhost:8000")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "public_base_url")
    assert check.status == "warning"


def test_public_base_url_localhost_staging_is_error(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(PUBLIC_BASE_URL="http://localhost:8000", APP_ENV="staging")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "public_base_url")
    assert check.status == "error"


def test_public_base_url_real_is_ok(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(PUBLIC_BASE_URL="https://myserver.example.com")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "public_base_url")
    assert check.status == "ok"


def test_public_base_url_invalid_is_error(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(PUBLIC_BASE_URL="not-a-url")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "public_base_url")
    assert check.status == "error"


def test_storage_mode_valid_is_ok(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(STORAGE_MODE="local")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "storage_mode")
    assert check.status == "ok"


def test_storage_mode_unknown_is_warning(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(STORAGE_MODE="s3-future")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "storage_mode")
    assert check.status == "warning"


def test_asset_url_generation_ok(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(PUBLIC_BASE_URL="https://example.com")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "asset_url_generation")
    assert check.status == "ok"
    assert "https://example.com/media/" in check.message


def test_no_ig_accounts_local_is_warning(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(APP_ENV="local")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "instagram_accounts")
    assert check.status == "warning"


def test_no_ig_accounts_staging_is_error(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(APP_ENV="staging")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "instagram_accounts")
    assert check.status == "error"


def test_ig_account_without_token_not_counted(
    svc: DiagnosticsService, db_session: Session
) -> None:
    _make_ig_account(db_session, with_token=False)
    settings = _settings(APP_ENV="local")
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "instagram_accounts")
    assert check.status == "warning"  # no token → not counted


def test_ig_account_with_token_is_ok(svc: DiagnosticsService, db_session: Session) -> None:
    _make_ig_account(db_session, with_token=True)
    settings = _settings()
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "instagram_accounts")
    assert check.status == "ok"


def test_instagram_access_token_missing_local_warns(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(INSTAGRAM_ACCESS_TOKEN=None)
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "instagram_access_token")
    assert check.status == "warning"


def test_instagram_access_token_missing_staging_errors(svc: DiagnosticsService, db_session: Session) -> None:
    _make_ig_account(db_session, with_token=True)
    settings = _settings(
        APP_ENV="staging",
        INSTAGRAM_ACCESS_TOKEN=None,
        OPENAI_API_KEY="sk-x",
        PUBLIC_BASE_URL="https://example.com",
    )
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "instagram_access_token")
    assert check.status == "error"


def test_assets_dir_exists_ok(svc: DiagnosticsService, db_session: Session, tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    settings = _settings(ASSETS_DIR=str(assets))
    report = svc.run_config_checks(settings, db_session)
    check = next(c for c in report.checks if c.name == "assets_dir")
    assert check.status == "ok"


# ---------------------------------------------------------------------------
# Unit: overall report status
# ---------------------------------------------------------------------------


def test_overall_ready_when_all_ok(svc: DiagnosticsService, db_session: Session) -> None:
    _make_ig_account(db_session, with_token=True)
    settings = _settings(
        APP_ENV="local",
        OPENAI_API_KEY="sk-x",
        ADMIN_API_KEY="key",
        PUBLIC_BASE_URL="https://example.com",
        STORAGE_MODE="local",
    )
    report = svc.run_config_checks(settings, db_session)
    # All errors resolved; may still have warnings for brand_profiles (empty DB)
    assert report.overall in ("ready", "degraded")


def test_overall_not_ready_when_error_present(svc: DiagnosticsService, db_session: Session) -> None:
    settings = _settings(APP_ENV="staging", OPENAI_API_KEY=None)
    report = svc.run_config_checks(settings, db_session)
    assert report.overall == "not_ready"


# ---------------------------------------------------------------------------
# Unit: publish readiness checks
# ---------------------------------------------------------------------------


def test_publish_readiness_draft_not_found(
    svc: DiagnosticsService, db_session: Session
) -> None:
    settings = _settings()
    report = svc.run_publish_readiness(db_session, draft_id="missing-id", settings=settings)
    assert report.ready is False
    check = next(c for c in report.checks if c.name == "draft_exists")
    assert check.status == "error"


def test_publish_readiness_draft_not_approved(
    svc: DiagnosticsService, db_session: Session, brand_profile
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="draft")
    settings = _settings()
    report = svc.run_publish_readiness(db_session, draft_id=draft.id, settings=settings)
    assert report.ready is False
    check = next(c for c in report.checks if c.name == "draft_approved")
    assert check.status == "error"


def test_publish_readiness_no_asset(
    svc: DiagnosticsService, db_session: Session, brand_profile
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="approved")
    settings = _settings()
    report = svc.run_publish_readiness(db_session, draft_id=draft.id, settings=settings)
    assert report.ready is False
    check = next(c for c in report.checks if c.name == "draft_has_asset")
    assert check.status == "error"


def test_publish_readiness_reel_type_warning(
    svc: DiagnosticsService, db_session: Session, brand_profile
) -> None:
    draft = _make_draft(db_session, brand_profile.id, draft_type="reel", status="approved")
    _make_asset(db_session, draft)
    settings = _settings(PUBLIC_BASE_URL="https://example.com")
    report = svc.run_publish_readiness(db_session, draft_id=draft.id, settings=settings)
    check = next(c for c in report.checks if c.name == "draft_type_publishable")
    assert check.status == "warning"


def test_publish_readiness_localhost_url_warning(
    svc: DiagnosticsService, db_session: Session, brand_profile
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="approved")
    _make_asset(db_session, draft)
    settings = _settings(PUBLIC_BASE_URL="http://localhost:8000")
    report = svc.run_publish_readiness(db_session, draft_id=draft.id, settings=settings)
    check = next(c for c in report.checks if c.name == "publish_public_url")
    assert check.status == "warning"


def test_publish_readiness_fully_ready(
    svc: DiagnosticsService, db_session: Session, brand_profile
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="approved")
    _make_asset(db_session, draft)
    settings = _settings(
        PUBLIC_BASE_URL="https://real.example.com",
        INSTAGRAM_ACCESS_TOKEN="tok",
    )
    report = svc.run_publish_readiness(db_session, draft_id=draft.id, settings=settings)
    assert report.ready is True
    assert all(c.status == "ok" for c in report.checks)


# ---------------------------------------------------------------------------
# API: GET /api/v1/admin/diagnostics
# ---------------------------------------------------------------------------


@pytest.fixture()
def diag_client(db_session: Session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    # Inject controlled settings (admin key unset → guard disabled in tests)
    fake_settings = _settings()
    app.dependency_overrides[get_settings] = lambda: fake_settings
    return TestClient(app)


def test_diagnostics_endpoint_returns_200(diag_client: TestClient) -> None:
    resp = diag_client.get("/api/v1/admin/diagnostics")
    assert resp.status_code == 200
    body = resp.json()
    assert "overall" in body
    assert "checks" in body
    assert isinstance(body["checks"], list)
    assert len(body["checks"]) > 0


def test_diagnostics_endpoint_check_names_present(diag_client: TestClient) -> None:
    resp = diag_client.get("/api/v1/admin/diagnostics")
    names = {c["name"] for c in resp.json()["checks"]}
    assert "openai_api_key" in names
    assert "public_base_url" in names
    assert "storage_mode" in names
    assert "assets_dir" in names
    assert "asset_url_generation" in names
    assert "instagram_access_token" in names
    assert "instagram_ig_user_id" in names
    assert "instagram_accounts" in names


def test_diagnostics_endpoint_structure(diag_client: TestClient) -> None:
    resp = diag_client.get("/api/v1/admin/diagnostics")
    body = resp.json()
    assert body["overall"] in ("ready", "degraded", "not_ready")
    assert body["app_env"] == "local"
    assert "checked_at" in body
    for c in body["checks"]:
        assert c["status"] in ("ok", "warning", "error")
        assert "message" in c


# ---------------------------------------------------------------------------
# API: GET /api/v1/admin/publish-readiness/{draft_id}
# ---------------------------------------------------------------------------


def test_publish_readiness_endpoint_missing_draft(diag_client: TestClient) -> None:
    resp = diag_client.get("/api/v1/admin/publish-readiness/no-such-draft")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is False
    check = next(c for c in body["checks"] if c["name"] == "draft_exists")
    assert check["status"] == "error"


def test_publish_readiness_endpoint_approved_with_asset(
    diag_client: TestClient, brand_profile, db_session: Session
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="approved")
    _make_asset(db_session, draft)

    resp = diag_client.get(f"/api/v1/admin/publish-readiness/{draft.id}")
    assert resp.status_code == 200
    body = resp.json()
    # localhost URL will cause a warning → not fully ready
    assert "ready" in body
    assert "checks" in body
    # draft_exists and draft_approved must be ok
    by_name = {c["name"]: c for c in body["checks"]}
    assert by_name["draft_exists"]["status"] == "ok"
    assert by_name["draft_approved"]["status"] == "ok"
    assert by_name["draft_has_asset"]["status"] == "ok"


def test_publish_readiness_endpoint_unapproved_draft(
    diag_client: TestClient, brand_profile, db_session: Session
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="draft")
    resp = diag_client.get(f"/api/v1/admin/publish-readiness/{draft.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is False
    by_name = {c["name"]: c for c in body["checks"]}
    assert by_name["draft_approved"]["status"] == "error"
    assert "hint" in by_name["draft_approved"]


def test_publish_readiness_simulate_query_returns_preview(
    diag_client: TestClient, brand_profile, db_session: Session
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="approved")
    _make_asset(db_session, draft)
    acc = _make_ig_account(db_session, with_token=True)
    resp = diag_client.get(
        f"/api/v1/admin/publish-readiness/{draft.id}",
        params={"simulate": "true", "instagram_account_id": acc.id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("simulation") is not None
    assert "image_url" in body["simulation"]
    assert body["simulation"]["ig_user_id"] == "ig-123"


def test_publish_readiness_with_bad_instagram_account_id(
    svc: DiagnosticsService, db_session: Session, brand_profile
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="approved")
    _make_asset(db_session, draft)
    settings = _settings(PUBLIC_BASE_URL="https://x.example.com", INSTAGRAM_ACCESS_TOKEN="t")
    report = svc.run_publish_readiness(
        db_session,
        draft_id=draft.id,
        settings=settings,
        instagram_account_id="not-a-uuid-row",
    )
    assert report.ready is False
    assert any(c.name == "instagram_account" and c.status == "error" for c in report.checks)


def test_publish_readiness_include_simulation_unit(
    svc: DiagnosticsService, db_session: Session, brand_profile
) -> None:
    draft = _make_draft(db_session, brand_profile.id, status="approved")
    _make_asset(db_session, draft)
    settings = _settings(PUBLIC_BASE_URL="https://x.example.com", INSTAGRAM_ACCESS_TOKEN="t")
    report = svc.run_publish_readiness(
        db_session,
        draft_id=draft.id,
        settings=settings,
        include_simulation=True,
    )
    assert report.simulation is not None
    assert "/media/" in report.simulation.image_url
