"""Tests for Venus weekly → PublisherService bridge (no real Meta API)."""
from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path

import pytest

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.models import InstagramAccount
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.services.content.venus_weekly_real_publish import (
    assert_publish_gates,
    build_value_error_publish_result,
    handoff_post_to_draft_payload,
    load_json,
    persist_publish_artifacts,
    resolve_week_artifacts,
    run_venus_weekly_real_publish,
)
from astro_content_agent.services.media.url_builder import get_local_storage
from astro_content_agent.services.instagram.client import MetaAPIError
from astro_content_agent.tests.fakes.fake_instagram import FakeInstagramClient


def _png1() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )


def _minimal_handoff(*, with_reel: bool = True) -> dict:
    items = [
        {
            "type": "post",
            "title": "Week title",
            "hook": "Hook line",
            "body": "Caption body text here.",
            "cta": "Save this.",
            "hashtags": ["#venus", "#astro"],
        },
    ]
    if with_reel:
        items.append(
            {
                "type": "reel",
                "hook_0_3s": "Open strong",
                "spoken_hook": "Different hook for reel",
                "script": "Script body " * 5,
                "cta": "Follow",
            }
        )
    return {"version": 1, "week_start": "2099-01-06", "week_end": "2099-01-12", "items": items}


def _final_ok() -> dict:
    return {
        "version": 1,
        "week_start": "2099-01-06",
        "final_check_status": "pass",
        "ready_for_publish": True,
        "issues": [],
    }


def test_assert_publish_gates_rejects_non_approved() -> None:
    with pytest.raises(ValueError, match="approved"):
        assert_publish_gates(state={"status": "draft"}, final_check=_final_ok())


def test_handoff_post_to_draft_payload_joins_hook_body_for_container_caption() -> None:
    post = {
        "type": "post",
        "title": "Week",
        "hook": "Opening",
        "body": "Main story.",
        "cta": "Go",
        "hashtags": ["tag"],
    }
    payload = handoff_post_to_draft_payload(post)
    assert payload["caption"] == "Opening\n\nMain story."
    assert payload["hashtags"] == ["#tag"]


def test_handoff_post_to_draft_payload_drops_template_caption_here_body() -> None:
    post = {
        "type": "post",
        "title": "Week",
        "hook": "Approved hook line.",
        "body": "Caption here.",
        "cta": "CTA text",
        "hashtags": [],
    }
    payload = handoff_post_to_draft_payload(post)
    assert "Caption here" not in payload["caption"]
    assert payload["caption"] == "Approved hook line."


def test_handoff_post_to_draft_payload_body_fallback_uses_caption_key() -> None:
    post = {
        "type": "post",
        "title": "Week",
        "hook": "",
        "caption": "Legacy caption field.",
        "cta": "",
        "hashtags": [],
    }
    payload = handoff_post_to_draft_payload(post)
    assert payload["caption"] == "Legacy caption field."


def test_assert_publish_gates_rejects_not_ready() -> None:
    fc = dict(_final_ok())
    fc["ready_for_publish"] = False
    with pytest.raises(ValueError, match="ready_for_publish"):
        assert_publish_gates(state={"status": "approved"}, final_check=fc)


def test_run_real_publish_post_only_rollup_published(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = "2099-01-06"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-01-12", "status": "approved"}),
        encoding="utf-8",
    )
    handoff = _minimal_handoff(with_reel=False)
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(
        json.dumps(handoff), encoding="utf-8"
    )
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")

    assets_root = tmp_path / "assets"
    key = "test-brand/venus.png"
    img_path = assets_root / key
    img_path.parent.mkdir(parents=True)
    img_path.write_bytes(_png1())

    monkeypatch.setenv("ASSETS_DIR", str(assets_root))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()

    settings = get_settings()
    storage = get_local_storage(settings)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="ig-user",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    final_check = load_json(paths.final_check_path)
    handoff_j = load_json(paths.handoff_path)

    run = run_venus_weekly_real_publish(
        db_session,
        settings=settings,
        paths=paths,
        handoff=handoff_j,
        state=state,
        final_check=final_check,
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        post_image_storage_key=key,
        ig_client=FakeInstagramClient(),
        storage=storage,
    )
    assert run.publish_status == "published"
    assert len(run.items) == 1
    assert run.items[0].role == "post"
    assert run.items[0].status == "succeeded"
    assert run.items[0].ig_media_id

    art, merged = persist_publish_artifacts(paths=paths, state=state, run=run)
    assert art.is_file()
    assert merged["publish_status"] == "published"
    assert "real_publish" in merged
    assert merged["real_publish"]["version"] == 2
    assert merged["publish_attempt_count"] == 1
    assert merged.get("publish_error_type") is None


