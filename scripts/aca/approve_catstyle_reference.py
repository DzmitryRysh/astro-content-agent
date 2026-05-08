#!/usr/bin/env python3
"""CLI: approve one generated Catstyle image as reusable reference."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_reference_approval import (  # noqa: E402
    CatstyleReferenceApprovalError,
    approval_result_as_jsonable,
    approve_catstyle_reference,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Approve a local generated Catstyle image and register it for future auto style-reference lookup. "
            "No OpenAI, Instagram, Cloudinary, or external APIs."
        )
    )
    ap.add_argument("--image-path", required=True, type=Path, dest="image_path")
    ap.add_argument("--planet-a", required=True, dest="planet_a")
    ap.add_argument("--planet-b", required=True, dest="planet_b")
    ap.add_argument("--aspect-type", required=True, dest="aspect_type")
    ap.add_argument("--mode", required=True, dest="mode")
    ap.add_argument("--label", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--priority", type=int, default=100)
    ap.add_argument("--inactive", action="store_true", help="Store entry as inactive (default is active).")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        result = approve_catstyle_reference(
            source_image=args.image_path,
            planet_a=args.planet_a,
            planet_b=args.planet_b,
            aspect_type=args.aspect_type,
            mode=args.mode,
            label=args.label,
            notes=args.notes,
            priority=args.priority,
            active=not args.inactive,
            overwrite=args.overwrite,
        )
    except (CatstyleReferenceApprovalError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(approval_result_as_jsonable(result), ensure_ascii=False, indent=2))
        return 0

    print()
    print("Catstyle reference approval")
    print(f"  source_image: {result.source_image}")
    print(f"  target_image: {result.target_image}")
    print(f"  registry_key: {result.registry_key}")
    print(f"  planet_pair:  {result.planet_pair}")
    print(f"  aspect:       {result.aspect}")
    print(f"  mode:         {result.mode}")
    print(f"  active:       {result.active}")
    print("  files_written:")
    for p in result.files_written:
        print(f"    - {p}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
