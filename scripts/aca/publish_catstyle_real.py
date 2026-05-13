#!/usr/bin/env python3
"""CLI: Catstyle publish handoff → Cloudinary (optional) + Instagram via ``PublisherService``."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import REPO_ROOT, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.core.repo_env import load_repo_dotenv_if_present, resolve_publish_target_ids

load_repo_dotenv_if_present(REPO_ROOT)

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.session import SessionLocal
from astro_content_agent.services.content.catstyle_real_publish import (
    CatstyleRealPublishError,
    CatstyleRealPublishResult,
    assert_handoff_publishable,
    load_catstyle_handoff_json,
    persist_catstyle_publish_artifacts,
    read_caption_final,
    resolve_local_image_path_for_publish,
    run_catstyle_real_publish,
    validate_catstyle_publish_environment,
    validate_db_accounts,
)
from astro_content_agent.services.content.venus_publish_failure import PublishFailureClassification, classify_exception
from astro_content_agent.services.content.venus_weekly_real_publish import build_meta_client
from astro_content_agent.services.media.cloudinary_uploader import upload_local_image, validate_cloudinary_config


def _persist_prereq(
    handoff_dir: Path,
    *,
    publish_status: str,
    error_message: str | None = None,
    error_type: str | None = None,
    publish_retryable: bool | None = None,
    detail: str | None = None,
    extra: dict | None = None,
) -> None:
    r = CatstyleRealPublishResult(
        publish_status=publish_status,
        error_message=error_message,
        error_type=error_type,
        publish_retryable=publish_retryable,
        detail=detail,
        extra=extra or {},
        validate_only=False,
    )
    persist_catstyle_publish_artifacts(handoff_dir, r)


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish Catstyle aspect post from publish handoff via PublisherService.")
    ap.add_argument("--handoff-dir", type=Path, required=True, help="Directory containing publish_handoff.json")
    ap.add_argument(
        "--local-image-path",
        type=Path,
        default=None,
        help="Local image file; uploaded to Cloudinary unless --post-image-url is set. "
        "If omitted, primary_image_path.txt in the handoff dir is used.",
    )
    ap.add_argument(
        "--post-image-url",
        default=None,
        help="Public https image URL for Meta (skips Cloudinary upload).",
    )
    ap.add_argument("--validate-only", action="store_true", help="Check handoff, files, env, and DB; no publish")
    ap.add_argument("--brand-profile-id", default=None, help="Or set ACA_BRAND_PROFILE_ID")
    ap.add_argument("--instagram-account-id", default=None, help="Or set ACA_INSTAGRAM_ACCOUNT_ID")
    args = ap.parse_args()

    handoff_dir = Path(args.handoff_dir).expanduser().resolve()
    if not handoff_dir.is_dir():
        print(f"Handoff directory not found: {handoff_dir}", file=sys.stderr)
        return 2

    settings = get_settings()
    brand_id, ig_account_id = resolve_publish_target_ids(
        cli_brand_profile_id=args.brand_profile_id,
        cli_instagram_account_id=args.instagram_account_id,
    )

    try:
        handoff = load_catstyle_handoff_json(handoff_dir)
    except CatstyleRealPublishError as e:
        _persist_prereq(handoff_dir, publish_status="blocked_handoff", error_message=str(e), error_type="invalid_handoff")
        print(str(e), file=sys.stderr)
        return 1

    try:
        assert_handoff_publishable(handoff)
    except CatstyleRealPublishError as e:
        _persist_prereq(
            handoff_dir,
            publish_status="blocked_not_ready",
            error_message=str(e),
            error_type="handoff_not_publishable",
            publish_retryable=False,
        )
        print(str(e), file=sys.stderr)
        return 1

    try:
        caption = read_caption_final(handoff_dir, handoff)
        if not caption.strip():
            raise CatstyleRealPublishError("caption_final is empty (caption_final.txt or publish_handoff.json).")
    except CatstyleRealPublishError as e:
        _persist_prereq(handoff_dir, publish_status="blocked_handoff", error_message=str(e), error_type="invalid_caption")
        print(str(e), file=sys.stderr)
        return 1

    hook = str(handoff.get("hook") or "").strip()
    if not hook:
        msg = "publish_handoff.json missing non-empty hook."
        _persist_prereq(handoff_dir, publish_status="blocked_handoff", error_message=msg, error_type="invalid_hook")
        print(msg, file=sys.stderr)
        return 1

    post_url = (args.post_image_url or "").strip() or None
    if post_url and args.local_image_path is not None:
        msg = "Pass at most one of --post-image-url and --local-image-path."
        _persist_prereq(handoff_dir, publish_status="blocked_prerequisites", error_message=msg, error_type="invalid_args")
        print(msg, file=sys.stderr)
        return 2

    need_cloudinary = post_url is None
    image_public_url: str | None = post_url

    resolved_local: Path | None = None
    try:
        if post_url is None:
            resolved_local = resolve_local_image_path_for_publish(
                handoff_dir,
                local_image_path=args.local_image_path,
                handoff=handoff,
            )
    except CatstyleRealPublishError as e:
        _persist_prereq(handoff_dir, publish_status="blocked_prerequisites", error_message=str(e), error_type="missing_image")
        print(str(e), file=sys.stderr)
        return 1

    if post_url is not None and not post_url.lower().startswith("https://"):
        msg = "--post-image-url must be an https:// URL."
        _persist_prereq(handoff_dir, publish_status="blocked_prerequisites", error_message=msg, error_type="invalid_image_url")
        print(msg, file=sys.stderr)
        return 1

    missing_env = validate_catstyle_publish_environment(settings=settings, need_cloudinary_upload=need_cloudinary)
    if missing_env:
        msg = "Missing required environment variables: " + ", ".join(missing_env)
        _persist_prereq(
            handoff_dir,
            publish_status="blocked_prerequisites",
            error_message=msg,
            error_type="missing_environment",
            publish_retryable=False,
            extra={"missing_environment_variables": missing_env},
        )
        print(msg, file=sys.stderr)
        return 1

    if need_cloudinary:
        try:
            validate_cloudinary_config(settings)
        except ValueError as e:
            _persist_prereq(
                handoff_dir,
                publish_status="blocked_prerequisites",
                error_message=str(e),
                error_type="cloudinary_config_invalid",
                publish_retryable=False,
            )
            print(str(e), file=sys.stderr)
            return 1

    if not brand_id or not ig_account_id:
        msg = (
            "Provide --brand-profile-id and --instagram-account-id, "
            "or set ACA_BRAND_PROFILE_ID / ACA_INSTAGRAM_ACCOUNT_ID in the repo-root .env file."
        )
        _persist_prereq(
            handoff_dir,
            publish_status="blocked_prerequisites",
            error_message=msg,
            error_type="missing_publish_targets",
            publish_retryable=False,
        )
        print(msg, file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        db_errs = validate_db_accounts(db, brand_profile_id=brand_id, instagram_account_id=ig_account_id)
        if db_errs:
            msg = "; ".join(db_errs)
            _persist_prereq(
                handoff_dir,
                publish_status="blocked_prerequisites",
                error_message=msg,
                error_type="database_prerequisites",
                publish_retryable=False,
            )
            print(msg, file=sys.stderr)
            return 1
    finally:
        db.close()

    if args.validate_only:
        db = SessionLocal()
        try:
            ig_client = build_meta_client(settings)
            if ig_client is None:
                msg = "INSTAGRAM_ACCESS_TOKEN is not set (internal check after env validation)."
                _persist_prereq(
                    handoff_dir,
                    publish_status="blocked_prerequisites",
                    error_message=msg,
                    error_type="missing_instagram_token",
                    publish_retryable=False,
                )
                print(msg, file=sys.stderr)
                return 1
            r = run_catstyle_real_publish(
                db,
                settings=settings,
                handoff_dir=handoff_dir,
                handoff=handoff,
                caption_final=caption,
                hook=hook,
                image_public_url=image_public_url,
                brand_profile_id=brand_id,
                instagram_account_id=ig_account_id,
                ig_client=ig_client,
                validate_only=True,
            )
        finally:
            db.close()
        jp, mp = persist_catstyle_publish_artifacts(handoff_dir, r)
        print(f"validate_only_ok (artifacts: {jp.name}, {mp.name})")
        return 0

    if image_public_url is None:
        assert resolved_local is not None
        try:
            cu = upload_local_image(settings, resolved_local)
        except (ValueError, OSError, RuntimeError) as e:
            cls = classify_exception(e)
            r = CatstyleRealPublishResult(
                publish_status="publish_failed",
                error_type=cls.error_type,
                error_message=cls.message,
                publish_retryable=cls.publish_retryable,
            )
            persist_catstyle_publish_artifacts(handoff_dir, r)
            print(str(e), file=sys.stderr)
            return 1
        image_public_url = cu.secure_url

    ig_client = build_meta_client(settings)
    if ig_client is None:
        cls = PublishFailureClassification(
            error_type="missing_instagram_token",
            publish_retryable=False,
            message="Set INSTAGRAM_ACCESS_TOKEN in environment (.env). Token value is not printed here.",
        )
        _persist_prereq(
            handoff_dir,
            publish_status="blocked_prerequisites",
            error_message=cls.message,
            error_type=cls.error_type,
            publish_retryable=False,
        )
        print(cls.message, file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        r = run_catstyle_real_publish(
            db,
            settings=settings,
            handoff_dir=handoff_dir,
            handoff=handoff,
            caption_final=caption,
            hook=hook,
            image_public_url=image_public_url,
            brand_profile_id=brand_id,
            instagram_account_id=ig_account_id,
            ig_client=ig_client,
            validate_only=False,
        )
    finally:
        db.close()

    persist_catstyle_publish_artifacts(handoff_dir, r)
    print(f"publish_status={r.publish_status}")
    if r.error_message:
        print(r.error_message, file=sys.stderr)
    ok = r.publish_status == "published"
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
