#!/usr/bin/env python3
"""CLI: build Catstyle publish handoff after approved manual review (local files only)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_publish_handoff import (
    CatstylePublishHandoffError,
    build_catstyle_publish_handoff,
    write_catstyle_publish_handoff,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Build publish_handoff.json/.md and snippet files from post_package.json + approved manual_review.json. "
            "No Instagram, Cloudinary, OpenAI, or automated publishing."
        ),
    )
    ap.add_argument(
        "--package-dir",
        type=Path,
        required=True,
        help="Catstyle post package directory (post_package.json + manual_review.json)",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Write artifacts here (default: catstyle_publish_handoffs/<date>)",
    )
    ap.add_argument("--overwrite", action="store_true", help="Overwrite outputs if they exist")
    args = ap.parse_args()

    try:
        handoff = build_catstyle_publish_handoff(args.package_dir)
        out_dir = args.output_dir
        if out_dir is None:
            out_dir = Path("catstyle_publish_handoffs") / handoff.date
        names = write_catstyle_publish_handoff(handoff, out_dir, overwrite=args.overwrite)
    except CatstylePublishHandoffError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle publish handoff")
    print(f"  date:           {handoff.date}")
    print(f"  package_dir:    {handoff.package_dir}")
    print(f"  output_dir:     {Path(out_dir).resolve()}")
    print(f"  status:         {handoff.publish_status}")
    print(f"  primary_image:  {handoff.recommended_primary_image}")
    print("  files_written:")
    for n in names:
        print(f"    - {n}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
