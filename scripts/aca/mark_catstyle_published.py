#!/usr/bin/env python3
"""CLI: mark Catstyle publish handoff as manually published."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_published_registry import (
    CatstylePublishedRegistryError,
    mark_catstyle_handoff_published,
    write_catstyle_published_record,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Mark a local Catstyle publish_handoff as manually published. "
            "No Instagram API, OpenAI, Cloudinary, or external calls."
        )
    )
    ap.add_argument("--handoff-dir", type=Path, required=True, help="Directory containing publish_handoff.json")
    ap.add_argument("--instagram-url", default=None, help="Optional published Instagram URL")
    ap.add_argument("--notes", default=None, help="Optional local notes")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing publish_record files")
    args = ap.parse_args()

    try:
        record = mark_catstyle_handoff_published(
            args.handoff_dir,
            instagram_url=args.instagram_url,
            notes=args.notes,
        )
        names = write_catstyle_published_record(record, args.handoff_dir, overwrite=args.overwrite)
    except CatstylePublishedRegistryError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle published record")
    print(f"  handoff_dir:      {record.handoff_dir}")
    print(f"  publish_state:    {record.publish_state}")
    print(f"  published_at:     {record.published_at}")
    print(f"  instagram_url:    {record.instagram_url or '(none)'}")
    print("  files_written:")
    for n in names:
        print(f"    - {n}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
