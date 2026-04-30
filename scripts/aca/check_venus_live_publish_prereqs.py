#!/usr/bin/env python3
"""Thin CLI: verify Venus weekly live-publish prerequisites (no Instagram POST)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

from _venus_cli_paths import default_week_dir, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.models import BrandProfile, InstagramAccount
from astro_content_agent.db.session import SessionLocal
from astro_content_agent.services.content.venus_weekly_real_publish import (
    assert_publish_gates,
    build_meta_client,
    load_json,
    resolve_week_artifacts,
)
from astro_content_agent.services.media.url_builder import build_asset_url


def main() -> int:
    p = argparse.ArgumentParser(description="Check gates + disk asset + DB + token (+ optional media URL HEAD).")
    p.add_argument("week_start", help="YYYY-MM-DD")
    p.add_argument("--instagram-account-id", required=True)
    p.add_argument("--brand-profile-id", required=True)
    p.add_argument("--post-image-storage-key", required=True)
    p.add_argument("--week-dir", type=Path, default=None)
    p.add_argument("--state-file", type=Path, default=None)
    p.add_argument("--handoff-file", type=Path, default=None)
    p.add_argument("--final-check-file", type=Path, default=None)
    p.add_argument(
        "--probe-media-url",
        action="store_true",
        help="HEAD request to built media URL (Instagram fetch simulation)",
    )
    args = p.parse_args()

    fails = 0
    week_dir = default_week_dir(args.week_start, args.week_dir)

    def ok(msg: str) -> None:
        print(f"OK   {msg}")

    def warn(msg: str) -> None:
        print(f"WARN {msg}")

    def err(msg: str) -> None:
        nonlocal fails
        fails += 1
        print(f"FAIL {msg}", file=sys.stderr)

    if not week_dir.is_dir():
        err(f"Week dir not found: {week_dir}")
        return 1

    try:
        paths = resolve_week_artifacts(
            week_dir=week_dir,
            week_start_hint=args.week_start,
            state_file=args.state_file,
            handoff_file=args.handoff_file,
            final_check_file=args.final_check_file,
        )
    except ValueError as e:
        err(str(e))
        return 1

    try:
        state = load_json(paths.state_path)
        handoff = load_json(paths.handoff_path)
        final_check = load_json(paths.final_check_path)
    except ValueError as e:
        err(str(e))
        return 1

    try:
        assert_publish_gates(state=state, final_check=final_check)
        ok("publish gates (approved state + final-check pass)")
    except ValueError as e:
        err(str(e))

    settings = get_settings()
    # Asset on disk (same helper as real publish)
    from astro_content_agent.services.content import venus_weekly_real_publish as vrp

    try:
        vrp._asset_file_must_exist(settings, args.post_image_storage_key)
        ok(f"post image file exists under ASSETS_DIR for key {args.post_image_storage_key!r}")
    except ValueError as e:
        err(str(e))

    db = SessionLocal()
    try:
        bp = db.get(BrandProfile, args.brand_profile_id)
        if bp is None:
            err(f"BrandProfile not found: {args.brand_profile_id}")
        else:
            ok(f"brand_profile {args.brand_profile_id!r} ({bp.name})")

        acc = db.get(InstagramAccount, args.instagram_account_id)
        if acc is None:
            err(f"InstagramAccount not found: {args.instagram_account_id}")
        else:
            ok(f"instagram account row {acc.account_name!r} active={acc.is_active}")
            if not (acc.ig_user_id or "").strip():
                err("instagram_accounts.ig_user_id is empty")
            else:
                ok("instagram_accounts.ig_user_id is set")
    finally:
        db.close()

    ig = build_meta_client(settings)
    if ig is None:
        warn("INSTAGRAM_ACCESS_TOKEN not set — real publish will block until configured")
    else:
        ok("INSTAGRAM_ACCESS_TOKEN is set (value not printed)")

    parsed = None
    try:
        from urllib.parse import urlparse

        parsed = urlparse(settings.public_base_url)
    except Exception:
        pass
    if parsed is None or not parsed.scheme or not parsed.netloc:
        err(f"PUBLIC_BASE_URL invalid for asset URLs: {settings.public_base_url!r}")
    elif parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
        warn(f"PUBLIC_BASE_URL is localhost ({settings.public_base_url}) — Meta cannot fetch media in production")

    media_url = build_asset_url(args.post_image_storage_key, settings)
    ok(f"Computed media URL (preview): {media_url}")

    if args.probe_media_url:
        try:
            r = httpx.head(media_url, follow_redirects=True, timeout=20.0)
            if r.status_code >= 400:
                err(f"HEAD {media_url} -> HTTP {r.status_code}")
            else:
                ok(f"HEAD {media_url} -> HTTP {r.status_code}")
        except httpx.HTTPError as e:
            err(f"HEAD failed: {e}")

    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
