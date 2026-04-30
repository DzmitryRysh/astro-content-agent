#!/usr/bin/env python3
"""Thin CLI for Venus weekly agent cycle (delegates to service layer)."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from _venus_cli_paths import default_weekly_venus_root, ensure_repo_on_path

ensure_repo_on_path()

from astro_content_agent.services.content.venus_weekly_agent import print_agent_summary, run_venus_weekly_agent_cycle


def main() -> int:
    p = argparse.ArgumentParser(description="Run Venus weekly agent pipeline (state + drafts + checklist).")
    p.add_argument("week_start", help="Week starting date YYYY-MM-DD")
    p.add_argument("--weekly-venus-root", type=Path, default=None, help="Root folder containing week subdirs (default: scripts/aca/weekly_venus)")
    p.add_argument("--brand-id", default="weekly-workflow", dest="brand_id", metavar="BRAND_ID", help="Brand profile id for astro days selector")
    p.add_argument("--climate-only", action="store_true", help="Climate selector path only (no full drafts)")
    args = p.parse_args()

    try:
        ws = date.fromisoformat(args.week_start)
    except ValueError as e:
        print(f"Invalid week_start date: {e}", file=sys.stderr)
        return 2

    root = default_weekly_venus_root(args.weekly_venus_root)
    out_dir = root / ws.isoformat()
    result = run_venus_weekly_agent_cycle(
        ws,
        out_dir=out_dir,
        brand_id=args.brand_id,
        climate_only=args.climate_only,
        weekly_venus_root=root,
    )
    print_agent_summary(result)
    return 1 if result.error else 0


if __name__ == "__main__":
    raise SystemExit(main())
