#!/usr/bin/env python3
"""CLI: list Catstyle approved style-reference registry entries (local, deterministic)."""
from __future__ import annotations

import argparse
import json
import sys

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.approved_reference_registry import (
    list_active_references,
    registry_entries_as_jsonable,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "List active approved Catstyle reference images (v1 registry). "
            "No OpenAI, Instagram, Cloudinary, or external APIs."
        )
    )
    ap.add_argument("--json", action="store_true", help="Print JSON array of entries.")
    args = ap.parse_args()

    if args.json:
        print(json.dumps(registry_entries_as_jsonable(), indent=2, ensure_ascii=False))
        return 0

    rows = list_active_references()
    print("Catstyle approved reference registry (v1)")
    print(f"  active entries: {len(rows)}")
    print()
    for e in rows:
        print(f"  {e.planet_a} {e.aspect_type} {e.planet_b}  /  {e.mode}")
        print(f"    registry_key: {e.registry_key}")
        print(f"    priority:     {e.priority}")
        print(f"    label:        {e.label}")
        print(f"    image_path:   {e.image_path}")
        if e.notes:
            print(f"    notes:        {e.notes}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
