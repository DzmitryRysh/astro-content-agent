"""Tests for scripts/aca/generate_catstyle_daily_pack.py CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.models import CatstyleDailyPackResult


def _load_daily_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    cli_path = repo / "scripts" / "aca" / "generate_catstyle_daily_pack.py"
    spec = importlib.util.spec_from_file_location("_generate_catstyle_daily_pack_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def daily_cli():
    return _load_daily_cli()


def _fake_pack() -> CatstyleDailyPackResult:
    return CatstyleDailyPackResult(
        date="2026-05-02",
        scan_mode="day-window",
        step_hours=2,
        ranked_candidates_count=2,
        selected_count=1,
        selected_candidates=[
            {
                "planet_a": "Pluto",
                "planet_b": "Moon",
                "aspect_type": "conjunction",
                "mode_recommendation": "tension",
                "total_score": 30,
                "orb": 0.2,
                "window_first_seen_hour_utc": 0,
                "window_last_seen_hour_utc": 4,
                "window_samples_seen": 3,
                "closest_hour_utc": 0,
                "is_moon_aspect": True,
            }
        ],
        prompt_packs=[
            {
                "image_prompts": ["alpha " * 30],
                "animation_prompt": "anim preview",
                "negative_prompt": "neg",
                "carousel_idea": "carousel text here",
            }
        ],
    )


def test_cli_prints_summary(daily_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["generate_catstyle_daily_pack.py", "--date", "2026-05-02", "--top", "1"]
        with patch.object(daily_cli, "generate_catstyle_daily_pack", return_value=_fake_pack()):
            assert daily_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "2026-05-02" in out
    assert "Pluto" in out and "Moon" in out
    assert "carousel" in out.lower()


def test_cli_writes_json(daily_cli, tmp_path: Path) -> None:
    out_file = tmp_path / "daily.json"
    old = sys.argv[:]
    try:
        sys.argv = [
            "generate_catstyle_daily_pack.py",
            "--date",
            "2026-05-02",
            "--output",
            str(out_file),
        ]
        with patch.object(daily_cli, "generate_catstyle_daily_pack", return_value=_fake_pack()):
            assert daily_cli.main() == 0
    finally:
        sys.argv = old
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["date"] == "2026-05-02"
    assert data["prompt_packs"][0]["image_prompts"][0].startswith("alpha")


def test_cli_empty_pack_message(daily_cli, capsys: pytest.CaptureFixture[str]) -> None:
    empty = CatstyleDailyPackResult(
        date="2026-06-01",
        scan_mode="day-window",
        step_hours=2,
        ranked_candidates_count=0,
        selected_count=0,
        selected_candidates=[],
        prompt_packs=[],
    )
    old = sys.argv[:]
    try:
        sys.argv = ["generate_catstyle_daily_pack.py", "--date", "2026-06-01"]
        with patch.object(daily_cli, "generate_catstyle_daily_pack", return_value=empty):
            assert daily_cli.main() == 0
    finally:
        sys.argv = old
    assert "No Catstyle-ranked" in capsys.readouterr().out or "no prompt packs" in capsys.readouterr().out.lower()