def test_missing_media_asset_returns_publish_blocked(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = "2099-02-03"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-02-09", "status": "approved"}),
        encoding="utf-8",
    )
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(
        json.dumps(_minimal_handoff(with_reel=True)), encoding="utf-8"
    )
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")

    monkeypatch.setenv("ASSETS_DIR", str(tmp_path / "empty_assets"))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()
    settings = get_settings()
    storage = get_local_storage(settings)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="ig-user-m",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    run = run_venus_weekly_real_publish(
        db_session,
        settings=settings,
        paths=paths,
        handoff=load_json(paths.handoff_path),
        state=state,
        final_check=load_json(paths.final_check_path),
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        post_image_storage_key="missing/path.png",
        ig_client=FakeInstagramClient(),
        storage=storage,
        publish_attempt_count=2,
    )
    assert run.publish_status == "publish_blocked"
    assert run.publish_error_type == "missing_media_asset"
    assert run.publish_retryable is False
    assert run.publish_attempt_count == 2
    post = next(i for i in run.items if i.role == "post")
    assert post.status == "blocked"


def test_build_value_error_invalid_handoff_publish_failed(tmp_path: Path) -> None:
    ws = "2099-02-10"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-02-16", "status": "approved"}),
        encoding="utf-8",
    )
    handoff = {"version": 1, "week_start": ws, "items": [{"type": "reel", "x": 1}]}
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(json.dumps(handoff), encoding="utf-8")
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")
    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    exc = ValueError("handoff has no post item (type == 'post')")
    run = build_value_error_publish_result(
        paths=paths,
        handoff=handoff,
        state=state,
        publish_attempt_count=1,
        exc=exc,
    )
    assert run.publish_status == "publish_failed"
    assert run.publish_error_type == "invalid_handoff_payload"


def test_run_real_publish_with_reel_is_partial(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = "2099-01-13"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-01-19", "status": "approved"}),
        encoding="utf-8",
    )
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(
        json.dumps(_minimal_handoff(with_reel=True)), encoding="utf-8"
    )
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")

    assets_root = tmp_path / "assets2"
    key = "b/w.png"
    (assets_root / "b").mkdir(parents=True)
    (assets_root / key).write_bytes(_png1())
    monkeypatch.setenv("ASSETS_DIR", str(assets_root))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()
    settings = get_settings()
    storage = get_local_storage(settings)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="ig-user-2",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    run = run_venus_weekly_real_publish(
        db_session,
        settings=settings,
        paths=paths,
        handoff=load_json(paths.handoff_path),
        state=state,
        final_check=load_json(paths.final_check_path),
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        post_image_storage_key=key,
        ig_client=FakeInstagramClient(),
        storage=storage,
    )
    assert run.publish_status == "publish_partial"
    roles = {i.role: i.status for i in run.items}
    assert roles["post"] == "succeeded"
    assert roles["reel"] == "skipped_not_supported_by_publisher_mvp"


def test_instagram_caption_uses_hook_and_excludes_placeholder_body(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = "2099-03-01"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-03-07", "status": "approved"}),
        encoding="utf-8",
    )
    handoff = {
        "version": 1,
        "week_start": ws,
        "week_end": "2099-03-07",
        "items": [
            {
                "type": "post",
                "title": "Week",
                "hook": "Real approved hook.",
                "body": "Caption here.",
                "cta": "Save this.",
                "hashtags": ["venusweekly"],
            },
        ],
    }
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(json.dumps(handoff), encoding="utf-8")
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")

    assets_root = tmp_path / "assets_cap"
    key = "k/post.png"
    (assets_root / "k").mkdir(parents=True)
    (assets_root / key).write_bytes(_png1())
    monkeypatch.setenv("ASSETS_DIR", str(assets_root))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()
    settings = get_settings()
    storage = get_local_storage(settings)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="ig-user-cap",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    ig = FakeInstagramClient()
    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    run = run_venus_weekly_real_publish(
        db_session,
        settings=settings,
        paths=paths,
        handoff=load_json(paths.handoff_path),
        state=state,
        final_check=load_json(paths.final_check_path),
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        post_image_storage_key=key,
        ig_client=ig,
        storage=storage,
    )
    assert run.publish_status == "published"
    caption = ig.container_calls[0]["caption"]
    assert "Caption here" not in caption
    assert "Real approved hook." in caption
    assert "Save this." in caption
    assert "#venusweekly" in caption


