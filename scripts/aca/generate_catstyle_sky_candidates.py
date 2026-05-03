#!/usr/bin/env python3
"""CLI: real-sky outer→personal aspects for a date, ranked for Catstyle."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_sky_aspect_scan import scan_catstyle_sky_aspects


def _parse_day(s: str) -> date:
    parts = s.strip().split("-")
    if len(parts) != 3:
        raise ValueError("Date must be YYYY-MM-DD")
    try:
        y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as e:
        raise ValueError("Date must be YYYY-MM-DD") from e
    return date(y, m, d)


def _print_result(result, *, top: int | None) -> None:
    ranked = result.ranked
    if top is not None:
        ranked = ranked[: max(0, top)]

    print()
    print("Catstyle sky aspect scan (v0)")
    if not result.ranked:
        print("  No outer-to-personal major aspects within Catstyle v0 orbs for this date.")
        print()
        return

    print(f"  Ranked candidates: {len(ranked)}" + (f" (showing top {top})" if top is not None else ""))
    print()
    for i, c in enumerate(ranked, start=1):
        print(f"{i}. {c.planet_a} + {c.planet_b}  {c.aspect_type}")
        print(f"   orb={c.orb} deg  total_score={c.total_score}  mode={c.mode_recommendation}  source={c.source}")
        if c.orb is not None:
            print(f"   orb_bonus=+{c.orb_bonus}")
        print(f"   angle: {c.recommended_scene_angle}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan sky for Catstyle outer→personal aspects and rank.")
    ap.add_argument("--date", required=True, help="UTC date YYYY-MM-DD (positions at noon UTC)")
    ap.add_argument("--output", type=Path, default=None, help="Write JSON (full ranking) to this path")
    ap.add_argument("--top", type=int, default=None, help="Only print this many rows (full result still saved with --output)")
    args = ap.parse_args()

    try:
        day = _parse_day(args.date)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    try:
        result = scan_catstyle_sky_aspects(day)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    _print_result(result, top=args.top)

    if args.output is not None:
        out_path = args.output.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blob = result.model_dump(mode="json")
        out_path.write_text(json.dumps(blob, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
