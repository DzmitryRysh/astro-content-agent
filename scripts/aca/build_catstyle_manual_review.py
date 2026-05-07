#!/usr/bin/env python3
"""CLI: build Catstyle manual_review.json / manual_review.md from a post package directory."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_manual_review import (
    build_catstyle_manual_review,
    write_catstyle_manual_review,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Build a deterministic manual review worksheet from catstyle_post_packages/.../post_package.json. "
            "Runs local quality checks only — no LLM, Instagram, Cloudinary, or publishing."
        ),
    )
    ap.add_argument(
        "--package-dir",
        type=Path,
        required=True,
        help="Directory containing post_package.json (e.g. catstyle_post_packages/YYYY-MM-DD)",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Write manual_review.* here (default: same as --package-dir)",
    )
    ap.add_argument("--overwrite", action="store_true", help="Overwrite manual_review.json / .md if present")
    args = ap.parse_args()

    try:
        review = build_catstyle_manual_review(args.package_dir)
        out_dir = args.output_dir if args.output_dir is not None else args.package_dir
        names = write_catstyle_manual_review(review, out_dir, overwrite=args.overwrite)
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle manual review")
    print(f"  date:           {review.date}")
    print(f"  package_dir:    {review.package_dir}")
    print(f"  output_dir:     {Path(out_dir).resolve()}")
    print(f"  quality:        {review.quality_status}  score={review.quality_score}")
    print(f"  approval:       {review.approval_status}")
    print("  files_written:")
    for n in names:
        print(f"    - {n}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
