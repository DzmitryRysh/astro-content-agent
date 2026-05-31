#!/usr/bin/env python3
"""CLI: approve one image as a reusable Catstyle per-planet character reference."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_planet_reference_approval import (  # noqa: E402
    CatstylePlanetReferenceApprovalError,
    approval_result_as_jsonable,
    approve_catstyle_planet_reference,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Approve a local image as a Catstyle per-planet character reference "
            "(reusable across aspects). No OpenAI, Instagram, or Cloudinary."
        )
    )
    ap.add_argument("--image-path", required=True, type=Path, dest="image_path")
    ap.add_argument("--planet", required=True, help="Planet name e.g. Saturn, Moon, Venus.")
    ap.add_argument("--registry-key", required=True, dest="registry_key")
    ap.add_argument("--label", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--priority", type=int, default=100)
    ap.add_argument("--inactive", action="store_true", help="Store entry as inactive (default is active).")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        result = approve_catstyle_planet_reference(
            source_image=args.image_path,
            planet=args.planet,
            registry_key=args.registry_key,
            label=args.label,
            notes=args.notes,
            priority=args.priority,
            active=not args.inactive,
            overwrite=args.overwrite,
        )
    except (CatstylePlanetReferenceApprovalError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(approval_result_as_jsonable(result), ensure_ascii=False, indent=2))
        return 0

    print()
    print("Catstyle planet reference approval")
    print(f"  source_image: {result.source_image}")
    print(f"  target_image: {result.target_image}")
    print(f"  planet:       {result.planet}")
    print(f"  registry_key: {result.registry_key}")
    print(f"  active:       {result.active}")
    print("  files_written:")
    for p in result.files_written:
        print(f"    - {p}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