def test_existing_post_draft_payload_synced_from_handoff_before_publish(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = "2099-03-08"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-03-14", "status": "approved"}),
        encoding="utf-8",
    )
    handoff = {
        "version": 1,
        "week_start": ws,
        "week_end": "2099-03-14",
        "items": [
            {
                "type": "post",
                "title": "Week",
                "hook": "Synced hook from handoff.",
                "body": "Caption here.",
                "cta": "Tap link",
                "hashtags": ["fresh"],
            },
        ],
    }
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(json.dumps(handoff), encoding="utf-8")
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")

    assets_root = tmp_path / "assets_sync"
    key = "reuse/post.png"
    (assets_root / "reuse").mkdir(parents=True)
    (assets_root / key).write_bytes(_png1())
    monkeypatch.setenv("ASSETS_DIR", str(assets_root))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()
    settings = get_settings()
    storage = get_local_storage(settings)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="ig-user-sync",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    drepo = DraftRepository()
    arepo = AssetRepository()
    stale = drepo.create(
        db_session,
        brand_profile_id=brand_profile.id,
        content_plan_id=None,
        draft_type="post",
        text="Caption here.",
        payload={
            "title": "Stale",
            "hook": "",
            "caption": "Caption here.",
            "cta": "CTA",
            "hashtags": ["#v"],
            "metadata": {},
        },
    )
    db_session.flush()
    drepo.approve(db_session, stale)
    arepo.create(
        db_session,
        brand_profile_id=brand_profile.id,
        draft_id=stale.id,
        asset_type="image",
        storage_path=key.replace("\\", "/").lstrip("/"),
        mime_type="image/png",
        width=None,
        height=None,
        meta={},
    )
    db_session.commit()
    db_session.refresh(stale)

    ig = FakeInstagramClient()
    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    run = run_venus_weekly_real_publish(
        db_session,
        settings=settings,
        paths=paths,
        handoff=load_json(paths.handoff_path),
        state=state,
        final_check=load_json(paths.final_check_path),
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        post_image_storage_key=key,
        ig_client=ig,
        storage=storage,
        existing_post_draft_id=stale.id,
    )
    assert run.publish_status == "published"
    caption = ig.container_calls[0]["caption"]
    assert "Caption here" not in caption
    assert "Synced hook from handoff." in caption
    assert "#fresh" in caption
    db_session.refresh(stale)
    assert stale.payload is not None
    assert "Caption here" not in str(stale.payload.get("caption", ""))


def test_publish_failed_on_fake_container_error(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = "2099-01-20"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-01-26", "status": "approved"}),
        encoding="utf-8",
    )
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(
        json.dumps(_minimal_handoff(with_reel=False)), encoding="utf-8"
    )
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")

    assets_root = tmp_path / "assets3"
    key = "c/x.png"
    (assets_root / "c").mkdir(parents=True)
    (assets_root / key).write_bytes(_png1())
    monkeypatch.setenv("ASSETS_DIR", str(assets_root))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()
    settings = get_settings()
    storage = get_local_storage(settings)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="ig-user-3",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    run = run_venus_weekly_real_publish(
        db_session,
        settings=settings,
        paths=paths,
        handoff=load_json(paths.handoff_path),
        state=state,
        final_check=load_json(paths.final_check_path),
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        post_image_storage_key=key,
        ig_client=FakeInstagramClient(fail_on_container=True),
        storage=storage,
    )
    assert run.publish_status == "publish_failed"
    assert run.items[0].status == "failed"
    assert run.items[0].error


