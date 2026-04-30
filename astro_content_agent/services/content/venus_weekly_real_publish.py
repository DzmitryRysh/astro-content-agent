"""Approved + final-check-passed Venus weekly handoff → ``PublisherService`` (image post MVP).

Reel and support items from the handoff are not published by ``PublisherService`` today
(only ``draft_type == "post"`` with an image asset). Those items are recorded explicitly
as ``not_supported_by_publisher_mvp`` so callers never treat them as Instagram successes.
"""
from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from sqlalchemy.orm import Session

from astro_content_agent.core.config import Settings
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.services.instagram.client import InstagramClientProtocol, MetaInstagramClient
from astro_content_agent.services.instagram.publisher import PublisherService
from astro_content_agent.services.content.venus_publish_failure import (
    PublishFailureClassification,
    classify_exception,
    classify_message,
    next_publish_attempt_count,
)
from astro_content_agent.services.media.storage import StorageBackend
from astro_content_agent.services.media.url_builder import get_local_storage


@dataclass
class WeekArtifactPaths:
    week_dir: Path
    state_path: Path
    handoff_path: Path
    final_check_path: Path
    week_start: str


def resolve_week_artifacts(
    *,
    week_dir: Path,
    week_start_hint: str | None = None,
    state_file: Path | None = None,
    handoff_file: Path | None = None,
    final_check_file: Path | None = None,
) -> WeekArtifactPaths:
    """Resolve standard Venus weekly JSON paths under *week_dir*."""
    week_dir = Path(week_dir)
    if state_file is not None:
        sp = Path(state_file)
    else:
        hint = week_start_hint or week_dir.name
        exact = week_dir / f"venus_weekly_state_{hint}.json"
        if exact.is_file():
            sp = exact
        else:
            matches = sorted(week_dir.glob("venus_weekly_state_*.json"))
            if not matches:
                raise ValueError(f"No venus_weekly_state_*.json in {week_dir}")
            if len(matches) > 1:
                raise ValueError(
                    "Multiple state files; pass state_file or week_start_hint: "
                    + ", ".join(m.name for m in matches)
                )
            sp = matches[0]

    state = json.loads(sp.read_text(encoding="utf-8"))
    ws = str(state.get("week_start") or week_dir.name)

    if handoff_file is not None:
        hp = Path(handoff_file)
    else:
        hp = week_dir / f"venus_publish_handoff_{ws}.json"

    if final_check_file is not None:
        fp = Path(final_check_file)
    else:
        fp = week_dir / f"venus_final_check_{ws}.json"

    return WeekArtifactPaths(week_dir=week_dir, state_path=sp, handoff_path=hp, final_check_path=fp, week_start=ws)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_publish_gates(*, state: dict[str, Any], final_check: dict[str, Any]) -> None:
    """Require approved weekly state and final-check pass (same gates as publishing)."""
    if str(state.get("status", "")) != "approved":
        raise ValueError(f"Publishing requires state.status == 'approved'; got {state.get('status')!r}")
    if not bool(final_check.get("ready_for_publish")):
        raise ValueError(
            "Publishing requires final_check.ready_for_publish == true "
            f"(final_check_status={final_check.get('final_check_status')!r})."
        )
    if str(final_check.get("final_check_status", "")) != "pass":
        raise ValueError(
            "Publishing requires final_check.final_check_status == 'pass'; "
            f"got {final_check.get('final_check_status')!r}."
        )


def _find_handoff_post(handoff: dict[str, Any]) -> dict[str, Any]:
    for it in handoff.get("items") or []:
        if isinstance(it, dict) and it.get("type") == "post":
            return it
    raise ValueError("handoff has no post item (type == 'post')")


def _handoff_post_body_text(post: dict[str, Any]) -> str:
    """Prefer ``body`` (handoff builder); accept legacy/alternate ``caption`` key."""
    raw = post.get("body")
    if raw is None or not str(raw).strip():
        raw = post.get("caption")
    return str(raw or "").strip()


_PLACEHOLDER_BODY_NORMALIZED = frozenset({"caption here"})


