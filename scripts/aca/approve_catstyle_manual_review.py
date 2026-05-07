#!/usr/bin/env python3
"""CLI: record Catstyle manual approval decision into manual_review.json / manual_review.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_manual_review import (
    ALLOWED_APPROVAL_DECISIONS,
    approve_catstyle_manual_review,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Update manual_review.json with approval_status, reviewer_notes, and reviewed_at (UTC). "
            "Re-renders manual_review.md. Local only — no APIs."
        ),
    )
    ap.add_argument(
        "--package-dir",
        type=Path,
        required=True,
        help="Directory containing manual_review.json (and post_package.json parent bundle)",
    )
    ap.add_argument(
        "--decision",
        required=True,
        choices=sorted(ALLOWED_APPROVAL_DECISIONS),
        help="Reviewer decision",
    )
    ap.add_argument("--notes", default="", help="Reviewer notes (optional)")
    ap.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Overwrite manual_review outputs (default: --overwrite)",
    )
    args = ap.parse_args()

    try:
        updated = approve_catstyle_manual_review(
            args.package_dir,
            args.decision,
            reviewer_notes=args.notes,
            overwrite=args.overwrite,
        )
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle manual approval")
    print(f"  package_dir:    {updated.package_dir}")
    print(f"  decision:       {updated.approval_status}")
    print(f"  reviewed_at:    {updated.reviewed_at}")
    print("  files_written:")
    print("    - manual_review.json")
    print("    - manual_review.md")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
