#!/usr/bin/env python3
"""CLI: build deterministic Catstyle Instagram post package from image_generation_jobs.json."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.core.config import get_settings
from astro_content_agent.services.content.catstyle_post_package import (
    build_catstyle_post_package,
    write_catstyle_post_package,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Build a local Catstyle post package (JSON + Markdown + text snippets) from an image jobs manifest. "
            "Captions use the LLM when OPENAI_API_KEY is set (override with --no-llm-caption). "
            "No Instagram, Cloudinary, or publishing."
        ),
    )
    ap.add_argument("--manifest", type=Path, required=True, help="Path to image_generation_jobs.json")
    ap.add_argument(
        "--use-llm-caption",
        action="store_true",
        help="Force LLM caption (default: on when OPENAI_API_KEY is set)",
    )
    ap.add_argument(
        "--no-llm-caption",
        action="store_true",
        help="Use structured fallback caption only (no API call)",
    )
    ap.add_argument(
        "--generated-images-dir",
        type=Path,
        default=None,
        help="Optional directory where PNGs were written (matches suggested_output_name basenames).",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Write package here (default: catstyle_post_packages/<manifest date>)",
    )
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing package files")
    args = ap.parse_args()

    try:
        if args.use_llm_caption and args.no_llm_caption:
            print("Use only one of --use-llm-caption and --no-llm-caption.", file=sys.stderr)
            return 1
        if args.no_llm_caption:
            use_llm: bool | None = False
        elif args.use_llm_caption:
            use_llm = True
        else:
            use_llm = bool(get_settings().openai_api_key)
        pkg = build_catstyle_post_package(
            args.manifest,
            generated_images_dir=args.generated_images_dir,
            use_llm_caption=use_llm,
        )
        out_dir = args.output_dir
        if out_dir is None:
            out_dir = Path("catstyle_post_packages") / pkg.date
        paths = write_catstyle_post_package(pkg, out_dir, overwrite=args.overwrite)
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle post package")
    print(f"  date:           {pkg.date}")
    print(f"  output_dir:     {Path(out_dir).resolve()}")
    print(f"  manifest:       {pkg.source_manifest_path}")
    print(f"  primary_image:  {pkg.recommended_primary_image or '(none on disk)'}")
    print("  files_written:")
    for name in paths:
        print(f"    - {name}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