def _omit_placeholder_body(body: str) -> str:
    """Drop markdown-template filler so IG caption uses real hook/body only."""
    t = body.strip()
    if not t:
        return ""
    if t.lower().rstrip(".") in _PLACEHOLDER_BODY_NORMALIZED:
        return ""
    return body.strip()


def _normalize_hashtag_list(raw: Any) -> list[str]:
    """Ensure space-joined hashtags render as ``#tag`` (handoff may omit ``#``)."""
    out: list[str] = []
    for x in raw or []:
        s = str(x).strip()
        if not s:
            continue
        if not s.startswith("#"):
            s = f"#{s}"
        out.append(s)
    return out


def _instagram_caption_first_block(*, hook: str, body: str, title: str) -> str:
    """Block merged into ``PostDraftPayload.caption`` (see ``ContainerBuilder``)."""
    h = hook.strip()
    b = _omit_placeholder_body(body)
    parts = [p for p in (h, b) if p]
    if parts:
        return "\n\n".join(parts)
    t = title.strip()
    return t


def handoff_post_to_draft_payload(post: dict[str, Any]) -> dict[str, Any]:
    """Map Venus handoff post item to ``PostDraftPayload``-compatible dict.

    Instagram captions are assembled in ``ContainerBuilder`` from ``caption`` + ``cta``
    + hashtags, and **do not** read ``hook`` separately — so ``caption`` must carry the
    hook + main body per the approved handoff (see module docstring).
    """
    hook = str(post.get("hook") or "").strip()
    body_text = _handoff_post_body_text(post)
    title = str(post.get("title") or "").strip() or "Venus weekly"
    caption_first = _instagram_caption_first_block(hook=hook, body=body_text, title=title)
    return {
        "title": title,
        "hook": hook,
        "caption": caption_first,
        "cta": str(post.get("cta") or ""),
        "hashtags": _normalize_hashtag_list(post.get("hashtags")),
        "metadata": {
            "source": "venus_weekly_handoff",
            "handoff_version": post.get("version"),
        },
    }


def _mime_for_storage_key(key: str) -> str:
    guess, _enc = mimetypes.guess_type(key.replace("\\", "/"))
    if guess in ("image/png", "image/jpeg"):
        return guess
    lower = key.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    return "image/png"


def _looks_like_public_url(value: str) -> bool:
    v = (value or "").strip().lower()
    return v.startswith("http://") or v.startswith("https://")


class _DirectURLAwareStorage(StorageBackend):
    """Delegate to storage, but pass through already-public URLs unchanged."""

    def __init__(self, base: StorageBackend) -> None:
        self._base = base

    def save(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        return self._base.save(key, data, content_type=content_type)

    def url(self, key: str) -> str:
        if _looks_like_public_url(key):
            return key
        return self._base.url(key)

    def absolute_path(self, key: str) -> Path | None:
        return self._base.absolute_path(key)


def _asset_file_must_exist(settings: Settings, storage_key: str) -> Path:
    assets_root = Path(settings.assets_dir)
    rel = storage_key.replace("\\", "/").lstrip("/")
    path = assets_root / rel
    if not path.is_file():
        raise ValueError(
            f"Post image not found on disk for storage key {storage_key!r} "
            f"(resolved {path}). Place the image under ASSETS_DIR or fix --post-image-storage-key."
        )
    return path


def build_meta_client(settings: Settings) -> MetaInstagramClient | None:
    token = settings.instagram_access_token
    if not token:
        return None
    return MetaInstagramClient(
        access_token=token,
        base_url=settings.instagram_graph_base_url,
    )


ItemStatus = Literal["succeeded", "failed", "skipped_not_supported_by_publisher_mvp", "blocked"]


@dataclass
class RealPublishItemResult:
    role: str
    status: ItemStatus
    detail: str | None = None
    publish_job_id: str | None = None
    external_container_id: str | None = None
    ig_media_id: str | None = None
    draft_id: str | None = None
    error: str | None = None
    error_type: str | None = None
    publish_retryable: bool | None = None
    meta_status_code: int | None = None
    meta_error_body: str | None = None
    meta_error_json: dict[str, Any] | list[Any] | None = None
    meta_error_code: int | None = None
    meta_error_subcode: int | None = None
    meta_error_type: str | None = None
    meta_error_message: str | None = None
    meta_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "status": self.status,
            "detail": self.detail,
            "publish_job_id": self.publish_job_id,
            "external_container_id": self.external_container_id,
            "ig_media_id": self.ig_media_id,
            "draft_id": self.draft_id,
            "error": self.error,
            "error_type": self.error_type,
            "publish_retryable": self.publish_retryable,
            "meta_status_code": self.meta_status_code,
            "meta_error_body": self.meta_error_body,
            "meta_error_json": self.meta_error_json,
            "meta_error_code": self.meta_error_code,
            "meta_error_subcode": self.meta_error_subcode,
            "meta_error_type": self.meta_error_type,
            "meta_error_message": self.meta_error_message,
            "meta_url": self.meta_url,
        }


