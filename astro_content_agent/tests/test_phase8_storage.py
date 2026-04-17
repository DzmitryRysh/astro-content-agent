from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.api.routes import drafts as drafts_routes
from astro_content_agent.api.routes import publish as publish_routes
from astro_content_agent.db.models import Draft, InstagramAccount
from astro_content_agent.db.session import get_db
from astro_content_agent.main import create_app
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.services.instagram.container_builder import ContainerBuilder
from astro_content_agent.services.instagram.publisher import PublisherService
from astro_content_agent.services.media.storage import LocalFileStorage
from astro_content_agent.services.media.url_builder import build_asset_url, get_local_storage
from astro_content_agent.core.config import Settings
from astro_content_agent.tests.fakes.fake_instagram import FakeInstagramClient


# ---------------------------------------------------------------------------
# Unit: LocalFileStorage
# ---------------------------------------------------------------------------


def test_local_storage_save_creates_file(tmp_path: Path) -> None:
    storage = LocalFileStorage(assets_dir=tmp_path, public_base_url="http://localhost:8000")
    key = "brand-1/draft-1/image.png"
    returned_key = storage.save(key, b"PNG_DATA", content_type="image/png")

    assert returned_key == key
    assert (tmp_path / key).exists()
    assert (tmp_path / key).read_bytes() == b"PNG_DATA"


def test_local_storage_normalises_backslashes(tmp_path: Path) -> None:
    storage = LocalFileStorage(assets_dir=tmp_path, public_base_url="http://localhost:8000")
    key = r"brand-1\draft-1\image.png"
    returned_key = storage.save(key, b"DATA")
    assert returned_key == "brand-1/draft-1/image.png"


def test_local_storage_url_builds_correct_path(tmp_path: Path) -> None:
    storage = LocalFileStorage(assets_dir=tmp_path, public_base_url="http://localhost:8000")
    assert storage.url("brand/draft/img.png") == "http://localhost:8000/media/brand/draft/img.png"


def test_local_storage_url_strips_leading_slash(tmp_path: Path) -> None:
    storage = LocalFileStorage(assets_dir=tmp_path, public_base_url="http://localhost:8000")
    assert storage.url("/brand/draft/img.png") == "http://localhost:8000/media/brand/draft/img.png"


def test_local_storage_url_strips_trailing_slash_from_base(tmp_path: Path) -> None:
    storage = LocalFileStorage(assets_dir=tmp_path, public_base_url="http://localhost:8000/")
    assert storage.url("k.png") == "http://localhost:8000/media/k.png"


def test_local_storage_absolute_path(tmp_path: Path) -> None:
    storage = LocalFileStorage(assets_dir=tmp_path, public_base_url="http://localhost:8000")
    assert storage.absolute_path("a/b.png") == tmp_path / "a" / "b.png"


def test_local_storage_creates_parent_dirs(tmp_path: Path) -> None:
    storage = LocalFileStorage(assets_dir=tmp_path, public_base_url="http://localhost:8000")
    storage.save("deep/nested/dir/file.png", b"X")
    assert (tmp_path / "deep" / "nested" / "dir" / "file.png").exists()


# ---------------------------------------------------------------------------
# Unit: url_builder helpers
# ---------------------------------------------------------------------------


def test_build_asset_url() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        DATABASE_URL="sqlite:///:memory:",
        PUBLIC_BASE_URL="https://example.com",
    )
    url = build_asset_url("brand/draft/img.png", settings)
    assert url == "https://example.com/media/brand/draft/img.png"


def test_build_asset_url_normalises_backslash() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        DATABASE_URL="sqlite:///:memory:",
        PUBLIC_BASE_URL="https://example.com",
    )
    url = build_asset_url(r"brand\draft\img.png", settings)
    assert url == "https://example.com/media/brand/draft/img.png"


def test_get_local_storage_returns_local_file_storage(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        DATABASE_URL="sqlite:///:memory:",
        ASSETS_DIR=str(tmp_path),
        PUBLIC_BASE_URL="http://localhost:8000",
    )
    storage = get_local_storage(settings)
    assert isinstance(storage, LocalFileStorage)
    assert storage.url("k.png") == "http://localhost:8000/media/k.png"


# ---------------------------------------------------------------------------
# Unit: ContainerBuilder uses url_resolver
# ---------------------------------------------------------------------------


def _make_mock_draft(brand_profile_id: str) -> Draft:
    d = Draft()
    d.id = str(uuid.uuid4())
    d.brand_profile_id = brand_profile_id
    d.draft_type = "post"
    d.status = "approved"
    d.payload = {
        "title": "T",
        "hook": "H",
        "caption": "My caption",
        "cta": "Follow me",
        "hashtags": ["#astro"],
        "metadata": {},
    }
    return d


def _make_mock_asset(draft: Draft, storage_path: str) -> object:
    from astro_content_agent.db.models import Asset

    a = Asset()
    a.id = str(uuid.uuid4())
    a.brand_profile_id = draft.brand_profile_id
    a.draft_id = draft.id
    a.asset_type = "image"
    a.storage_path = storage_path
    a.mime_type = "image/png"
    return a


def test_container_builder_identity_resolver() -> None:
    """Default (no resolver): storage_path passes through as image_url."""
    builder = ContainerBuilder()
    draft = _make_mock_draft("bp-1")
    asset = _make_mock_asset(draft, "bp-1/draft-x/img.png")
    params = builder.build(draft=draft, asset=asset)
    assert params.image_url == "bp-1/draft-x/img.png"


