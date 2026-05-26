#!/usr/bin/env python3
"""CLI: list active Catstyle approved arena/environment references."""
from __future__ import annotations

import argparse
import json
import sys

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.approved_arena_reference_registry import (  # noqa: E402
    list_active_arena_references,
    resolve_approved_arena_reference,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="List active Catstyle arena reference registry rows.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = list_active_arena_references()
    winner = resolve_approved_arena_reference(registry=rows)
    payload = {
        "active_entries": [e.model_dump(mode="json") for e in rows],
        "resolved": winner.model_dump(mode="json") if winner else None,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print()
    print("Catstyle arena references (active)")
    if not rows:
        print("  (none)")
    for e in rows:
        mark = " *" if winner and e.registry_key == winner.registry_key else ""
        print(f"  {e.registry_key}{mark}: {e.image_path}  priority={e.priority}  label={e.label or '-'}")
    if winner:
        print(f"\nResolved winner: {winner.registry_key} -> {winner.image_path}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
