#!/usr/bin/env python3
"""CLI: deterministic quality check for Catstyle post_package.json bundles."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_post_package_quality import (
    check_catstyle_post_package,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Check a Catstyle post package directory (post_package.json) before manual Instagram review. "
            "No LLM, Instagram API, Cloudinary, or publishing."
        ),
    )
    ap.add_argument("--package-dir", type=Path, required=True, help="Directory containing post_package.json")
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text")
    args = ap.parse_args()

    try:
        result = check_catstyle_post_package(args.package_dir)
    except OSError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return 0

    print()
    print("Catstyle post package quality")
    print(f"  status:         {result.status}")
    print(f"  score:          {result.score}")
    print(f"  primary_image:  {result.recommended_primary_image or '(none)'}")
    print("  errors:")
    if result.errors:
        for line in result.errors:
            print(f"    - {line}")
    else:
        print("    (none)")
    print("  warnings:")
    if result.warnings:
        for line in result.warnings:
            print(f"    - {line}")
    else:
        print("    (none)")
    print("  passed:")
    for line in result.passed_checks:
        print(f"    - {line}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
