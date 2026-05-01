"""Tests for publish_venus_weekly_real.py CLI (importlib load, mocked Cloudinary / Meta)."""
from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path

import pytest

from astro_content_agent.core.config import Settings, get_settings
from astro_content_agent.db.models import BrandProfile, InstagramAccount
from astro_content_agent.services.media.cloudinary_uploader import CloudinaryUploadResult
from astro_content_agent.tests.fakes.fake_instagram import FakeInstagramClient


def _load_publish_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    cli_path = repo / "scripts" / "aca" / "publish_venus_weekly_real.py"
    spec = importlib.util.spec_from_file_location("_publish_vrp_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _NoCloseSession:
    __slots__ = ("_inner",)

    def __init__(self, inner):
        object.__setattr__(self, "_inner", inner)

    def __getattr__(self, name: str):
        return getattr(self._inner, name)

    def close(self) -> None:
        return None


def _write_week_pack(week_dir: Path, ws: str) -> None:
    week_dir.mkdir(parents=True, exist_ok=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-11-07", "status": "approved"}),
        encoding="utf-8",
    )
    handoff = {
        "version": 1,
        "week_start": ws,
        "week_end": "2099-11-07",
        "items": [
            {
                "type": "post",
                "title": "T",
                "hook": "H",
                "body": "B",
                "cta": "C",
                "hashtags": ["#a"],
            },
        ],
    }
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(json.dumps(handoff), encoding="utf-8")
    (week_dir / f"venus_final_check_{ws}.json").write_text(
        json.dumps(
            {
                "version": 1,
                "week_start": ws,
                "final_check_status": "pass",
                "ready_for_publish": True,
                "issues": [],
            }
        ),
        encoding="utf-8",
    )


@pytest.fixture()
def publish_cli():
    return _load_publish_cli()


def test_cli_rejects_url_and_path_without_week_dir(publish_cli, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    img = tmp_path / "x.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    monkeypatch.setattr(sys, "argv", ["x", "2099-11-01", "--instagram-account-id", "i", "--brand-profile-id", "b", "--post-image-url", "https://u", "--post-image-path", str(img)])
    assert publish_cli.main() == 2


def test_cli_post_image_path_uses_cloudinary_secure_url_in_publish(
    publish_cli,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    db_session,
    brand_profile: BrandProfile,
) -> None:
    ws = "2099-11-02"
    week_dir = tmp_path / ws
    _write_week_pack(week_dir, ws)
    img = tmp_path / "upload_me.jpg"
    img.write_bytes(b"\xff\xd8\xff")

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="CLI Test",
        ig_user_id="17841400000000000",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    fake_ig = FakeInstagramClient()
    expected_secure = "https://res.cloudinary.com/demo/image/upload/v123/z.jpg"

    def _fake_upload(settings, local_path, *, public_id=None, folder=None, timeout_seconds=120.0):  # type: ignore[no-untyped-def]
        assert Path(local_path).resolve() == img.resolve()
        return CloudinaryUploadResult(
            secure_url=expected_secure,
            public_id="astro-content-agent/cli_test",
            local_path=Path(local_path).resolve(),
            format="jpg",
            bytes=3,
        )

    get_settings.cache_clear()
    monkeypatch.setattr(
        publish_cli,
        "get_settings",
        lambda: Settings(
            _env_file=None,
            CLOUDINARY_CLOUD_NAME="demo",
            CLOUDINARY_API_KEY="k",
            CLOUDINARY_API_SECRET="sec",
            CLOUDINARY_FOLDER="astro-content-agent",
            INSTAGRAM_ACCESS_TOKEN="iga-token-for-meta-client",
            ASSETS_DIR=str(tmp_path / "assets"),
            PUBLIC_BASE_URL="http://test.example",
            DATABASE_URL="sqlite:///:memory:",
        ),
    )
    monkeypatch.setattr(publish_cli, "default_week_dir", lambda w, wd=None: week_dir)
    monkeypatch.setattr(publish_cli, "SessionLocal", lambda: _NoCloseSession(db_session))
    monkeypatch.setattr(publish_cli, "upload_local_image", _fake_upload)
    monkeypatch.setattr(publish_cli, "build_meta_client", lambda _s: fake_ig)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_venus_weekly_real.py",
            ws,
            "--instagram-account-id",
            acc.id,
            "--brand-profile-id",
            brand_profile.id,
            "--post-image-path",
            str(img),
        ],
    )
    assert publish_cli.main() == 0
    assert fake_ig.container_calls
    assert fake_ig.container_calls[0]["image_url"] == expected_secure


def test_cli_cloudinary_upload_failure_returns_1(
    publish_cli,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    db_session,
    brand_profile: BrandProfile,
) -> None:
    ws = "2099-11-03"
    week_dir = tmp_path / ws
    _write_week_pack(week_dir, ws)
    img = tmp_path / "bad.jpg"
    img.write_bytes(b"\xff\xd8\xff")

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="CLI Test 2",
        ig_user_id="17841400000000001",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    def _boom(settings, local_path, **kw):  # type: ignore[no-untyped-def]
        raise RuntimeError("Cloudinary upload failed HTTP 400: err")

    get_settings.cache_clear()
    monkeypatch.setattr(
        publish_cli,
        "get_settings",
        lambda: Settings(
            _env_file=None,
            CLOUDINARY_CLOUD_NAME="demo",
            CLOUDINARY_API_KEY="k",
            CLOUDINARY_API_SECRET="sec",
            INSTAGRAM_ACCESS_TOKEN="tok",
            ASSETS_DIR=str(tmp_path / "a"),
            PUBLIC_BASE_URL="http://t",
            DATABASE_URL="sqlite:///:memory:",
        ),
    )
    monkeypatch.setattr(publish_cli, "default_week_dir", lambda w, wd=None: week_dir)
    monkeypatch.setattr(publish_cli, "SessionLocal", lambda: _NoCloseSession(db_session))
    monkeypatch.setattr(publish_cli, "upload_local_image", _boom)
    monkeypatch.setattr(publish_cli, "build_meta_client", lambda _s: FakeInstagramClient())

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_venus_weekly_real.py",
            ws,
            "--instagram-account-id",
            acc.id,
            "--brand-profile-id",
            brand_profile.id,
            "--post-image-path",
            str(img),
        ],
    )
    assert publish_cli.main() == 1
