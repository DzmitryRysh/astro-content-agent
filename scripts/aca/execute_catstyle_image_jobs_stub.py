#!/usr/bin/env python3
"""CLI: stub-execute Catstyle image jobs (read manifest, write placeholders — no image API)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_image_generation_executor import (
    execute_catstyle_image_jobs_stub,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stub-execute Catstyle image_generation_jobs.json (no OpenAI, no upload).",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to image_generation_jobs.json",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Stub output directory (default: <manifest_dir>/generated_stub/)",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing generated_stub_*.txt files",
    )
    args = ap.parse_args()

    try:
        result = execute_catstyle_image_jobs_stub(
            args.manifest,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle image job executor (stub)")
    print(f"  manifest:       {result.source_manifest_path}")
    print(f"  output_dir:     {result.outputs_dir}")
    print(f"  jobs_processed: {result.jobs_processed}")
    if result.message:
        print(f"  message:        {result.message}")
    print(f"  status:         {result.status}")
    written = sum(1 for o in result.outputs if o.status == "generated_stub")
    print(f"  outputs_written: {written}")
    if result.skipped_count:
        print(f"  skipped:        {result.skipped_count}")
    if result.execution_manifest_path:
        print(f"  execution_manifest: {result.execution_manifest_path}")
    if result.stub_files_written:
        print("  stub_files:")
        for name in result.stub_files_written:
            print(f"    - {name}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