PublishOutcome = Literal["published", "publish_failed", "publish_partial", "publish_blocked"]


@dataclass
class RealPublishRunResult:
    week_start: str
    week_end: str
    publish_status: PublishOutcome
    final_check_passed: bool
    items: list[RealPublishItemResult] = field(default_factory=list)
    blocked_reason: str | None = None
    attempted_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    handoff_file: str | None = None
    final_check_file: str | None = None
    state_file: str | None = None
    publish_attempt_count: int = 1
    publish_error_type: str | None = None
    publish_error_message: str | None = None
    publish_retryable: bool | None = None
    meta_status_code: int | None = None
    meta_error_body: str | None = None
    meta_error_json: dict[str, Any] | list[Any] | None = None
    meta_error_code: int | None = None
    meta_error_subcode: int | None = None
    meta_error_type: str | None = None
    meta_error_message: str | None = None
    meta_url: str | None = None
    last_publish_attempt_at: str | None = None

    def succeeded_count(self) -> int:
        return sum(1 for i in self.items if i.status == "succeeded")

    def failed_count(self) -> int:
        return sum(1 for i in self.items if i.status == "failed")

    def to_artifact_dict(self) -> dict[str, Any]:
        return {
            "version": 2,
            "week_start": self.week_start,
            "week_end": self.week_end,
            "publish_status": self.publish_status,
            "final_check_passed": self.final_check_passed,
            "attempted_at": self.attempted_at,
            "last_publish_attempt_at": self.last_publish_attempt_at or self.attempted_at,
            "publish_attempt_count": self.publish_attempt_count,
            "publish_error_type": self.publish_error_type,
            "publish_error_message": self.publish_error_message,
            "publish_retryable": self.publish_retryable,
            "meta_status_code": self.meta_status_code,
            "meta_error_body": self.meta_error_body,
            "meta_error_json": self.meta_error_json,
            "meta_error_code": self.meta_error_code,
            "meta_error_subcode": self.meta_error_subcode,
            "meta_error_type": self.meta_error_type,
            "meta_error_message": self.meta_error_message,
            "meta_url": self.meta_url,
            "blocked_reason": self.blocked_reason,
            "handoff_file": self.handoff_file,
            "final_check_file": self.final_check_file,
            "state_file": self.state_file,
            "items": [i.to_dict() for i in self.items],
        }


def _rollup_publish_status(items: list[RealPublishItemResult]) -> PublishOutcome:
    post = next((i for i in items if i.role == "post"), None)
    if post is None:
        return "publish_failed"
    if post.status == "blocked":
        return "publish_blocked"
    if post.status == "failed":
        return "publish_failed"
    if post.status != "succeeded":
        return "publish_failed"
    # Post is the only channel wired to IG; reel/support are explicit non-API skips.
    others = [i for i in items if i.role != "post"]
    if any(i.status == "failed" for i in others):
        return "publish_partial"
    if any(i.status == "skipped_not_supported_by_publisher_mvp" for i in others):
        return "publish_partial"
    return "published"


