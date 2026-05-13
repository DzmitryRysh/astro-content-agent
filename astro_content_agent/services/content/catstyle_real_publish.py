"""Catstyle publish handoff → Cloudinary (optional) + ``PublisherService`` (Instagram image post).

Reuses the same draft/asset/job flow as ``venus_weekly_real_publish`` for ``draft_type='post'``.
Does not modify Venus weekly modules or behavior.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from astro_content_agent.core.config import Settings
from astro_content_agent.db.models import BrandProfile, InstagramAccount
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.services.content.venus_publish_failure import classify_exception, classify_publish_result_meta
from astro_content_agent.services.content.venus_weekly_real_publish import (
    _DirectURLAwareStorage,
    build_meta_client,
)
from astro_content_agent.services.instagram.client import InstagramClientProtocol, redact_access_token_from_url
from astro_content_agent.services.instagram.publisher import PublisherService
from astro_content_agent.services.media.cloudinary_uploader import upload_local_image, validate_cloudinary_config
from astro_content_agent.services.media.storage import StorageBackend
from astro_content_agent.services.media.url_builder import get_local_storage

CATSTYLE_READY_PUBLISH_STATUSES: frozenset[str] = frozenset({"ready_for_manual_publish"})


class CatstyleRealPublishError(ValueError):
    """Invalid handoff, paths, or prerequisites for Catstyle real publish."""


@dataclass
class CatstyleRealPublishResult:
    publish_status: str
    published_at: str | None = None
    image_url_used: str | None = None
    instagram_media_id: str | None = None
    instagram_container_id: str | None = None
    publish_job_id: str | None = None
    draft_id: str | None = None
    brand_profile_id: str | None = None
    instagram_account_id: str | None = None
    validate_only: bool = False
    error_type: str | None = None
    error_message: str | None = None
    publish_retryable: bool | None = None
    publish_attempt_count: int | None = None
    meta_error_code: int | None = None
    meta_error_subcode: int | None = None
    detail: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def load_catstyle_handoff_json(handoff_dir: Path) -> dict[str, Any]:
    hp = Path(handoff_dir).expanduser().resolve() / "publish_handoff.json"
    if not hp.is_file():
        raise CatstyleRealPublishError(f"Missing publish_handoff.json in {handoff_dir}")
    data = json.loads(hp.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CatstyleRealPublishError("publish_handoff.json root must be a JSON object.")
    return data


def read_caption_final(handoff_dir: Path, handoff: dict[str, Any]) -> str:
    tf = Path(handoff_dir).expanduser().resolve() / "caption_final.txt"
    if tf.is_file():
        return tf.read_text(encoding="utf-8-sig").strip()
    return str(handoff.get("caption_final") or "").strip()


def read_primary_image_path_file(handoff_dir: Path) -> str:
    pf = Path(handoff_dir).expanduser().resolve() / "primary_image_path.txt"
    if not pf.is_file():
        raise CatstyleRealPublishError(f"Missing primary_image_path.txt in {handoff_dir} (or pass --local-image-path).")
    return pf.read_text(encoding="utf-8-sig").strip()


def assert_handoff_publishable(handoff: dict[str, Any]) -> None:
    st = str(handoff.get("publish_status") or "").strip()
    if st not in CATSTYLE_READY_PUBLISH_STATUSES:
        raise CatstyleRealPublishError(
            f"publish_status must be one of {sorted(CATSTYLE_READY_PUBLISH_STATUSES)!r}; got {st!r}."
        )


def catstyle_handoff_to_draft_payload(*, hook: str, caption_final: str, date: str) -> dict[str, Any]:
    """Map Catstyle handoff fields to ``PostDraftPayload``-compatible dict."""
    h = hook.strip()
    c = caption_final.strip()
    caption = f"{h}\n\n{c}" if h and c else (c or h)
    title = f"Catstyle {date}".strip() or "Catstyle aspect post"
    return {
        "title": title,
        "hook": h,
        "caption": caption,
        "cta": "",
        "hashtags": [],
        "metadata": {"source": "catstyle_publish_handoff", "date": date},
    }


def missing_instagram_access_token(settings: Settings) -> bool:
    return not (settings.instagram_access_token or "").strip()


def missing_cloudinary_env_names(settings: Settings) -> list[str]:
    missing: list[str] = []
    if not (settings.cloudinary_cloud_name or "").strip():
        missing.append("CLOUDINARY_CLOUD_NAME")
    if not (settings.cloudinary_api_key or "").strip():
        missing.append("CLOUDINARY_API_KEY")
    if not (settings.cloudinary_api_secret or "").strip():
        missing.append("CLOUDINARY_API_SECRET")
    return missing


def redact_secrets_for_artifact(text: str) -> str:
    """Best-effort redaction for persisted artifacts (never echo raw tokens)."""
    if not text:
        return text
    s = redact_access_token_from_url(text)
    s = re.sub(r"(access_token|system_user_access_token)=([^&\s]+)", r"\1=<REDACTED>", s, flags=re.I)
    s = re.sub(r"\bIGA[\w.-]{10,}\b", "<REDACTED_INSTAGRAM_TOKEN>", s)
    s = re.sub(r"\bsk_live_[\w]+\b", "<REDACTED_SECRET_KEY>", s)
    return s


def resolve_local_image_path_for_publish(
    handoff_dir: Path,
    *,
    local_image_path: Path | None,
    handoff: dict[str, Any],
) -> Path:
    if local_image_path is not None:
        p = Path(local_image_path).expanduser().resolve()
    else:
        raw = read_primary_image_path_file(handoff_dir)
        p = Path(raw).expanduser().resolve()
    if not p.is_file():
        raise CatstyleRealPublishError(f"Image file not found: {p}")
    return p


def validate_catstyle_publish_environment(
    *,
    settings: Settings,
    need_cloudinary_upload: bool,
) -> list[str]:
    """Return list of missing *environment variable names* (values never included)."""
    missing: list[str] = []
    if missing_instagram_access_token(settings):
        missing.append("INSTAGRAM_ACCESS_TOKEN")
    if need_cloudinary_upload:
        missing.extend(missing_cloudinary_env_names(settings))
    return missing


def validate_db_accounts(
    db: Session,
    *,
    brand_profile_id: str,
    instagram_account_id: str,
) -> list[str]:
    """Return human-readable prerequisite errors (no secrets)."""
    errs: list[str] = []
    if db.get(BrandProfile, brand_profile_id) is None:
        errs.append(f"BrandProfile not found for id (verify --brand-profile-id).")
    acc = db.get(InstagramAccount, instagram_account_id)
    if acc is None:
        errs.append("InstagramAccount not found for id (verify --instagram-account-id).")
    elif not (acc.ig_user_id or "").strip():
        errs.append(
            "instagram_accounts.ig_user_id is empty for this account — set IG user id on the row "
            "or use an account that has completed Meta linking (numeric id, not @handle)."
        )
    return errs


def _create_catstyle_draft_and_asset(
    db: Session,
    *,
    settings: Settings,
    brand_profile_id: str,
    payload: dict[str, Any],
    image_public_url: str,
) -> str:
    """Create approved post draft + image asset whose storage_path is the public image URL."""
    draft_repo = DraftRepository()
    asset_repo = AssetRepository()
    text_preview = str(payload.get("caption") or "")[:500]
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
    asset_repo.create(
        db,
        brand_profile_id=brand_profile_id,
        draft_id=draft_id,
        asset_type="image",
        storage_path=image_public_url.strip(),
        mime_type="image/jpeg",
        width=None,
        height=None,
        meta={"source": "catstyle_real_publish", "image_source": "public_url"},
    )
    db.commit()
    db.refresh(draft)
    return draft_id


def run_catstyle_real_publish(
    db: Session,
    *,
    settings: Settings,
    handoff_dir: Path,
    handoff: dict[str, Any],
    caption_final: str,
    hook: str,
    image_public_url: str | None,
    brand_profile_id: str,
    instagram_account_id: str,
    ig_client: InstagramClientProtocol,
    validate_only: bool = False,
) -> CatstyleRealPublishResult:
    """Upload must be done by caller when needed.

    For real publish, *image_public_url* must be an HTTPS URL suitable for Meta.
    For *validate_only* with a pending local upload, *image_public_url* may be ``None``.
    """
    assert_handoff_publishable(handoff)
    date = str(handoff.get("date") or handoff_dir.name).strip()
    payload = catstyle_handoff_to_draft_payload(hook=hook, caption_final=caption_final, date=date)

    if validate_only:
        return CatstyleRealPublishResult(
            publish_status="validate_only_ok",
            image_url_used=image_public_url,
            validate_only=True,
            brand_profile_id=brand_profile_id,
            instagram_account_id=instagram_account_id,
            detail=(
                "Handoff gates, caption, image source, and DB prerequisites satisfied "
                "(no Instagram publish in validate-only mode)."
            ),
        )

    if not image_public_url or not str(image_public_url).strip().lower().startswith("https://"):
        return CatstyleRealPublishResult(
            publish_status="publish_failed",
            error_type="invalid_image_url",
            error_message="image_public_url must be a non-empty https:// URL for Meta ingestion.",
            publish_retryable=False,
            validate_only=False,
        )

    image_public_url = str(image_public_url).strip()

    storage = get_local_storage(settings)
    publisher_storage: StorageBackend = _DirectURLAwareStorage(storage)
    publisher = PublisherService(ig_client=ig_client, storage=publisher_storage)

    try:
        draft_id = _create_catstyle_draft_and_asset(
            db,
            settings=settings,
            brand_profile_id=brand_profile_id,
            payload=payload,
            image_public_url=image_public_url,
        )
    except Exception as exc:
        cls = classify_exception(exc)
        return CatstyleRealPublishResult(
            publish_status="publish_failed",
            error_type=cls.error_type,
            error_message=cls.message,
            publish_retryable=cls.publish_retryable,
            validate_only=False,
        )

    try:
        job = publisher.create_job(
            db,
            draft_id=draft_id,
            instagram_account_id=instagram_account_id,
        )
        result = publisher.execute_job(db, job_id=job.id)
    except Exception as exc:
        cls = classify_exception(exc)
        return CatstyleRealPublishResult(
            publish_status="publish_failed",
            draft_id=draft_id,
            error_type=cls.error_type,
            error_message=cls.message,
            publish_retryable=cls.publish_retryable,
            validate_only=False,
        )

    if result.succeeded and result.published_post is not None:
        job = result.publish_job
        return CatstyleRealPublishResult(
            publish_status="published",
            published_at=datetime.now(UTC).isoformat(),
            image_url_used=image_public_url,
            instagram_media_id=result.published_post.ig_media_id,
            instagram_container_id=job.external_container_id,
            publish_job_id=job.id,
            draft_id=draft_id,
            brand_profile_id=brand_profile_id,
            instagram_account_id=instagram_account_id,
            validate_only=False,
            publish_attempt_count=result.media_publish_attempts,
        )

    err = result.error or "unknown_error"
    meta = result.meta_error or {}
    mc = meta.get("meta_error_code") if isinstance(meta, dict) else None
    ms = meta.get("meta_error_subcode") if isinstance(meta, dict) else None
    try:
        meta_code = int(mc) if mc is not None else None
    except (TypeError, ValueError):
        meta_code = None
    try:
        meta_sub = int(ms) if ms is not None else None
    except (TypeError, ValueError):
        meta_sub = None

    cls = classify_publish_result_meta(error=err, meta_error=meta if isinstance(meta, dict) else None)
    fallback_et = "meta_publish_error" if meta else "publisher_execute_failed"
    error_type = cls.error_type if cls.error_type != "unknown" else fallback_et
    return CatstyleRealPublishResult(
        publish_status="publish_failed",
        draft_id=draft_id,
        publish_job_id=result.publish_job.id,
        instagram_container_id=result.publish_job.external_container_id,
        error_type=error_type,
        error_message=redact_secrets_for_artifact(err),
        publish_retryable=cls.publish_retryable,
        publish_attempt_count=result.media_publish_attempts,
        meta_error_code=meta_code,
        meta_error_subcode=meta_sub,
        validate_only=False,
        extra={"meta_error_keys": list(meta.keys()) if isinstance(meta, dict) else []},
    )


def result_to_public_dict(r: CatstyleRealPublishResult) -> dict[str, Any]:
    d = asdict(r)
    d.pop("extra", None)
    if r.error_message:
        d["error_message"] = redact_secrets_for_artifact(r.error_message)
    d.update(r.extra)
    return d


def render_catstyle_publish_result_markdown(r: CatstyleRealPublishResult) -> str:
    lines = [
        "# Catstyle publish result",
        "",
        f"- **publish_status:** `{r.publish_status}`",
        f"- **validate_only:** {r.validate_only}",
        f"- **published_at:** {r.published_at or '_(n/a)_'}",
        f"- **image_url_used:** {r.image_url_used or '_(n/a)_'}",
        f"- **instagram_media_id:** {r.instagram_media_id or '_(n/a)_'}",
        f"- **instagram_container_id:** {r.instagram_container_id or '_(n/a)_'}",
        f"- **publish_job_id:** {r.publish_job_id or '_(n/a)_'}",
        f"- **draft_id:** {r.draft_id or '_(n/a)_'}",
        f"- **publish_attempt_count:** {r.publish_attempt_count if r.publish_attempt_count is not None else '_(n/a)_'}",
        f"- **meta_error_code:** {r.meta_error_code if r.meta_error_code is not None else '_(n/a)_'}",
        f"- **meta_error_subcode:** {r.meta_error_subcode if r.meta_error_subcode is not None else '_(n/a)_'}",
        "",
    ]
    if r.error_message:
        lines.extend(
            [
                "## Error",
                "",
                redact_secrets_for_artifact(r.error_message),
                "",
                f"- **error_type:** `{r.error_type}`",
                f"- **publish_retryable:** {r.publish_retryable}",
                "",
            ]
        )
    if r.detail:
        lines.extend(["## Detail", "", r.detail, ""])
    return "\n".join(lines).rstrip() + "\n"


def persist_catstyle_publish_artifacts(handoff_dir: Path, r: CatstyleRealPublishResult) -> tuple[Path, Path]:
    out = Path(handoff_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    jp = out / "catstyle_publish_result.json"
    mp = out / "catstyle_publish_result.md"
    public = result_to_public_dict(r)
    jp.write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mp.write_text(render_catstyle_publish_result_markdown(r), encoding="utf-8")
    return jp, mp


__all__ = [
    "CATSTYLE_READY_PUBLISH_STATUSES",
    "CatstyleRealPublishError",
    "CatstyleRealPublishResult",
    "assert_handoff_publishable",
    "catstyle_handoff_to_draft_payload",
    "load_catstyle_handoff_json",
    "missing_cloudinary_env_names",
    "missing_instagram_access_token",
    "persist_catstyle_publish_artifacts",
    "read_caption_final",
    "read_primary_image_path_file",
    "redact_secrets_for_artifact",
    "render_catstyle_publish_result_markdown",
    "result_to_public_dict",
    "run_catstyle_real_publish",
    "validate_catstyle_publish_environment",
    "validate_db_accounts",
    "resolve_local_image_path_for_publish",
]
