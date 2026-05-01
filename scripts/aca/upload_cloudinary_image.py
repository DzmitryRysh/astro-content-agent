#!/usr/bin/env python3
"""Upload a local image to Cloudinary and print the secure HTTPS URL."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.core.config import get_settings
from astro_content_agent.services.media.cloudinary_uploader import upload_local_image


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload a local image file to Cloudinary.")
    ap.add_argument(
        "--image-path",
        type=Path,
        required=True,
        help="Path to a local image file (relative to cwd or absolute)",
    )
    ap.add_argument("--public-id", default=None, help="Optional Cloudinary public_id")
    ap.add_argument(
        "--folder",
        default=None,
        help="Override CLOUDINARY_FOLDER for this upload only",
    )
    args = ap.parse_args()

    image_path = args.image_path
    if not image_path.is_file():
        print(f"Image file not found: {image_path.resolve()}", file=sys.stderr)
        return 1

    settings = get_settings()
    try:
        result = upload_local_image(
            settings,
            image_path,
            public_id=args.public_id,
            folder=args.folder,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    print(f"local_path={result.local_path}")
    print(f"secure_url={result.secure_url}")
    print(f"public_id={result.public_id}")
    if result.format:
        print(f"format={result.format}")
    if result.bytes is not None:
        print(f"bytes={result.bytes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