def next_action_hint(run: RealPublishRunResult) -> str:
    """One-line operator hint for the CLI summary (manual retry only; no scheduler)."""
    if run.publish_status == "published":
        return "No action required for the main post; reel/support remain outside the current Instagram publisher MVP."
    if run.publish_status == "publish_partial":
        return (
            "Post reached Instagram (or succeeded in-app); reel/support were not sent by design. "
            "Treat reel/support separately if needed."
        )
    if run.publish_status == "publish_blocked":
        if run.publish_error_type in ("missing_instagram_token", "missing_instagram_account", "missing_media_asset"):
            return "Fix the blocking prerequisite, then re-run the same publish command (manual retry)."
        if run.publish_error_type == "gates_not_met":
            return "Resolve approval/final-check gates, then re-run publish."
        return "Clear the blocked condition documented in publish_error_message, then re-run."
    if run.publish_status == "publish_failed":
        if run.publish_retryable:
            return "Failure may be transient — you may re-run the publish command after a short wait (manual retry)."
        return "Fix the underlying issue (payload, media, token, or draft state), then re-run publish."
    return "Review real_publish artifact and state fields, then re-run if appropriate."


def build_prerequisite_blocked_publish_result(
    *,
    paths: WeekArtifactPaths,
    handoff: dict[str, Any],
    state: dict[str, Any],
    publish_attempt_count: int,
    blocked_reason: str,
    classification: PublishFailureClassification,
) -> RealPublishRunResult:
    """When publish never reaches ``PublisherService`` (token, DB row, missing file, etc.)."""
    ws = paths.week_start
    we = str(state.get("week_end") or handoff.get("week_end") or "")
    items: list[RealPublishItemResult] = [
        RealPublishItemResult(
            role="post",
            status="blocked",
            error=classification.message,
            error_type=classification.error_type,
            publish_retryable=classification.publish_retryable,
            detail=blocked_reason,
        ),
    ]
    for role in ("reel", "support"):
        if any(isinstance(it, dict) and it.get("type") == role for it in handoff.get("items") or []):
            items.append(
                RealPublishItemResult(
                    role=role,
                    status="blocked",
                    error="Not attempted — prerequisite blocked before Instagram API.",
                    error_type="prerequisite_blocked",
                    publish_retryable=False,
                    detail=blocked_reason,
                ),
            )
    return RealPublishRunResult(
        week_start=ws,
        week_end=we,
        publish_status="publish_blocked",
        final_check_passed=True,
        items=items,
        blocked_reason=blocked_reason,
        handoff_file=paths.handoff_path.name,
        final_check_file=paths.final_check_path.name,
        state_file=paths.state_path.name,
        publish_attempt_count=publish_attempt_count,
        publish_error_type=classification.error_type,
        publish_error_message=classification.message,
        publish_retryable=classification.publish_retryable,
    )


def build_value_error_publish_result(
    *,
    paths: WeekArtifactPaths,
    handoff: dict[str, Any],
    state: dict[str, Any],
    publish_attempt_count: int,
    exc: ValueError,
) -> RealPublishRunResult:
    """Normalize ``ValueError`` from validation / missing files into a persisted run result."""
    cls = classify_exception(exc)
    if cls.error_type == "missing_media_asset":
        return build_prerequisite_blocked_publish_result(
            paths=paths,
            handoff=handoff,
            state=state,
            publish_attempt_count=publish_attempt_count,
            blocked_reason=str(exc),
            classification=cls,
        )
    ws = paths.week_start
    we = str(state.get("week_end") or handoff.get("week_end") or "")
    post_item = RealPublishItemResult(
        role="post",
        status="failed",
        error=str(exc),
        error_type=cls.error_type,
        publish_retryable=cls.publish_retryable,
    )
    items: list[RealPublishItemResult] = [post_item]
    for role in ("reel", "support"):
        if any(isinstance(it, dict) and it.get("type") == role for it in handoff.get("items") or []):
            items.append(
                RealPublishItemResult(
                    role=role,
                    status="blocked",
                    error="Not attempted — post path failed before Instagram API.",
                    error_type="upstream_post_validation",
                    publish_retryable=False,
                ),
            )
    return RealPublishRunResult(
        week_start=ws,
        week_end=we,
        publish_status="publish_failed",
        final_check_passed=True,
        items=items,
        handoff_file=paths.handoff_path.name,
        final_check_file=paths.final_check_path.name,
        state_file=paths.state_path.name,
        publish_attempt_count=publish_attempt_count,
        publish_error_type=cls.error_type,
        publish_error_message=cls.message,
        publish_retryable=cls.publish_retryable,
    )


