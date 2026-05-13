#!/usr/bin/env python3
"""EXPERIMENTAL: Composite glyphs onto an image copy — not default Catstyle publishing."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import REPO_ROOT, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.core.repo_env import load_repo_dotenv_if_present

load_repo_dotenv_if_present(REPO_ROOT)

from astro_content_agent.services.content.catstyle_symbol_overlay import (
    FLAG_LAYOUT_PRESETS,
    PLANET_GLYPHS,
    apply_dual_flag_symbol_overlay,
    apply_symbol_overlay,
    default_overlay_output_path,
    default_symbols_fixed_output_path,
    glyph_for_planet,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "EXPERIMENTAL manual glyph compositing (optional repair tool). "
            "Normal Catstyle: planetary signs should be painted into flags in-image. "
            "Use --planet-a + --planet-b for dual placement tests only."
        ),
    )
    ap.add_argument("--input", type=Path, required=True, help="Source PNG/JPG")
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination (default: *_symbols_fixed.* for dual; *_overlay.* for single; not default publish)",
    )
    ap.add_argument(
        "--planet-a",
        type=str,
        default=None,
        metavar="NAME",
        help="Left / character-A planet (pair with --planet-b)",
    )
    ap.add_argument(
        "--planet-b",
        type=str,
        default=None,
        metavar="NAME",
        help="Right / character-B planet (pair with --planet-a)",
    )
    ap.add_argument(
        "--layout",
        choices=sorted(FLAG_LAYOUT_PRESETS.keys()),
        default="poster_ab",
        help="Normalized anchor preset for dual-flag mode (default poster_ab)",
    )
    ap.add_argument("--ax", type=float, default=None, help="Override A anchor x 0–1 (dual mode)")
    ap.add_argument("--ay", type=float, default=None, help="Override A anchor y 0–1 (dual mode)")
    ap.add_argument("--bx", type=float, default=None, help="Override B anchor x 0–1 (dual mode)")
    ap.add_argument("--by", type=float, default=None, help="Override B anchor y 0–1 (dual mode)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--glyph", help="Single character (single-glyph mode only)")
    g.add_argument(
        "--planet",
        choices=sorted(PLANET_GLYPHS.keys()),
        help="One planet → canonical glyph (single-glyph mode only)",
    )
    ap.add_argument("--x", type=float, default=0.5, help="Single mode: horizontal anchor 0–1")
    ap.add_argument("--y", type=float, default=0.35, help="Single mode: vertical anchor 0–1")
    ap.add_argument("--size", type=int, default=128, help="Font size in pixels (default 128)")
    ap.add_argument("--font-path", type=Path, default=None, help="Optional TTF path")
    ap.add_argument("--fill", type=str, default="#f7f2e4", help="Glyph fill (single mode; dual uses same default)")
    ap.add_argument("--stroke-width", type=int, default=3, help="Outline width")
    ap.add_argument("--stroke-fill", type=str, default="#14081f", help="Outline color")
    ap.add_argument(
        "--no-premium-glow",
        action="store_true",
        help="Single mode only: skip gold glow (plain stroke text)",
    )
    args = ap.parse_args()

    inp = Path(args.input).expanduser().resolve()
    if not inp.is_file():
        print(f"Input not found: {inp}", file=sys.stderr)
        return 2

    has_pair = args.planet_a is not None and args.planet_b is not None
    has_partial_pair = (args.planet_a is not None) ^ (args.planet_b is not None)
    if has_partial_pair:
        print("Dual mode requires both --planet-a and --planet-b", file=sys.stderr)
        return 2

    if has_pair and (args.planet or args.glyph):
        print("Do not combine --planet-a/--planet-b with --planet or --glyph", file=sys.stderr)
        return 2

    if has_pair:
        a_xy = (args.ax, args.ay) if args.ax is not None and args.ay is not None else None
        b_xy = (args.bx, args.by) if args.bx is not None and args.by is not None else None
        if (args.ax is not None) ^ (args.ay is not None):
            print("Dual overrides: provide both --ax and --ay for A, or neither", file=sys.stderr)
            return 2
        if (args.bx is not None) ^ (args.by is not None):
            print("Dual overrides: provide both --bx and --by for B, or neither", file=sys.stderr)
            return 2
        out = Path(args.output).expanduser().resolve() if args.output else default_symbols_fixed_output_path(inp)
        try:
            apply_dual_flag_symbol_overlay(
                inp,
                out,
                planet_a=args.planet_a,
                planet_b=args.planet_b,
                layout_preset=args.layout,
                size_px=int(args.size),
                font_path=args.font_path,
                fill=args.fill,
                stroke_width=int(args.stroke_width),
                stroke_fill=args.stroke_fill,
                a_xy=a_xy,
                b_xy=b_xy,
            )
        except (FileNotFoundError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 1
        print(f"wrote {out}")
        return 0

    if not args.planet and not args.glyph:
        print("Provide --planet-a and --planet-b, or --planet, or --glyph", file=sys.stderr)
        return 2

    if args.planet:
        ch = glyph_for_planet(args.planet)
        if not ch:
            print(f"Unknown planet: {args.planet}", file=sys.stderr)
            return 2
    else:
        ch = (args.glyph or "").strip()
        if not ch:
            print("--glyph must be non-empty", file=sys.stderr)
            return 2

    out = Path(args.output).expanduser().resolve() if args.output else default_overlay_output_path(inp)

    try:
        apply_symbol_overlay(
            inp,
            out,
            glyph=ch,
            x_norm=float(args.x),
            y_norm=float(args.y),
            size_px=int(args.size),
            font_path=args.font_path,
            fill=args.fill,
            stroke_width=int(args.stroke_width),
            stroke_fill=args.stroke_fill,
            premium_glow=not args.no_premium_glow,
        )
    except (FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
