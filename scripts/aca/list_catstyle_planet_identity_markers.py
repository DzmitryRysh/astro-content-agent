#!/usr/bin/env python3
"""Print Catstyle planet identity markers v1 summary for all ten planets."""
from __future__ import annotations

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.planet_identity_markers_v1 import list_planet_identity_marker_profiles


def main() -> int:
    print()
    print("Catstyle planet identity markers v1")
    print(f"{'Planet':<10} {'Symbol name':<14}  Primary marker / signature prop")
    print("-" * 78)
    for p in list_planet_identity_marker_profiles():
        must_summary = "; ".join(p.must_show_markers[:2])
        if len(p.must_show_markers) > 2:
            must_summary += "; ..."
        line = f"{p.primary_marker} | {p.signature_prop}"
        print(f"{p.planet_name:<10} {p.symbol_name:<14}  {line}")
        print(f"{'':10} {'':<14}  must-show: {must_summary}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
