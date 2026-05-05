#!/usr/bin/env python3
"""Print summaries for Catstyle world templates v1."""
from __future__ import annotations

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.world_templates_v1 import list_world_templates


def main() -> int:
    print()
    print("Catstyle world templates v1")
    for wt in list_world_templates():
        print(f"  key:           {wt.template_key}")
        print(f"  display_name:  {wt.display_name}")
        print(f"  energy_default:{wt.energy_default}")
        print(f"  environment:   {wt.environment_type}")
        print(f"  summary:       {wt.short_prompt_line}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
