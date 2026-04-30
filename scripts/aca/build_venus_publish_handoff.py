#!/usr/bin/env python3
"""Thin CLI: approved weekly state → publish handoff JSON."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _venus_cli_paths import default_week_dir, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.venus_publish_handoff import build_publish_handoff, print_handoff_summary


def main() -> int:
    p = argparse.ArgumentParser(description="Build venus_publish_handoff_<week>.json from approved state.")
    p.add_argument("week_start", help="YYYY-MM-DD (folder name under weekly root)")
    p.add_argument("--week-dir", type=Path, default=None, help="Week folder path")
    p.add_argument("--state-file", type=Path, default=None, help="Explicit venus_weekly_state_*.json path")
    p.add_argument("--no-markdown-summary", action="store_true", help="Skip brief handoff .md summary")
    args = p.parse_args()

    week_dir = default_week_dir(args.week_start, args.week_dir)
    try:
        result = build_publish_handoff(
            week_dir=week_dir,
            state_path=Path(args.state_file) if args.state_file else None,
            week_start_hint=args.week_start,
            write_markdown_summary=not args.no_markdown_summary,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    print_handoff_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
