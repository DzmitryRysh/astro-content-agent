#!/usr/bin/env python3
"""Print summaries for Catstyle render style profiles v1."""
from __future__ import annotations

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.render_style_profiles_v1 import list_render_style_profiles


def main() -> int:
    print()
    print("Catstyle render style profiles v1")
    for prof in list_render_style_profiles():
        avoid_preview = "; ".join(prof.avoid_lines[:4])
        if len(prof.avoid_lines) > 4:
            avoid_preview += " ..."
        print(f"  key:              {prof.key}")
        print(f"  label:            {prof.label}")
        print(f"  short_prompt_line:{prof.short_prompt_line}")
        print(f"  avoid summary:    {avoid_preview}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