def build_gate_blocked_publish_result(
    *,
    paths: WeekArtifactPaths,
    handoff: dict[str, Any],
    state: dict[str, Any],
    publish_attempt_count: int,
    gate_message: str,
) -> RealPublishRunResult:
    """Approval or final-check gates failed — no Instagram or DB publish side-effects."""
    cls = PublishFailureClassification(
        error_type="gates_not_met",
        publish_retryable=False,
        message=gate_message,
    )
    ws = paths.week_start
    we = str(state.get("week_end") or handoff.get("week_end") or "")
    items = [
        RealPublishItemResult(
            role="post",
            status="blocked",
            error=gate_message,
            error_type=cls.error_type,
            publish_retryable=False,
            detail="Approval/final-check gates not satisfied.",
        ),
    ]
    for role in ("reel", "support"):
        if any(isinstance(it, dict) and it.get("type") == role for it in handoff.get("items") or []):
            items.append(
                RealPublishItemResult(
                    role=role,
                    status="blocked",
                    error="Not attempted — gates not satisfied.",
                    error_type="gates_not_met",
                    publish_retryable=False,
                    detail=gate_message,
                ),
            )
    return RealPublishRunResult(
        week_start=ws,
        week_end=we,
        publish_status="publish_blocked",
        final_check_passed=False,
        items=items,
        blocked_reason=gate_message,
        handoff_file=paths.handoff_path.name,
        final_check_file=paths.final_check_path.name,
        state_file=paths.state_path.name,
        publish_attempt_count=publish_attempt_count,
        publish_error_type=cls.error_type,
        publish_error_message=cls.message,
        publish_retryable=False,
    )


