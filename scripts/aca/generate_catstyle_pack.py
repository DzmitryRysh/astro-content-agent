#!/usr/bin/env python3
"""CLI: generate Catstyle v0 visual prompt pack artifact (JSON optional)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import (
    generate_catstyle_prompt_pack,
    normalize_planet_name,
)


def _artifact_dict(
    *,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    pack,
    skin_a: str | None,
    skin_b: str | None,
    world_template_key: str | None,
    scene_template_key: str | None,
    render_style_profile_key: str | None,
) -> dict:
    blob: dict = {
        "planet_a": planet_a,
        "planet_b": planet_b,
        "aspect_type": aspect_type,
        "mode": mode,
        "image_prompts": pack.image_prompts,
        "animation_prompt": pack.animation_prompt,
        "negative_prompt": pack.negative_prompt,
        "carousel_idea": pack.carousel_idea,
    }
    if skin_a:
        blob["skin_a"] = skin_a
    if skin_b:
        blob["skin_b"] = skin_b
    if world_template_key:
        blob["world_template_key"] = world_template_key
    if scene_template_key:
        blob["scene_template_key"] = scene_template_key
    if pack.world_template_profile is not None:
        blob["world_template_profile"] = pack.world_template_profile
    if pack.scene_template_profile is not None:
        blob["scene_template_profile"] = pack.scene_template_profile
    if render_style_profile_key:
        blob["render_style_profile_key"] = render_style_profile_key
    if pack.render_style_profile is not None:
        blob["render_style_profile"] = pack.render_style_profile
    return blob


def _print_pack_readable(
    planet_a: str, planet_b: str, aspect_type: str, mode: str, pack, *, skin_a: str | None, skin_b: str | None
) -> None:
    print()
    print("Catstyle prompt pack")
    print(f"  Planets:      {planet_a} + {planet_b}")
    if skin_a or skin_b:
        print(f"  Skins:        skin_a={skin_a or '(none)'}  skin_b={skin_b or '(none)'}")
    if pack.world_template_profile or pack.scene_template_profile:
        wk = (pack.world_template_profile or {}).get("template_key", "(none)")
        sk = (pack.scene_template_profile or {}).get("template_key", "(none)")
        print(f"  World tmpl:   {wk}")
        print(f"  Scene tmpl:   {sk}")
    if pack.render_style_profile:
        rk = (pack.render_style_profile or {}).get("key", "(none)")
        print(f"  Render style: {rk}")
    print(f"  Aspect:       {aspect_type}")
    print(f"  Mode:         {mode}")
    print(f"  Variants:     {len(pack.image_prompts)}")
    print()
    for i, p in enumerate(pack.image_prompts, start=1):
        print(f"--- Image prompt {i} ---")
        print(p)
        print()
    print("--- Animation prompt ---")
    print(pack.animation_prompt)
    print()
    print("--- Negative prompt ---")
    print(pack.negative_prompt)
    print()
    print("--- Carousel idea ---")
    print(pack.carousel_idea)
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Catstyle v0 prompt pack (text prompts only).")
    ap.add_argument("--planet-a", required=True, dest="planet_a")
    ap.add_argument("--planet-b", required=True, dest="planet_b")
    ap.add_argument("--aspect-type", required=True, dest="aspect_type")
    ap.add_argument("--mode", required=True, choices=["tension", "compensation", "mixed", "flow"])
    ap.add_argument("--variants-count", type=int, default=2, dest="variants_count")
    ap.add_argument(
        "--skin-a",
        default=None,
        dest="skin_a",
        help="Optional character skin key for planet-a (v0: Mars, Jupiter, Saturn)",
    )
    ap.add_argument(
        "--skin-b",
        default=None,
        dest="skin_b",
        help="Optional character skin key for planet-b (v0: Mars, Jupiter, Saturn)",
    )
    ap.add_argument(
        "--world-template",
        default=None,
        dest="world_template",
        help="Catstyle world template key v1 (defaults internally when premium art-direction is on).",
    )
    ap.add_argument(
        "--scene-template",
        default=None,
        dest="scene_template",
        help="Catstyle scene template key v1 (optional explicit hero beat).",
    )
    ap.add_argument(
        "--render-style-profile",
        default=None,
        dest="render_style_profile",
        help="Catstyle render style profile key (default: premium_comic_poster_v2; use premium_comic_poster_v1 for legacy).",
    )
    ap.add_argument(
        "--shot-mode",
        choices=("hero_pair", "epic_arena_showdown", "standard"),
        default=None,
        dest="shot_mode",
        help=(
            "hero_pair (default): paired hero_poster + alternate_action_angle framing; "
            "epic_arena_showdown: wide arena spectacle framing with readable central characters; "
            "standard: legacy variant prompts."
        ),
    )
    ap.add_argument("--output", type=Path, default=None, help="Write JSON artifact to this path")
    args = ap.parse_args()

    skin_a = str(args.skin_a).strip() if args.skin_a else None
    skin_b = str(args.skin_b).strip() if args.skin_b else None
    world_template = str(args.world_template).strip() if args.world_template else None
    scene_template = str(args.scene_template).strip() if args.scene_template else None
    if world_template == "":
        world_template = None
    if scene_template == "":
        scene_template = None
    render_style = str(args.render_style_profile).strip() if args.render_style_profile else None
    if render_style == "":
        render_style = None

    try:
        pa = normalize_planet_name(args.planet_a)
        pb = normalize_planet_name(args.planet_b)
        req_kw = dict(
            planet_a=args.planet_a,
            planet_b=args.planet_b,
            aspect_type=args.aspect_type,
            mode=args.mode,
            variants_count=args.variants_count,
            skin_a=skin_a,
            skin_b=skin_b,
            world_template_key=world_template,
            scene_template_key=scene_template,
        )
        if render_style is not None:
            req_kw["render_style_profile_key"] = render_style
        if args.shot_mode is not None:
            req_kw["shot_mode"] = args.shot_mode
        req = CatstylePromptRequest(**req_kw)
        pack = generate_catstyle_prompt_pack(req)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    _print_pack_readable(pa, pb, args.aspect_type, args.mode, pack, skin_a=skin_a, skin_b=skin_b)

    if args.output is not None:
        out_path = args.output.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blob = _artifact_dict(
            planet_a=pa,
            planet_b=pb,
            aspect_type=args.aspect_type,
            mode=args.mode,
            pack=pack,
            skin_a=skin_a,
            skin_b=skin_b,
            world_template_key=world_template,
            scene_template_key=scene_template,
            render_style_profile_key=render_style,
        )
        out_path.write_text(json.dumps(blob, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote artifact: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
