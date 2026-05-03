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

from astro_content_agent.services.content.catstyle_sky_aspect_scan import (
    scan_catstyle_sky_aspect_windows,
    scan_catstyle_sky_aspects,
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


def _print_result(result, *, top: int | None, scan_mode: str) -> None:
    ranked = result.ranked
    if top is not None:
        ranked = ranked[: max(0, top)]

    print()
    print(f"Catstyle sky aspect scan (scan_mode={scan_mode})")
    if not result.ranked:
        print("  No outer-to-personal major aspects within Catstyle v0 orbs for this date/window.")
        print()
        return

    print(f"  Ranked candidates: {len(ranked)}" + (f" (showing top {top})" if top is not None else ""))
    print()
    for i, c in enumerate(ranked, start=1):
        print(f"{i}. {c.planet_a} + {c.planet_b}  {c.aspect_type}")
        print(f"   orb(min)={c.orb} deg  total_score={c.total_score}  mode={c.mode_recommendation}  source={c.source}")
        if c.orb is not None:
            print(f"   orb_bonus=+{c.orb_bonus}")
        if scan_mode == "day-window" and c.window_samples_seen is not None:
            print(
                f"   UTC window: {c.window_first_seen_hour_utc}h-{c.window_last_seen_hour_utc}h  "
                f"samples={c.window_samples_seen}  closest_hour_utc={c.closest_hour_utc}"
            )
            if c.is_moon_aspect:
                print("   fast Moon aspect (sampled across day window)")
        print(f"   angle: {c.recommended_scene_angle}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan sky for Catstyle outer→personal aspects and rank.")
    ap.add_argument("--date", required=True, help="UTC calendar date YYYY-MM-DD")
    ap.add_argument(
        "--scan-mode",
        choices=("noon", "day-window"),
        default="day-window",
        help="noon: single 12:00 UTC chart; day-window: sample 0..22 UTC every --step-hours",
    )
    ap.add_argument("--step-hours", type=int, default=2, help="UTC sampling step for day-window mode (default 2)")
    ap.add_argument("--output", type=Path, default=None, help="Write JSON (full ranking) to this path")
    ap.add_argument("--top", type=int, default=None, help="Only print this many rows (full result still saved with --output)")
    args = ap.parse_args()

    try:
        day = _parse_day(args.date)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    step = max(1, int(args.step_hours))
    try:
        if args.scan_mode == "noon":
            result = scan_catstyle_sky_aspects(day)
        else:
            result = scan_catstyle_sky_aspect_windows(day, step_hours=step)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    _print_result(result, top=args.top, scan_mode=args.scan_mode)

    if args.output is not None:
        out_path = args.output.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blob = result.model_dump(mode="json")
        blob["scan_mode"] = args.scan_mode
        blob["step_hours"] = step if args.scan_mode == "day-window" else None
        out_path.write_text(json.dumps(blob, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
