#!/usr/bin/env python3
"""CLI: build deterministic Catstyle gallery index from publish handoffs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_gallery_index import (
    build_catstyle_gallery_index,
    write_catstyle_gallery_index,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Build local Catstyle gallery index by scanning catstyle_publish_handoffs/*/publish_handoff.json. "
            "No Instagram, Cloudinary, OpenAI, or external APIs."
        )
    )
    ap.add_argument(
        "--handoffs-dir",
        type=Path,
        default=Path("catstyle_publish_handoffs"),
        help="Directory to scan for publish handoffs (default: catstyle_publish_handoffs)",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=Path("catstyle_publish_handoffs"),
        help="Directory to write gallery_index.json/.md (default: catstyle_publish_handoffs)",
    )
    ap.add_argument(
        "--include-not-ready",
        action="store_true",
        help="Include non-ready handoffs (default includes only ready/approved handoffs).",
    )
    ap.add_argument("--json", action="store_true", help="Print result payload as JSON.")
    args = ap.parse_args()

    try:
        result = build_catstyle_gallery_index(
            args.handoffs_dir,
            include_not_ready=args.include_not_ready,
        )
        names = write_catstyle_gallery_index(result, args.output_dir, overwrite=True)
    except (FileNotFoundError, ValueError, FileExistsError, OSError, json.JSONDecodeError) as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "handoffs_dir": str(Path(args.handoffs_dir).expanduser().resolve()),
            "output_dir": str(Path(args.output_dir).expanduser().resolve()),
            "posts_indexed": result.posts_indexed,
            "files_written": names,
            "gallery_index": result.model_dump(mode="json"),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print()
    print("Catstyle gallery index")
    print(f"  handoffs_dir:    {Path(args.handoffs_dir).expanduser().resolve()}")
    print(f"  output_dir:      {Path(args.output_dir).expanduser().resolve()}")
    print(f"  posts_indexed:   {result.posts_indexed}")
    print("  files_written:")
    for n in names:
        print(f"    - {n}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
