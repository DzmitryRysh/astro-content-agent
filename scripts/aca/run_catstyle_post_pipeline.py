#!/usr/bin/env python3
"""CLI: run Catstyle local post pipeline (package → QC → manual review → optional approval → handoff)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_post_pipeline import run_catstyle_post_pipeline


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Orchestrate Catstyle post_package + quality + manual_review (+ optional approve + publish_handoff). "
            "Assumes image generation already produced files under --generated-images-dir. "
            "No OpenAI, Instagram, Cloudinary, or automated publishing."
        ),
    )
    ap.add_argument("--manifest", type=Path, required=True, help="Path to image_generation_jobs.json")
    ap.add_argument(
        "--generated-images-dir",
        type=Path,
        default=None,
        help="Directory containing generated PNGs referenced by the manifest",
    )
    ap.add_argument(
        "--post-package-dir",
        type=Path,
        default=None,
        help="Write post package here (default: catstyle_post_packages/<date> under cwd)",
    )
    ap.add_argument(
        "--publish-handoff-dir",
        type=Path,
        default=None,
        help="Write publish handoff here when --approve succeeds (default: catstyle_publish_handoffs/<date>)",
    )
    ap.add_argument(
        "--approve",
        action="store_true",
        help="After QC passes, approve manual review and build publish handoff",
    )
    ap.add_argument("--approval-notes", default="", help="Notes stored with approval (optional; may be empty)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing package/review/handoff files")
    ap.add_argument("--json", action="store_true", help="Print pipeline result as JSON")
    args = ap.parse_args()

    try:
        result = run_catstyle_post_pipeline(
            args.manifest,
            generated_images_dir=args.generated_images_dir,
            post_package_dir=args.post_package_dir,
            publish_handoff_dir=args.publish_handoff_dir,
            approve=args.approve,
            approval_notes=args.approval_notes,
            overwrite=args.overwrite,
        )
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return 0

    print()
    print("Catstyle post pipeline")
    print(f"  date:             {result.date}")
    print(f"  status:           {result.status}")
    print(f"  package_dir:      {result.package_dir}")
    print(f"  quality:          {result.quality_status}  score={result.quality_score}")
    print(f"  primary_image:    {result.recommended_primary_image or '(none)'}")
    print(f"  manual_review:    {result.manual_review_path}")
    print(f"  publish_handoff:  {result.publish_handoff_dir or '(none)'}")
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
    print("  files_written:")
    for line in result.files_written:
        print(f"    - {line}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
