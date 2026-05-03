#!/usr/bin/env python3
"""CLI: Catstyle daily pack — sky scan + top prompt packs (text JSON, no images)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_daily_pack import generate_catstyle_daily_pack


def _parse_day(s: str) -> date:
    parts = s.strip().split("-")
    if len(parts) != 3:
        raise ValueError("Date must be YYYY-MM-DD")
    try:
        y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as e:
        raise ValueError("Date must be YYYY-MM-DD") from e
    return date(y, m, d)


def _preview(s: str, max_len: int = 220) -> str:
    s = s.replace("\n", " ")
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Catstyle daily prompt pack from sky scan (no images).")
    ap.add_argument("--date", required=True, help="UTC calendar date YYYY-MM-DD")
    ap.add_argument("--top", type=int, default=1, help="How many top-ranked aspects get prompt packs (default 1)")
    ap.add_argument(
        "--scan-mode",
        choices=("noon", "day-window"),
        default="day-window",
        help="Sky scan mode (default day-window)",
    )
    ap.add_argument("--step-hours", type=int, default=2, help="UTC step for day-window scan (default 2)")
    ap.add_argument(
        "--editorial-profile",
        choices=("charged", "balanced", "supportive"),
        default="charged",
        help="How to pick winners after intrinsic ranking (default charged)",
    )
    ap.add_argument("--output", type=Path, default=None, help="Write JSON artifact to this path")
    args = ap.parse_args()

    try:
        day = _parse_day(args.date)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    try:
        pack = generate_catstyle_daily_pack(
            day,
            top=args.top,
            scan_mode=args.scan_mode,
            step_hours=args.step_hours,
            editorial_profile=args.editorial_profile,
        )
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle daily pack")
    print(f"  date:       {pack.date}")
    print(f"  scan_mode:  {pack.scan_mode}" + (f"  step_hours={pack.step_hours}" if pack.step_hours else ""))
    print(f"  editorial:  {pack.editorial_profile}")
    print(f"  candidates: {pack.ranked_candidates_count} ranked, {pack.selected_count} selected for packs")
    print()

    if pack.selected_count == 0:
        print("  No Catstyle-ranked aspects for this date — no prompt packs generated.")
        print()
    else:
        for i, (cand, pp) in enumerate(zip(pack.selected_candidates, pack.prompt_packs, strict=True), start=1):
            print(f"--- Selected {i} ---")
            print(f"  pair:    {cand.get('planet_a')} + {cand.get('planet_b')}  {cand.get('aspect_type')}")
            sel = cand.get("editorial_selection_score")
            sel_s = f"  selection_score={sel}" if sel is not None else ""
            print(
                f"  score:   total={cand.get('total_score')}{sel_s}  "
                f"mode: {cand.get('mode_recommendation')}  source: {cand.get('source')}"
            )
            print(f"  orb:     {cand.get('orb')}")
            if pack.scan_mode == "day-window" and cand.get("window_samples_seen") is not None:
                print(
                    f"  window:  UTC {cand.get('window_first_seen_hour_utc')}h-{cand.get('window_last_seen_hour_utc')}h  "
                    f"closest_hour={cand.get('closest_hour_utc')}  samples={cand.get('window_samples_seen')}"
                )
                if cand.get("is_moon_aspect"):
                    print("  fast Moon aspect")
            print(f"  carousel: {_preview(pp.get('carousel_idea', ''), 280)}")
            ips = pp.get("image_prompts") or []
            if ips:
                print(f"  image 1:  {_preview(ips[0], 240)}")
            print(f"  animation: {_preview(pp.get('animation_prompt', ''), 200)}")
            print()

        if pack.secondary_supportive_candidate:
            sec = pack.secondary_supportive_candidate
            print("--- Secondary supportive (optional) ---")
            print(
                f"  pair: {sec.get('planet_a')} + {sec.get('planet_b')}  {sec.get('aspect_type')}  "
                f"selection_score={sec.get('editorial_selection_score')}  total={sec.get('total_score')}"
            )
            print()

    if args.output is not None:
        out_path = args.output.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(pack.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
