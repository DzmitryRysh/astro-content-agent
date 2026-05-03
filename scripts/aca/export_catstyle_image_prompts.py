#!/usr/bin/env python3
"""CLI: export Catstyle image prompts as local .txt files (no image gen, no upload)."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from _venus_cli_paths import ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.catstyle_prompt_export import export_catstyle_image_prompts


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
    return Path("catstyle_exports") / day.isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Export Catstyle daily pack prompts as text files for manual image/video production.",
    )
    ap.add_argument("--date", required=True, help="UTC calendar date YYYY-MM-DD")
    ap.add_argument("--top", type=int, default=1, help="Top N from pack (default 1; export uses primary pack only)")
    ap.add_argument(
        "--editorial-profile",
        choices=("charged", "balanced", "supportive"),
        default="charged",
    )
    ap.add_argument("--scan-mode", choices=("noon", "day-window"), default="day-window")
    ap.add_argument("--step-hours", type=int, default=2)
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Destination directory (default: catstyle_exports/YYYY-MM-DD under cwd)",
    )
    args = ap.parse_args()

    try:
        day = _parse_day(args.date)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    out_dir = args.output_dir if args.output_dir is not None else _default_output_dir(day)

    try:
        result = export_catstyle_image_prompts(
            day,
            out_dir,
            top=args.top,
            editorial_profile=args.editorial_profile,
            scan_mode=args.scan_mode,
            step_hours=args.step_hours,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    print()
    print("Catstyle image prompt export")
    print(f"  date:            {result.date}")
    print(f"  output_dir:      {result.output_dir}")
    if result.selected_candidate:
        c = result.selected_candidate
        print(
            f"  selected aspect: {c.get('planet_a')}+{c.get('planet_b')} {c.get('aspect_type')}  "
            f"score={c.get('total_score')}"
        )
    else:
        print("  selected aspect: (none)")
    if result.secondary_supportive_candidate:
        s = result.secondary_supportive_candidate
        print(
            f"  secondary:       {s.get('planet_a')}+{s.get('planet_b')} {s.get('aspect_type')}"
        )
    if not result.success:
        print(f"  status:          {result.message}", file=sys.stderr)
        return 1
    print(f"  files_written:   {len(result.files_written)}")
    for name in result.files_written:
        print(f"    - {name}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
