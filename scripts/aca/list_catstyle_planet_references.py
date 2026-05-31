#!/usr/bin/env python3
"""CLI: list active Catstyle approved per-planet character references."""
from __future__ import annotations

import argparse
import json
import sys

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (  # noqa: E402
    list_active_planet_references_grouped,
    list_resolved_winners_by_planet,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="List active Catstyle planet reference registry rows.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    grouped = list_active_planet_references_grouped()
    winners = list_resolved_winners_by_planet()
    payload = {
        "by_planet": {
            planet: [e.model_dump(mode="json") for e in entries]
            for planet, entries in sorted(grouped.items())
        },
        "resolved_winners": {
            planet: (w.model_dump(mode="json") if w else None)
            for planet, w in sorted(winners.items())
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print()
    print("Catstyle planet references (active)")
    if not grouped:
        print("  (none)")
    for planet in sorted(grouped):
        print(f"\n  {planet}:")
        for e in grouped[planet]:
            mark = " *" if winners.get(planet) and winners[planet].registry_key == e.registry_key else ""
            print(
                f"    {e.registry_key}{mark}: {e.image_path}  priority={e.priority}  label={e.label or '-'}"
            )
    if winners:
        print("\nResolved winners:")
        for planet in sorted(winners):
            w = winners[planet]
            if w:
                print(f"  {planet}: {w.registry_key} -> {w.image_path}")
            else:
                print(f"  {planet}: (none)")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
