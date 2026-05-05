#!/usr/bin/env python3
"""Print summaries for Catstyle scene templates v1."""
from __future__ import annotations

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.scene_templates_v1 import list_scene_templates


def _compat_summary(st) -> str:
    if st.compatible_pairs:
        pairs = [f"{a}+{b}" for a, b in st.compatible_pairs[:6]]
        tail = " …" if len(st.compatible_pairs) > 6 else ""
        return f"pairs ({len(st.compatible_pairs)}): {', '.join(pairs)}{tail}"
    if st.compatible_planets:
        return f"planets (subset): {', '.join(st.compatible_planets)}"
    return "(none)"


def main() -> int:
    print()
    print("Catstyle scene templates v1")
    for st in list_scene_templates():
        asp = "any" if st.compatible_aspects is None else ", ".join(st.compatible_aspects)
        skins = "optional" if st.compatible_skins is None else ", ".join(st.compatible_skins)
        print(f"  key:            {st.template_key}")
        print(f"  display_name:   {st.display_name}")
        print(f"  energy:         {st.energy}")
        print(f"  compatibility:  {_compat_summary(st)}")
        print(f"  aspects:        {asp}")
        print(f"  skins:          {skins}")
        print(f"  cue:            {st.short_prompt_line}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
