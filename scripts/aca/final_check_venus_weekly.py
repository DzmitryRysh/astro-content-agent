#!/usr/bin/env python3
"""Thin CLI: final-check JSON for Venus weekly handoff."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _venus_cli_paths import default_week_dir, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.venus_final_check import run_final_check


def main() -> int:
    p = argparse.ArgumentParser(description="Run Venus weekly final-check (writes venus_final_check_<week>.json).")
    p.add_argument("week_start", help="YYYY-MM-DD")
    p.add_argument("--week-dir", type=Path, default=None, help="Week folder path")
    p.add_argument("--state-file", type=Path, default=None)
    p.add_argument("--handoff-file", type=Path, default=None)
    p.add_argument("--no-markdown-summary", action="store_true")
    args = p.parse_args()

    week_dir = default_week_dir(args.week_start, args.week_dir)
    try:
        result = run_final_check(
            week_dir=week_dir,
            state_path=Path(args.state_file) if args.state_file else None,
            handoff_path=Path(args.handoff_file) if args.handoff_file else None,
            week_start_hint=args.week_start,
            write_markdown_summary=not args.no_markdown_summary,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    summary = {
        "week_start": result.week_start,
        "week_end": result.week_end,
        "final_check_status": result.final_check_status,
        "ready_for_publish": result.ready_for_publish,
        "issue_count": len(result.issues),
        "warning_count": len(result.warnings),
        "out_path": str(result.out_path) if result.out_path else None,
    }
    print(json.dumps(summary, indent=2))
    if result.issues:
        print("\nIssues:", file=sys.stderr)
        for i in result.issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
