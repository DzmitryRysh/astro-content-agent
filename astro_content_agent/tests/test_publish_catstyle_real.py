"""Deterministic tests for Catstyle real publish (no Meta / Cloudinary network)."""
from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path

import pytest

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.models import InstagramAccount
from astro_content_agent.services.content.catstyle_real_publish import (
    CatstyleRealPublishError,
    CatstyleRealPublishResult,
    assert_handoff_publishable,
    load_catstyle_handoff_json,
    persist_catstyle_publish_artifacts,
    read_caption_final,
    read_primary_image_path_file,
    redact_secrets_for_artifact,
    resolve_local_image_path_for_publish,
    result_to_public_dict,
    run_catstyle_real_publish,
    validate_catstyle_publish_environment,
)
from astro_content_agent.services.content.venus_weekly_real_publish import build_meta_client
from astro_content_agent.tests.fakes.fake_instagram import FakeInstagramClient


def _png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )


def _write_ready_handoff(hdir: Path, *, publish_status: str = "ready_for_manual_publish") -> Path:
    hdir.mkdir(parents=True, exist_ok=True)
    img = hdir / "shot.png"
    img.write_bytes(_png_bytes())
    (hdir / "publish_handoff.json").write_text(
        json.dumps(
            {
                "version": "catstyle-publish-handoff-v1",
                "date": "2099-05-09",
                "publish_status": publish_status,
                "hook": "Hook line",
                "caption_final": "From json only",
                "recommended_primary_image": str(img.resolve()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (hdir / "caption_final.txt").write_text("Caption from disk file wins\n", encoding="utf-8")
    (hdir / "primary_image_path.txt").write_text(str(img.resolve()), encoding="utf-8")
    return img


def test_read_caption_final_prefers_txt_over_json(tmp_path: Path) -> None:
    hdir = tmp_path / "h"
    _write_ready_handoff(hdir)
    handoff = load_catstyle_handoff_json(hdir)
    cap = read_caption_final(hdir, handoff)
    assert "disk file" in cap
    assert "From json" not in cap


def test_read_primary_image_path_file(tmp_path: Path) -> None:
    hdir = tmp_path / "h"
    img = _write_ready_handoff(hdir)
    raw = read_primary_image_path_file(hdir)
    assert Path(raw).resolve() == img.resolve()


def test_resolve_local_image_path_explicit_overrides_primary_file(tmp_path: Path) -> None:
    hdir = tmp_path / "h"
    _write_ready_handoff(hdir)
    other = tmp_path / "other.png"
    other.write_bytes(_png_bytes())
    handoff = load_catstyle_handoff_json(hdir)
    p = resolve_local_image_path_for_publish(hdir, local_image_path=other, handoff=handoff)
    assert p.resolve() == other.resolve()


def test_assert_handoff_publishable_rejects_wrong_status() -> None:
    with pytest.raises(CatstyleRealPublishError, match="publish_status"):
        assert_handoff_publishable({"publish_status": "draft"})


def test_validate_catstyle_publish_environment_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "")
    get_settings.cache_clear()
    settings = get_settings()
    missing = validate_catstyle_publish_environment(settings=settings, need_cloudinary_upload=False)
    assert "INSTAGRAM_ACCESS_TOKEN" in missing
    get_settings.cache_clear()


def test_validate_catstyle_publish_environment_missing_cloudinary_when_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "x")
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "")
    get_settings.cache_clear()
    settings = get_settings()
    missing = validate_catstyle_publish_environment(settings=settings, need_cloudinary_upload=True)
    assert "CLOUDINARY_CLOUD_NAME" in missing
    assert "CLOUDINARY_API_KEY" in missing
    assert "CLOUDINARY_API_SECRET" in missing
    get_settings.cache_clear()


def test_validate_catstyle_skips_cloudinary_when_post_url_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "x")
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "")
    get_settings.cache_clear()
    settings = get_settings()
    missing = validate_catstyle_publish_environment(settings=settings, need_cloudinary_upload=False)
    assert not any(x.startswith("CLOUDINARY_") for x in missing)
    get_settings.cache_clear()


