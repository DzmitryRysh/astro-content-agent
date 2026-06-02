#!/usr/bin/env python3
"""CLI: build Catstyle image generation job manifests (no image API, no upload)."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    build_catstyle_image_generation_jobs,
)


def _parse_day(s: str) -> date:
    parts = s.strip().split("-")
    if len(parts) != 3:
        raise ValueError("Date must be YYYY-MM-DD")
    try:
        y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as e:
        raise ValueError("Date must be YYYY-MM-DD") from e
    return date(y, m, d)


def _default_output_dir(day: date) -> Path:
    return Path("catstyle_image_jobs") / day.isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build Catstyle image generation job artifacts from daily pack (structured text only).",
    )
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument(
        "--editorial-profile",
        choices=("charged", "balanced", "supportive"),
        default="charged",
    )
    ap.add_argument("--top", type=int, default=1)
    ap.add_argument("--scan-mode", choices=("noon", "day-window"), default="day-window")
    ap.add_argument("--step-hours", type=int, default=2)
    ap.add_argument("--variants-per-prompt", type=int, default=1, dest="variants_per_prompt")
    ap.add_argument(
        "--jobs-count",
        type=int,
        choices=(1, 2),
        default=None,
        dest="jobs_count",
        help="Emit exactly this many image jobs from the primary pack (1 or 2). Omit for legacy: one job per pack prompt line.",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Write manifests here (default: catstyle_image_jobs/YYYY-MM-DD under cwd)",
    )
    ap.add_argument("--skin-a", default=None, dest="skin_a")
    ap.add_argument("--skin-b", default=None, dest="skin_b")
    ap.add_argument(
        "--world-template",
        default=None,
        dest="world_template",
        help="Optional Catstyle world template key v1 passed into daily pack prompts.",
    )
    ap.add_argument(
        "--scene-template",
        default=None,
        dest="scene_template",
        help="Optional Catstyle scene template key v1 passed into daily pack prompts.",
    )
    ap.add_argument(
        "--render-style-profile",
        default=None,
        dest="render_style_profile",
        help="Optional Catstyle render style profile key v1 passed into daily pack prompts.",
    )
    ap.add_argument(
        "--clean-refs-mode",
        action="store_true",
        dest="clean_refs_mode",
        help=(
            "Minimal reference-first prompts (catstyle_clean_refs_v1): planet + arena refs only, "
            "no legacy canon/hardlock stacks; pair/style reference off unless --style-reference-image set."
        ),
    )
    ap.add_argument(
        "--shot-mode",
        choices=("hero_pair", "epic_arena_showdown", "standard"),
        default=None,
        dest="shot_mode",
        help="Optional shot framing mode for daily pack (default request uses hero_pair).",
    )
    ap.add_argument(
        "--style-reference-image",
        default=None,
        dest="style_reference_image",
        help="Optional local reference image path for style anchoring (providers may or may not support image conditioning).",
    )
    ap.add_argument(
        "--disable-approved-reference-auto",
        action="store_true",
        dest="disable_approved_reference_auto",
        help="Do not auto-pick an approved reference from the Catstyle registry when --style-reference-image is omitted.",
    )
    ap.add_argument(
        "--arena-reference-image",
        default=None,
        dest="arena_reference_image",
        help="Optional local arena/environment reference image (coliseum, sky, floor only).",
    )
    ap.add_argument(
        "--disable-arena-reference-auto",
        action="store_true",
        dest="disable_arena_reference_auto",
        help="Do not auto-pick the default approved arena reference from the arena registry.",
    )
    ap.add_argument(
        "--arena-pool-key",
        default=None,
        dest="arena_pool_key",
        help=(
            "Select arena/environment reference from a registered pool (deterministic stable_by_pair). "
            "Ignored when --arena-reference-image is set."
        ),
    )
    ap.add_argument(
        "--arena-pool-selection",
        default="stable_by_pair",
        dest="arena_pool_selection",
        help="Arena pool selection mode (default: stable_by_pair).",
    )
    ap.add_argument(
        "--use-planet-reference-auto",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="use_planet_reference_auto",
        help="Attach approved per-planet character references to jobs and inject planet reference lock.",
    )
    ap.add_argument(
        "--planet-a",
        default=None,
        dest="planet_a_override",
        help="Manual aspect override v1: planet A (requires --planet-b, --aspect-type, --mode).",
    )
    ap.add_argument(
        "--planet-b",
        default=None,
        dest="planet_b_override",
        help="Manual aspect override v1: planet B.",
    )
    ap.add_argument(
        "--aspect-type",
        default=None,
        dest="aspect_type_override",
        help="Manual aspect override v1: aspect e.g. square, opposition, trine.",
    )
    ap.add_argument(
        "--mode",
        default=None,
        dest="mode_override",
        help="Manual aspect override v1: tension | compensation | mixed | flow.",
    )
    args = ap.parse_args()

    try:
        day = _parse_day(args.date)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    out_dir = args.output_dir if args.output_dir is not None else _default_output_dir(day)

    try:
        result = build_catstyle_image_generation_jobs(
            day,
            editorial_profile=args.editorial_profile,
            top=args.top,
            scan_mode=args.scan_mode,
            step_hours=args.step_hours,
            variants_per_prompt=args.variants_per_prompt,
            output_dir=out_dir,
            skin_a=args.skin_a,
            skin_b=args.skin_b,
            world_template_key=args.world_template,
            scene_template_key=args.scene_template,
            render_style_profile_key=args.render_style_profile,
            shot_mode=args.shot_mode,
            style_reference_image_path=args.style_reference_image,
            disable_approved_reference_auto=args.disable_approved_reference_auto,
            arena_reference_image_path=args.arena_reference_image,
            disable_arena_reference_auto=args.disable_arena_reference_auto,
            arena_pool_key=args.arena_pool_key,
            arena_pool_selection=args.arena_pool_selection,
            use_planet_reference_auto=args.use_planet_reference_auto,
            clean_refs_mode=args.clean_refs_mode,
            planet_a_override=args.planet_a_override,
            planet_b_override=args.planet_b_override,
            aspect_type_override=args.aspect_type_override,
            mode_override=args.mode_override,
            jobs_count=args.jobs_count,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle image generation jobs")
    print(f"  date:              {result.date}")
    print(f"  editorial_profile: {result.editorial_profile}")
    meta = result.style_reference_meta or {}
    src = meta.get("source")
    if meta.get("approved_reference_used"):
        for line in meta.get("log_lines") or []:
            print(f"  {line}")
        if meta.get("approved_reference_registry_key"):
            print(f"  approved_reference_registry_key: {meta.get('approved_reference_registry_key')}")
    elif src == "approved_registry" and meta.get("path"):
        print(f"  style reference:   approved reference auto-resolved: {meta.get('path')}")
    elif src == "explicit" and meta.get("path"):
        print(f"  style reference:   explicit style reference: {meta.get('path')}")
    else:
        print("  style reference:   no reference selected")
    arena_meta = result.arena_reference_meta or {}
    if arena_meta.get("arena_reference_used") and arena_meta.get("arena_reference_image_path"):
        print(f"  arena reference:   {arena_meta.get('arena_reference_image_path')}")
        if arena_meta.get("arena_pool_key"):
            print(f"  arena pool key:    {arena_meta.get('arena_pool_key')}")
        if arena_meta.get("selected_arena_pool_candidate_key"):
            print(f"  arena pool pick:   {arena_meta.get('selected_arena_pool_candidate_key')}")
        if arena_meta.get("arena_selection_mode"):
            print(f"  arena selection:   {arena_meta.get('arena_selection_mode')}")
        if arena_meta.get("arena_reference_registry_key"):
            print(f"  arena registry key: {arena_meta.get('arena_reference_registry_key')}")
    elif arena_meta.get("clean_refs_text_only_arena"):
        print("  arena reference:   clean refs text-only colosseum (no arena image)")
    else:
        print("  arena reference:   no arena reference selected")
    if result.manual_aspect_override:
        mo = result.manual_aspect_override
        print(
            f"  manual override:   {mo.get('planet_a')} {mo.get('aspect_type')} {mo.get('planet_b')}  "
            f"mode={mo.get('mode')}"
        )
    if result.selected_candidate:
        c = result.selected_candidate
        print(
            f"  selected aspect:   {c.get('planet_a')}+{c.get('planet_b')} {c.get('aspect_type')}  "
            f"score={c.get('total_score')}"
        )
    else:
        print("  selected aspect:   (none)")
    if result.secondary_supportive_candidate:
        s = result.secondary_supportive_candidate
        print(
            f"  secondary:         {s.get('planet_a')}+{s.get('planet_b')} {s.get('aspect_type')}"
        )
    print(f"  jobs count:        {len(result.jobs)}")
    if result.message and not result.jobs:
        print(f"  message:           {result.message}")
    if result.output_dir:
        print(f"  output_dir:        {result.output_dir}")
    if result.files_written:
        print("  files_written:")
        for name in result.files_written:
            print(f"    - {name}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
