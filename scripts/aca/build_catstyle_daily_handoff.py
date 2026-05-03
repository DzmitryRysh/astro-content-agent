#!/usr/bin/env python3
"""CLI: build Catstyle daily production handoff (Markdown or JSON)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_daily_handoff import (
    build_catstyle_daily_handoff,
    render_catstyle_daily_handoff_markdown,
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


def _print_summary(h) -> None:
    print()
    print("Catstyle daily handoff")
    print(f"  date:        {h.date}")
    print(f"  scan_mode:   {h.scan_mode}" + (f"  step_hours={h.step_hours}" if h.step_hours else ""))
    print(f"  ranked:      {h.ranked_candidates_count}  selected: {h.selected_count}")
    if h.no_post_reason:
        print(f"  status:      {h.no_post_reason}")
        return
    for i, it in enumerate(h.items, start=1):
        c = it.candidate
        label = f"  item {i}:" if len(h.items) > 1 else "  primary:"
        print(f"{label} {c.planet_a}+{c.planet_b} {c.aspect_type}  score={c.total_score}  mode={c.mode_recommendation}")
        if c.orb is not None:
            print(f"         orb={c.orb}  source={c.source}")
        if c.window_samples_seen is not None:
            print(
                f"         window UTC {c.window_first_seen_hour_utc}h-{c.window_last_seen_hour_utc}h  "
                f"samples={c.window_samples_seen}"
            )
        prev = (it.image_prompts[0][:160] + "…") if it.image_prompts else "(no prompts)"
        print(f"         prompt preview: {prev}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Catstyle daily handoff for manual image / CapCut / IG prep.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--top", type=int, default=1)
    ap.add_argument("--scan-mode", choices=("noon", "day-window"), default="day-window")
    ap.add_argument("--step-hours", type=int, default=2)
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument("--format", choices=("json", "md"), default="md")
    args = ap.parse_args()

    try:
        day = _parse_day(args.date)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    try:
        handoff = build_catstyle_daily_handoff(
            day,
            top=args.top,
            scan_mode=args.scan_mode,
            step_hours=args.step_hours,
        )
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    _print_summary(handoff)

    if args.output is not None:
        out_path = args.output.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "md":
            out_path.write_text(render_catstyle_daily_handoff_markdown(handoff), encoding="utf-8")
        else:
            out_path.write_text(
                json.dumps(handoff.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        print(f"Wrote: {out_path}")
    elif args.format == "md":
        print(render_catstyle_daily_handoff_markdown(handoff))
    else:
        print(json.dumps(handoff.model_dump(mode="json"), indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
