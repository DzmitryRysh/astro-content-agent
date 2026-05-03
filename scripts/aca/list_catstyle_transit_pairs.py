#!/usr/bin/env python3
"""List all 25 Catstyle social/outer→personal transit pair seeds (v0)."""
from __future__ import annotations

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.transit_pair_seed_v0 import list_transit_pair_seeds


def main() -> int:
    seeds = list_transit_pair_seeds()
    print(f"Catstyle transit_pair_seed_v0: {len(seeds)} pairs\n")
    for s in seeds:
        print(f"{s.outer_planet} + {s.personal_planet}")
        print(f"  tension: {s.core_tension[:100]}{'…' if len(s.core_tension) > 100 else ''}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
