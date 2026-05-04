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
        "--output-dir",
        type=Path,
        default=None,
        help="Write manifests here (default: catstyle_image_jobs/YYYY-MM-DD under cwd)",
    )
    ap.add_argument("--skin-a", default=None, dest="skin_a")
    ap.add_argument("--skin-b", default=None, dest="skin_b")
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
