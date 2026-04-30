"""Shared paths for Venus weekly CLI wrappers (no business logic)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def ensure_repo_on_path() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def default_week_dir(week_start: str, week_dir: Path | None) -> Path:
    if week_dir is not None:
        return Path(week_dir)
    return REPO_ROOT / "scripts" / "aca" / "weekly_venus" / week_start


def default_weekly_venus_root(weekly_venus_root: Path | None) -> Path:
    return Path(weekly_venus_root) if weekly_venus_root is not None else REPO_ROOT / "scripts" / "aca" / "weekly_venus"