def test_container_builder_with_url_resolver(tmp_path: Path) -> None:
    """With a real LocalFileStorage resolver, image_url becomes a public URL."""
    storage = LocalFileStorage(assets_dir=tmp_path, public_base_url="http://localhost:8000")
    builder = ContainerBuilder(url_resolver=storage.url)
    draft = _make_mock_draft("bp-1")
    asset = _make_mock_asset(draft, "bp-1/draft-x/img.png")
    params = builder.build(draft=draft, asset=asset)
    assert params.image_url == "http://localhost:8000/media/bp-1/draft-x/img.png"


# ---------------------------------------------------------------------------
# Unit: ImageGenerationService stores relative key and uses StorageBackend
# ---------------------------------------------------------------------------


def test_image_service_stores_relative_key(db_session: Session, brand_profile, tmp_path: Path) -> None:
    from astro_content_agent.services.image.image_service import ImageGenerationService

    repo = DraftRepository()
    draft = repo.create(
        db_session,
        brand_profile_id=brand_profile.id,
        content_plan_id=None,
        draft_type="post",
        text="test",
        payload={"title": "T", "hook": "H", "caption": "C", "cta": "CTA", "hashtags": [], "metadata": {}},
    )
    db_session.commit()
    db_session.refresh(draft)

    storage = LocalFileStorage(assets_dir=tmp_path / "assets", public_base_url="http://localhost:8000")
    svc = ImageGenerationService()
    asset = svc.generate_placeholder(db=db_session, draft=draft, storage=storage)

    # storage_path must be a relative key, not an absolute path
    assert not Path(asset.storage_path).is_absolute()
    assert asset.storage_path == f"{brand_profile.id}/{draft.id}/placeholder.png"
    # The file must actually exist on disk
    assert (tmp_path / "assets" / asset.storage_path).exists()
    # URL can be resolved
    assert storage.url(asset.storage_path).startswith("http://localhost:8000/media/")


# ---------------------------------------------------------------------------
# API: generate-image returns public_url
# ---------------------------------------------------------------------------


@pytest.fixture()
def client_p8(db_session: Session, tmp_path: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[drafts_routes.get_storage] = lambda: LocalFileStorage(
        assets_dir=tmp_path / "assets",
        public_base_url="http://testserver",
    )
    return TestClient(app)


def test_generate_image_full_flow(
    client_p8: TestClient, brand_profile, db_session: Session, tmp_path: Path
) -> None:
    """End-to-end: create draft → generate-image → verify public_url + file on disk."""
    repo = DraftRepository()
    draft = repo.create(
        db_session,
        brand_profile_id=brand_profile.id,
        content_plan_id=None,
        draft_type="post",
        text="test caption",
        payload={"title": "T", "hook": "H", "caption": "C", "cta": "CTA", "hashtags": [], "metadata": {}},
    )
    db_session.commit()

    resp = client_p8.post(f"/api/v1/drafts/{draft.id}/generate-image")
    assert resp.status_code == 200
    body = resp.json()

    assert body["asset_type"] == "image"
    assert body["width"] == 1080
    assert not Path(body["storage_path"]).is_absolute()
    assert body["public_url"] == f"http://testserver/media/{body['storage_path']}"
    assert (tmp_path / "assets" / body["storage_path"]).exists()


# ---------------------------------------------------------------------------
# Publish flow: ContainerBuilder receives real URL when storage injected
# ---------------------------------------------------------------------------


def _make_approved_draft_and_asset(
    db: Session, brand_profile_id: str, storage: LocalFileStorage
) -> tuple:
    from astro_content_agent.services.image.image_service import ImageGenerationService

    repo = DraftRepository()
    draft = repo.create(
        db,
        brand_profile_id=brand_profile_id,
        content_plan_id=None,
        draft_type="post",
        text="caption",
        payload={
            "title": "T",
            "hook": "H",
            "caption": "Caption text",
            "cta": "Follow for more",
            "hashtags": ["#astro"],
            "metadata": {},
        },
    )
    db.commit()
    db.refresh(draft)
    repo.approve(db, draft)
    db.commit()
    db.refresh(draft)

    svc = ImageGenerationService()
    asset = svc.generate_placeholder(db=db, draft=draft, storage=storage)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test Acc",
        ig_user_id="ig-123",
        access_token="tok",
        is_active=1,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return draft, asset, acc


def test_publish_uses_public_url_in_container(
    db_session: Session, brand_profile, tmp_path: Path
) -> None:
    """PublisherService with storage injects a real public URL into container creation."""
    storage = LocalFileStorage(
        assets_dir=tmp_path / "assets",
        public_base_url="http://myserver.example.com",
    )
    ig_client = FakeInstagramClient()
    draft, asset, acc = _make_approved_draft_and_asset(db_session, brand_profile.id, storage)

    svc = PublisherService(ig_client=ig_client, storage=storage)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=acc.id)
    result = svc.execute_job(db_session, job_id=job.id)

    assert result.succeeded is True
    # The URL passed to the fake IG client must be a real public URL, not a bare key
    called_url = ig_client.container_calls[0]["image_url"]
    assert called_url.startswith("http://myserver.example.com/media/")
    assert asset.storage_path in called_url


def test_publish_without_storage_uses_key_as_url(
    db_session: Session, brand_profile, tmp_path: Path
) -> None:
    """Without storage injection, storage_path passes through unchanged (identity resolver)."""
    storage = LocalFileStorage(
        assets_dir=tmp_path / "assets",
        public_base_url="http://myserver.example.com",
    )
    ig_client = FakeInstagramClient()
    draft, asset, acc = _make_approved_draft_and_asset(db_session, brand_profile.id, storage)

    # No storage passed → identity resolver
    svc = PublisherService(ig_client=ig_client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=acc.id)
    result = svc.execute_job(db_session, job_id=job.id)

    assert result.succeeded is True
    called_url = ig_client.container_calls[0]["image_url"]
    # Identity resolver: URL == raw storage_path key
    assert called_url == asset.storage_path