def run_venus_weekly_real_publish(
    db: Session,
    *,
    settings: Settings,
    paths: WeekArtifactPaths,
    handoff: dict[str, Any],
    state: dict[str, Any],
    final_check: dict[str, Any],
    brand_profile_id: str,
    instagram_account_id: str,
    post_image_storage_key: str | None,
    ig_client: InstagramClientProtocol,
    storage: StorageBackend,
    post_image_url: str | None = None,
    existing_post_draft_id: str | None = None,
    publish_attempt_count: int = 1,
) -> RealPublishRunResult:
    """Create (or reuse) an approved post draft + asset, then run ``PublisherService`` for the main post.

    *existing_post_draft_id*: if set, skip creating a draft; publish this draft (must be approved, type post,
    and have at least one image asset).
    """
    assert_publish_gates(state=state, final_check=final_check)
    ws = paths.week_start
    we = str(state.get("week_end") or handoff.get("week_end") or "")

    items: list[RealPublishItemResult] = []
    for role in ("reel", "support"):
        if any(isinstance(it, dict) and it.get("type") == role for it in handoff.get("items") or []):
            items.append(
                RealPublishItemResult(
                    role=role,
                    status="skipped_not_supported_by_publisher_mvp",
                    detail=(
                        "PublisherService / ContainerBuilder MVP only supports draft_type='post' "
                        "with an image asset. Reel/support are not sent to the Instagram API."
                    ),
                    error_type="publisher_mvp_not_supported",
                    publish_retryable=False,
                )
            )

    draft_repo = DraftRepository()
    asset_repo = AssetRepository()
    publisher_storage: StorageBackend = _DirectURLAwareStorage(storage) if post_image_url else storage
    publisher = PublisherService(ig_client=ig_client, storage=publisher_storage)
    draft_id: str

    try:
        if not existing_post_draft_id and not post_image_url:
            if not post_image_storage_key:
                raise ValueError("post_image_storage_key is required when post_image_url is not provided")
            _asset_file_must_exist(settings, post_image_storage_key)

        post_item = _find_handoff_post(handoff)
        payload_from_handoff = handoff_post_to_draft_payload(post_item)

        if existing_post_draft_id:
            draft = draft_repo.get_by_id(db, existing_post_draft_id)
            if draft is None:
                raise ValueError(f"draft not found: {existing_post_draft_id}")
            if draft.draft_type != "post":
                raise ValueError(f"draft {existing_post_draft_id} must be draft_type 'post', got {draft.draft_type!r}")
            if draft.status != "approved":
                raise ValueError(f"draft {existing_post_draft_id} must be approved (status={draft.status!r})")
            if draft.brand_profile_id != brand_profile_id:
                raise ValueError(
                    f"draft.brand_profile_id ({draft.brand_profile_id!r}) != "
                    f"expected brand_profile_id ({brand_profile_id!r})"
                )
            draft_id = draft.id
            draft.payload = payload_from_handoff
            draft.text = (payload_from_handoff.get("caption") or "")[:500]
            db.add(draft)
            assets = asset_repo.list_for_draft(db, draft_id)
            if not assets:
                raise ValueError(f"draft {draft_id} has no assets; add an image asset before publishing")
            if post_image_url:
                primary_asset = assets[0]
                primary_asset.storage_path = post_image_url.strip()
                primary_asset.mime_type = "image/jpeg"
                db.add(primary_asset)
            db.commit()
            db.refresh(draft)
        else:
            payload = payload_from_handoff
            text_preview = (payload.get("caption") or "")[:500]
            draft = draft_repo.create(
                db,
                brand_profile_id=brand_profile_id,
                content_plan_id=None,
                draft_type="post",
                text=text_preview,
                payload=payload,
            )
            db.flush()
            draft_id = draft.id
            draft_repo.approve(db, draft)
            asset_storage_path = (
                post_image_url.strip()
                if post_image_url
                else str(post_image_storage_key or "").replace("\\", "/").lstrip("/")
            )
            asset_mime = "image/jpeg" if post_image_url else _mime_for_storage_key(str(post_image_storage_key or ""))
            asset_repo.create(
                db,
                brand_profile_id=brand_profile_id,
                draft_id=draft_id,
                asset_type="image",
                storage_path=asset_storage_path,
                mime_type=asset_mime,
                width=None,
                height=None,
                meta={
                    "source": "venus_weekly_real_publish",
                    "image_source": "direct_url" if post_image_url else "storage_key",
                },
            )
            db.commit()
            db.refresh(draft)
    except ValueError as exc:
        return build_value_error_publish_result(
            paths=paths,
            handoff=handoff,
            state=state,
            publish_attempt_count=publish_attempt_count,
            exc=exc,
        )

    post_result = RealPublishItemResult(role="post", status="failed", draft_id=draft_id)
    items.insert(0, post_result)

    try:
        job = publisher.create_job(
            db,
            draft_id=draft_id,
            instagram_account_id=instagram_account_id,
        )
        post_result.publish_job_id = job.id
        db.refresh(job)
        if job.external_container_id:
            post_result.external_container_id = job.external_container_id
    except Exception as exc:
        cls = classify_exception(exc)
        post_result.status = "failed"
        post_result.error = cls.message
        post_result.error_type = cls.error_type
        post_result.publish_retryable = cls.publish_retryable
        db.rollback()
        return RealPublishRunResult(
            week_start=ws,
            week_end=we,
            publish_status="publish_failed",
            final_check_passed=True,
            items=items,
            handoff_file=paths.handoff_path.name,
            final_check_file=paths.final_check_path.name,
            state_file=paths.state_path.name,
            publish_attempt_count=publish_attempt_count,
            publish_error_type=cls.error_type,
            publish_error_message=cls.message,
            publish_retryable=cls.publish_retryable,
        )

    result = publisher.execute_job(db, job_id=post_result.publish_job_id or "")
    post_result.external_container_id = result.publish_job.external_container_id
    if result.succeeded and result.published_post is not None:
        post_result.status = "succeeded"
        post_result.ig_media_id = result.published_post.ig_media_id
        post_result.error = None
        post_result.error_type = None
        post_result.publish_retryable = None
    else:
        cls = classify_message(result.error or "")
        post_result.status = "failed"
        post_result.error = result.error
        post_result.error_type = cls.error_type
        post_result.publish_retryable = cls.publish_retryable
        if result.meta_error:
            post_result.meta_status_code = result.meta_error.get("meta_status_code")
            post_result.meta_error_body = result.meta_error.get("meta_error_body")
            post_result.meta_error_json = result.meta_error.get("meta_error_json")
            post_result.meta_error_code = result.meta_error.get("meta_error_code")
            post_result.meta_error_subcode = result.meta_error.get("meta_error_subcode")
            post_result.meta_error_type = result.meta_error.get("meta_error_type")
            post_result.meta_error_message = result.meta_error.get("meta_error_message")
            post_result.meta_url = result.meta_error.get("meta_url")

    overall = _rollup_publish_status(items)
    err_t = None
    err_m = None
    retry_top: bool | None = None
    if overall == "publish_failed":
        err_t = post_result.error_type
        err_m = post_result.error
        retry_top = post_result.publish_retryable
    elif overall == "publish_partial":
        retry_top = False
    return RealPublishRunResult(
        week_start=ws,
        week_end=we,
        publish_status=overall,
        final_check_passed=True,
        items=items,
        handoff_file=paths.handoff_path.name,
        final_check_file=paths.final_check_path.name,
        state_file=paths.state_path.name,
        publish_attempt_count=publish_attempt_count,
        publish_error_type=err_t,
        publish_error_message=err_m,
        publish_retryable=retry_top,
        meta_status_code=post_result.meta_status_code,
        meta_error_body=post_result.meta_error_body,
        meta_error_json=post_result.meta_error_json,
        meta_error_code=post_result.meta_error_code,
        meta_error_subcode=post_result.meta_error_subcode,
        meta_error_type=post_result.meta_error_type,
        meta_error_message=post_result.meta_error_message,
        meta_url=post_result.meta_url,
    )