def test_run_catstyle_validate_only_ok(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "fake-token-for-tests")
    monkeypatch.setenv("ASSETS_DIR", str(tmp_path / "assets"))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()

    hdir = tmp_path / "handoff"
    _write_ready_handoff(hdir)
    handoff = load_catstyle_handoff_json(hdir)
    caption = read_caption_final(hdir, handoff)
    settings = get_settings()

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="17841400000000000",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    ig = build_meta_client(settings)
    assert ig is not None
    r = run_catstyle_real_publish(
        db_session,
        settings=settings,
        handoff_dir=hdir,
        handoff=handoff,
        caption_final=caption,
        hook=str(handoff["hook"]),
        image_public_url=None,
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        ig_client=ig,
        validate_only=True,
    )
    assert r.publish_status == "validate_only_ok"
    assert r.image_url_used is None
    get_settings.cache_clear()


def test_run_catstyle_real_publish_with_post_url_skips_upload_path(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "fake-token-for-tests")
    monkeypatch.setenv("ASSETS_DIR", str(tmp_path / "assets"))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()

    hdir = tmp_path / "handoff"
    _write_ready_handoff(hdir)
    handoff = load_catstyle_handoff_json(hdir)
    caption = read_caption_final(hdir, handoff)
    settings = get_settings()

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="17841400000000000",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    fake = FakeInstagramClient()
    r = run_catstyle_real_publish(
        db_session,
        settings=settings,
        handoff_dir=hdir,
        handoff=handoff,
        caption_final=caption,
        hook=str(handoff["hook"]),
        image_public_url="https://cdn.example.com/public/cat.png",
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        ig_client=fake,
        validate_only=False,
    )
    assert r.publish_status == "published"
    assert r.image_url_used == "https://cdn.example.com/public/cat.png"
    assert fake.container_calls and "cdn.example.com" in fake.container_calls[0]["image_url"]
    get_settings.cache_clear()


def test_persisted_result_json_has_no_raw_instagram_token(tmp_path: Path) -> None:
    r = CatstyleRealPublishResult(
        publish_status="publish_failed",
        error_message="Meta said access_token=IGAABCVERYLONGFAKETOKENSTRING and failed",
        error_type="meta_publish_error",
        publish_retryable=True,
    )
    jp, _ = persist_catstyle_publish_artifacts(tmp_path, r)
    dumped = jp.read_text(encoding="utf-8")
    assert "IGAABC" not in dumped
    assert "<REDACTED" in dumped or "REDACTED" in dumped


def test_result_to_public_dict_redacts_error_message() -> None:
    r = CatstyleRealPublishResult(
        publish_status="publish_failed",
        error_message="failure https://graph.instagram.com/x?access_token=IGAFAKE123456789012345",
        error_type="x",
    )
    d = result_to_public_dict(r)
    assert "IGAFAKE" not in json.dumps(d)
    assert "access_token=<REDACTED>" in d["error_message"] or "<REDACTED" in d["error_message"]


def test_redact_secrets_for_artifact_covers_token_like_strings() -> None:
    s = redact_secrets_for_artifact("err IGAABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 tail")
    assert "IGA" not in s or "REDACTED" in s


@pytest.mark.parametrize("url", ["http://insecure.example/x.png", "ftp://x"])
def test_run_catstyle_rejects_non_https_image_url(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "fake-token-for-tests")
    monkeypatch.setenv("ASSETS_DIR", str(tmp_path / "assets"))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()

    hdir = tmp_path / "handoff"
    _write_ready_handoff(hdir)
    handoff = load_catstyle_handoff_json(hdir)
    settings = get_settings()
    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="17841400000000000",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()
    fake = FakeInstagramClient()
    r = run_catstyle_real_publish(
        db_session,
        settings=settings,
        handoff_dir=hdir,
        handoff=handoff,
        caption_final="c",
        hook="h",
        image_public_url=url,
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        ig_client=fake,
        validate_only=False,
    )
    assert r.publish_status == "publish_failed"
    assert r.error_type == "invalid_image_url"
    assert fake.container_calls == []
    get_settings.cache_clear()