def test_direct_post_image_url_is_used_for_meta_container(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = "2099-05-01"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-05-07", "status": "approved"}),
        encoding="utf-8",
    )
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(
        json.dumps(_minimal_handoff(with_reel=False)),
        encoding="utf-8",
    )
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")

    monkeypatch.setenv("ASSETS_DIR", str(tmp_path / "unused_assets"))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()
    settings = get_settings()
    storage = get_local_storage(settings)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="ig-user-direct",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    direct_url = "https://cdn.example.com/media/venus_2099-05-01.jpg"
    ig = FakeInstagramClient()
    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    run = run_venus_weekly_real_publish(
        db_session,
        settings=settings,
        paths=paths,
        handoff=load_json(paths.handoff_path),
        state=state,
        final_check=load_json(paths.final_check_path),
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        post_image_storage_key=None,
        post_image_url=direct_url,
        ig_client=ig,
        storage=storage,
    )
    assert run.publish_status == "published"
    assert ig.container_calls[0]["image_url"] == direct_url


class _Meta400Client:
    def create_image_container(self, *, ig_user_id: str, image_url: str, caption: str) -> str:
        raise MetaAPIError(
            status_code=400,
            url=(
                "https://graph.facebook.com/v19.0/123/media?"
                "image_url=https%3A%2F%2Ftest.example%2Fimg.png&access_token=<REDACTED>"
            ),
            response_text=(
                '{"error":{"message":"Invalid parameter","type":"OAuthException",'
                '"code":100,"error_subcode":2207052}}'
            ),
            response_json={
                "error": {
                    "message": "Invalid parameter",
                    "type": "OAuthException",
                    "code": 100,
                    "error_subcode": 2207052,
                }
            },
            meta_error_code=100,
            meta_error_subcode=2207052,
            meta_error_type="OAuthException",
            meta_error_message="Invalid parameter",
        )

    def publish_container(self, *, ig_user_id: str, container_id: str) -> str:
        return "unused"


def test_meta_json_error_persisted_and_token_redacted_in_artifact(
    db_session,
    brand_profile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = "2099-04-01"
    week_dir = tmp_path / ws
    week_dir.mkdir(parents=True)
    (week_dir / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-04-07", "status": "approved"}),
        encoding="utf-8",
    )
    (week_dir / f"venus_publish_handoff_{ws}.json").write_text(
        json.dumps(_minimal_handoff(with_reel=False)),
        encoding="utf-8",
    )
    (week_dir / f"venus_final_check_{ws}.json").write_text(json.dumps(_final_ok()), encoding="utf-8")

    assets_root = tmp_path / "assets_meta"
    key = "meta/post.png"
    (assets_root / "meta").mkdir(parents=True)
    (assets_root / key).write_bytes(_png1())
    monkeypatch.setenv("ASSETS_DIR", str(assets_root))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test.example")
    get_settings.cache_clear()
    settings = get_settings()
    storage = get_local_storage(settings)

    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Test",
        ig_user_id="ig-user-meta",
        access_token="fake",
        is_active=1,
    )
    db_session.add(acc)
    db_session.commit()

    paths = resolve_week_artifacts(week_dir=week_dir, week_start_hint=ws)
    state = load_json(paths.state_path)
    run = run_venus_weekly_real_publish(
        db_session,
        settings=settings,
        paths=paths,
        handoff=load_json(paths.handoff_path),
        state=state,
        final_check=load_json(paths.final_check_path),
        brand_profile_id=brand_profile.id,
        instagram_account_id=acc.id,
        post_image_storage_key=key,
        ig_client=_Meta400Client(),
        storage=storage,
    )
    assert run.publish_status == "publish_failed"
    assert run.meta_status_code == 400
    assert run.meta_error_message == "Invalid parameter"
    assert run.meta_error_code == 100
    assert run.meta_error_subcode == 2207052
    assert run.meta_error_body is not None and '"error"' in run.meta_error_body
    assert run.meta_url is not None and "access_token=<REDACTED>" in run.meta_url
    assert "access_token=EA" not in run.meta_url

    artifact_path, _merged = persist_publish_artifacts(paths=paths, state=state, run=run)
    artifact = artifact_path.read_text(encoding="utf-8")
    assert "access_token=<REDACTED>" in artifact
    assert '"meta_error_message": "Invalid parameter"' in artifact
    assert '"meta_status_code": 400' in artifact