def merge_state_with_publish_result(state: dict[str, Any], run: RealPublishRunResult) -> dict[str, Any]:
    """Return a shallow copy of *state* with ``real_publish`` and top-level publish fields updated."""
    out = dict(state)
    out["real_publish"] = run.to_artifact_dict()
    out["publish_status"] = run.publish_status
    out["publish_attempt_count"] = run.publish_attempt_count
    out["last_publish_attempt_at"] = run.last_publish_attempt_at or run.attempted_at
    out["publish_error_type"] = run.publish_error_type
    out["publish_error_message"] = run.publish_error_message
    out["publish_retryable"] = run.publish_retryable
    if run.publish_status == "published" or run.publish_status == "publish_partial":
        if any(i.status == "succeeded" for i in run.items):
            out["publish_timestamp"] = run.attempted_at
    if run.publish_status in ("publish_blocked", "publish_failed"):
        out.pop("publish_timestamp", None)
    out["publish_note"] = (
        f"real_publish v2 — {run.publish_status} "
        f"(post={'ok' if any(i.role == 'post' and i.status == 'succeeded' for i in run.items) else 'no'}; "
        f"attempt={run.publish_attempt_count})"
    )
    return out


def persist_publish_artifacts(
    *,
    paths: WeekArtifactPaths,
    state: dict[str, Any],
    run: RealPublishRunResult,
) -> tuple[Path, dict[str, Any]]:
    """Write ``venus_real_publish_<week>.json`` and merged weekly state JSON."""
    artifact_path = paths.week_dir / f"venus_real_publish_{paths.week_start}.json"
    merged = merge_state_with_publish_result(state, run)
    artifact_path.write_text(json.dumps(run.to_artifact_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths.state_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return artifact_path, merged


__all__ = [
    "PublishOutcome",
    "RealPublishItemResult",
    "RealPublishRunResult",
    "WeekArtifactPaths",
    "assert_publish_gates",
    "build_gate_blocked_publish_result",
    "build_meta_client",
    "build_prerequisite_blocked_publish_result",
    "build_value_error_publish_result",
    "get_local_storage",
    "handoff_post_to_draft_payload",
    "load_json",
    "merge_state_with_publish_result",
    "next_action_hint",
    "next_publish_attempt_count",
    "persist_publish_artifacts",
    "resolve_week_artifacts",
    "run_venus_weekly_real_publish",
]
