#!/usr/bin/env python3
"""Thin CLI: Venus weekly real Instagram publish (delegates to service layer)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import default_week_dir, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.models import BrandProfile, InstagramAccount
from astro_content_agent.db.session import SessionLocal
from astro_content_agent.services.content import venus_weekly_real_publish as vrp
from astro_content_agent.services.content.venus_publish_failure import PublishFailureClassification, next_publish_attempt_count
from astro_content_agent.services.content.venus_weekly_real_publish import (
    assert_publish_gates,
    build_gate_blocked_publish_result,
    build_meta_client,
    build_prerequisite_blocked_publish_result,
    load_json,
    next_action_hint,
    persist_publish_artifacts,
    resolve_week_artifacts,
    run_venus_weekly_real_publish,
)
from astro_content_agent.services.media.cloudinary_uploader import upload_local_image, validate_cloudinary_config
from astro_content_agent.services.media.url_builder import get_local_storage
from astro_content_agent.services.content.weekly_publish_image_source import weekly_publish_image_mode


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish Venus weekly post via PublisherService.")
    ap.add_argument("week_start", help="YYYY-MM-DD")
    ap.add_argument("--instagram-account-id", required=True)
    ap.add_argument("--brand-profile-id", required=True)
    ap.add_argument("--post-image-storage-key", default=None)
    ap.add_argument("--post-image-url", default=None, help="Direct public image URL for Meta ingestion")
    ap.add_argument(
        "--post-image-path",
        type=Path,
        default=None,
        help="Local image path; uploaded to Cloudinary, then publish uses returned secure_url",
    )
    ap.add_argument("--validate-only", action="store_true", help="Check gates + disk asset + DB; no Instagram publish")
    ap.add_argument("--week-dir", type=Path, default=None)
    ap.add_argument("--state-file", type=Path, default=None)
    ap.add_argument("--handoff-file", type=Path, default=None)
    ap.add_argument("--final-check-file", type=Path, default=None)
    ap.add_argument("--existing-post-draft-id", default=None, help="Reuse existing approved post draft")
    args = ap.parse_args()

    try:
        mode = weekly_publish_image_mode(
            post_image_url=args.post_image_url,
            post_image_storage_key=args.post_image_storage_key,
            post_image_path=args.post_image_path,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    use_storage_key = mode == "storage_key"
    post_image_url_for_publish: str | None = None

    if mode == "path":
        path_img = Path(args.post_image_path).expanduser()
        if not path_img.is_file():
            print(f"Image file not found: {path_img.resolve()}", file=sys.stderr)
            return 1

    week_dir = default_week_dir(args.week_start, args.week_dir)
    if not week_dir.is_dir():
        print(f"Week dir not found: {week_dir}", file=sys.stderr)
        return 1

    try:
        paths = resolve_week_artifacts(
            week_dir=week_dir,
            week_start_hint=args.week_start,
            state_file=args.state_file,
            handoff_file=args.handoff_file,
            final_check_file=args.final_check_file,
        )
        state = load_json(paths.state_path)
        handoff = load_json(paths.handoff_path)
        final_check = load_json(paths.final_check_path)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    settings = get_settings()
    storage = get_local_storage(settings)
    attempt_count = next_publish_attempt_count(state)

    try:
        assert_publish_gates(state=state, final_check=final_check)
    except ValueError as e:
        run = build_gate_blocked_publish_result(
            paths=paths,
            handoff=handoff,
            state=state,
            publish_attempt_count=attempt_count,
            gate_message=str(e),
        )
        if not args.validate_only:
            persist_publish_artifacts(paths=paths, state=state, run=run)
        print(run.publish_status, run.blocked_reason or "", file=sys.stderr)
        print(next_action_hint(run))
        return 1

    if use_storage_key:
        try:
            vrp._asset_file_must_exist(settings, args.post_image_storage_key)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            if args.validate_only:
                return 1
            cls = PublishFailureClassification(
                error_type="missing_media_asset",
                publish_retryable=False,
                message=str(e),
            )
            run = build_prerequisite_blocked_publish_result(
                paths=paths,
                handoff=handoff,
                state=state,
                publish_attempt_count=attempt_count,
                blocked_reason=str(e),
                classification=cls,
            )
            persist_publish_artifacts(paths=paths, state=state, run=run)
            print(next_action_hint(run))
            return 1

    if mode == "path":
        try:
            validate_cloudinary_config(settings)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 1

    db = SessionLocal()
    try:
        if db.get(BrandProfile, args.brand_profile_id) is None:
            print(f"BrandProfile not found: {args.brand_profile_id}", file=sys.stderr)
            return 1
        acc = db.get(InstagramAccount, args.instagram_account_id)
        if acc is None:
            print(f"InstagramAccount not found: {args.instagram_account_id}", file=sys.stderr)
            return 1
        if not (acc.ig_user_id or "").strip():
            print("instagram_accounts.ig_user_id is missing", file=sys.stderr)
            return 1
    finally:
        db.close()

    if args.validate_only:
        ig = build_meta_client(settings)
        if ig is None:
            print("WARN: INSTAGRAM_ACCESS_TOKEN not set — publish would block.", file=sys.stderr)
        print("validate-only: prerequisites satisfied for gates, image source, and DB rows.")
        return 0

    if mode == "path":
        try:
            cu = upload_local_image(settings, Path(args.post_image_path).expanduser())
        except (ValueError, RuntimeError) as e:
            print(str(e), file=sys.stderr)
            return 1
        post_image_url_for_publish = cu.secure_url
        print(f"cloudinary secure_url={cu.secure_url}")
        print(f"cloudinary public_id={cu.public_id}")

    ig_client = build_meta_client(settings)
    if ig_client is None:
        run = build_prerequisite_blocked_publish_result(
            paths=paths,
            handoff=handoff,
            state=state,
            publish_attempt_count=attempt_count,
            blocked_reason="Instagram Graph token missing",
            classification=PublishFailureClassification(
                error_type="missing_instagram_token",
                publish_retryable=False,
                message="Set INSTAGRAM_ACCESS_TOKEN in environment (.env). Token value is not printed here.",
            ),
        )
        persist_publish_artifacts(paths=paths, state=state, run=run)
        print(next_action_hint(run))
        return 1

    db = SessionLocal()
    try:
        run = run_venus_weekly_real_publish(
            db,
            settings=settings,
            paths=paths,
            handoff=handoff,
            state=state,
            final_check=final_check,
            brand_profile_id=args.brand_profile_id,
            instagram_account_id=args.instagram_account_id,
            post_image_storage_key=args.post_image_storage_key if use_storage_key else None,
            post_image_url=post_image_url_for_publish
            if mode == "path"
            else (str(args.post_image_url).strip() if mode == "url" else None),
            ig_client=ig_client,
            storage=storage,
            existing_post_draft_id=args.existing_post_draft_id,
            publish_attempt_count=attempt_count,
        )
        persist_publish_artifacts(paths=paths, state=state, run=run)
    finally:
        db.close()

    print(f"publish_status={run.publish_status}")
    print(next_action_hint(run))
    if run.meta_error_message:
        suffix: list[str] = []
        if run.meta_error_code is not None:
            suffix.append(f"code {run.meta_error_code}")
        if run.meta_error_subcode is not None:
            suffix.append(f"subcode {run.meta_error_subcode}")
        if run.meta_status_code is not None:
            suffix.append(f"http {run.meta_status_code}")
        line = f"Meta error: {run.meta_error_message}"
        if suffix:
            line += f" ({', '.join(suffix)})"
        print(line, file=sys.stderr)
    if run.publish_error_message:
        print(run.publish_error_message, file=sys.stderr)

    ok = run.publish_status in ("published", "publish_partial")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
