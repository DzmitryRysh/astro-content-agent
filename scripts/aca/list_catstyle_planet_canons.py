#!/usr/bin/env python3
"""Print one-line summaries for Catstyle planet canon v1 (all ten planets)."""
from __future__ import annotations

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.planet_canon_v1 import list_planet_canons


def main() -> int:
    print()
    print("Catstyle planet canon v1")
    for c in list_planet_canons():
        print(f"  {c.planet_name:8}  {c.short_prompt_line}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
