#!/usr/bin/env python3
"""Thin CLI: manual Venus weekly approval transitions on weekly state JSON (file-based)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from _venus_cli_paths import default_week_dir, ensure_repo_on_path

ensure_repo_on_path()

# action -> (status, approval_status)
_ACTION_TARGET: dict[str, tuple[str, str]] = {
    "approve": ("approved", "approved"),
    "reject": ("rejected", "rejected"),
    "revise": ("needs_revision", "needs_revision"),
}


def _utc_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Update venus_weekly_state JSON (awaiting_approval → approved | rejected | needs_revision)."
    )
    ap.add_argument("week_start", metavar="WEEK_START", help="YYYY-MM-DD (must match state.week_start when present)")
    ap.add_argument(
        "action",
        choices=sorted(_ACTION_TARGET.keys()),
        help="approve | reject | revise",
    )
    ap.add_argument("--note", default=None, help="Optional note recorded as approval_note")
    ap.add_argument("--week-dir", type=Path, default=None, help="Week folder (default: scripts/aca/weekly_venus/<week_start>)")
    ap.add_argument("--state-file", type=Path, default=None, help="Explicit path to venus_weekly_state_*.json")
    args = ap.parse_args()

    week_dir = default_week_dir(args.week_start, args.week_dir)
    state_path = Path(args.state_file) if args.state_file is not None else week_dir / f"venus_weekly_state_{args.week_start}.json"

    if not state_path.is_file():
        print(f"State file not found: {state_path}", file=sys.stderr)
        return 1

    try:
        # utf-8-sig tolerates a UTF-8 BOM (common from Windows editors)
        state: dict = json.loads(state_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {state_path}: {exc}", file=sys.stderr)
        return 1

    ws_in = state.get("week_start")
    if ws_in is not None and str(ws_in) != args.week_start:
        print(
            f"Week mismatch: JSON week_start={ws_in!r} does not match argument {args.week_start!r}.",
            file=sys.stderr,
        )
        return 1

    target_status, target_approval = _ACTION_TARGET[args.action]
    current = str(state.get("status", ""))

    if current == target_status:
        if args.note is not None:
            state["approval_note"] = args.note
            state["approval_timestamp"] = _utc_iso()
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Already {target_status}; no transition needed.")
        return 0

    if current != "awaiting_approval":
        print(
            f"Cannot {args.action}: current status is {current!r}; "
            "only transitioning from awaiting_approval is allowed (or repeat when already at target status).",
            file=sys.stderr,
        )
        return 1

    state["status"] = target_status
    state["approval_status"] = target_approval
    state["approval_timestamp"] = _utc_iso()
    state["approval_note"] = args.note if args.note is not None else ""

    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {state_path.name}: status={target_status}, approval_status={target_approval}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
