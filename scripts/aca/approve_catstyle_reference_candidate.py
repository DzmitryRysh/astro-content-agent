#!/usr/bin/env python3
"""CLI: approve one reference candidate image and register it in approved_references.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_creative_publish_stability import (  # noqa: E402
    evaluate_creative_publish_stability,
)
from astro_content_agent.services.content.catstyle_reference_approval import (  # noqa: E402
    CatstyleReferenceApprovalError,
    approval_result_as_jsonable,
    approve_catstyle_reference,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Approve a Catstyle reference candidate: copy image into references/ and upsert "
            "approved_references.json (same registry as approve_catstyle_reference.py). "
            "No OpenAI, Instagram, Cloudinary, or secrets."
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

    stability = evaluate_creative_publish_stability(
        args.planet_a, args.planet_b, args.aspect_type, args.mode
    )

    if args.json:
        payload = approval_result_as_jsonable(result)
        payload["creative_publish_stable"] = stability.stable
        payload["stability_reason"] = stability.reason
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print()
    print("Catstyle reference candidate approval")
    print(f"  source_image: {result.source_image}")
    print(f"  target_image: {result.target_image}")
    print(f"  registry_key: {result.registry_key}")
    print(f"  planet_pair:  {result.planet_pair}")
    print(f"  aspect:       {result.aspect}")
    print(f"  mode:         {result.mode}")
    print(f"  active:       {result.active}")
    print(f"  publish_stable_after_approval: {stability.stable}")
    print(f"  stability_reason: {stability.reason}")
    print("  files_written:")
    for p in result.files_written:
        print(f"    - {p}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
