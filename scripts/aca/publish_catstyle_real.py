#!/usr/bin/env python3
"""CLI: Catstyle publish handoff → Cloudinary (optional) + Instagram via ``PublisherService``."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import REPO_ROOT, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.core.repo_env import load_repo_dotenv_if_present

load_repo_dotenv_if_present(REPO_ROOT)

from astro_content_agent.core.config import get_settings
from astro_content_agent.services.content.catstyle_real_publish import run_catstyle_handoff_publish_workflow


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
    code, r = run_catstyle_handoff_publish_workflow(
        handoff_dir,
        settings=settings,
        validate_only=args.validate_only,
        do_publish=not args.validate_only,
        brand_profile_id_cli=args.brand_profile_id,
        instagram_account_id_cli=args.instagram_account_id,
        local_image_path=args.local_image_path,
        post_image_url=args.post_image_url,
    )
    if code != 0 and r is not None and r.error_message:
        print(r.error_message, file=sys.stderr)
    if args.validate_only and code == 0:
        print("validate_only_ok (artifacts: catstyle_publish_result.json, catstyle_publish_result.md)")
    elif not args.validate_only and r is not None:
        print(f"publish_status={r.publish_status}")
        if r.error_message:
            print(r.error_message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
