"""Tests for scripts/aca/build_catstyle_daily_handoff.py CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.services.content.catstyle_daily_handoff import (
    CatstyleDailyHandoff,
    CatstyleHandoffCandidateSummary,
    CatstyleHandoffItem,
    CatstyleHandoffProductionPlan,
)


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "build_catstyle_daily_handoff.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_daily_handoff_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def handoff_cli():
    return _load_cli()


def _minimal_handoff() -> CatstyleDailyHandoff:
    c = CatstyleHandoffCandidateSummary(
        planet_a="A",
        planet_b="B",
        aspect_type="trine",
        orb=1.0,
        total_score=25,
        mode_recommendation="mixed",
        source="seed",
        recommended_scene_angle="angle",
    )
    plan = CatstyleHandoffProductionPlan(
        recommended_format="carousel",
        image_generation_notes="img",
        capcut_animation_notes="cap",
        manual_review_notes="man",
    )
    item = CatstyleHandoffItem(
        candidate=c,
        why_this_post="because",
        production_plan=plan,
        image_prompts=["p1"],
        animation_prompt="anim",
        negative_prompt="neg",
        carousel_idea="car",
        caption_draft="cap draft",
    )
    return CatstyleDailyHandoff(
        date="2026-05-02",
        scan_mode="day-window",
        step_hours=2,
        ranked_candidates_count=1,
        selected_count=1,
        items=[item],
    )


def test_cli_invalid_date(handoff_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["build_catstyle_daily_handoff.py", "--date", "bad"]
        assert handoff_cli.main() == 1
    finally:
        sys.argv = old
    err = capsys.readouterr().err
    assert "YYYY" in err or "Date" in err


def test_cli_writes_md(handoff_cli, tmp_path: Path) -> None:
    out = tmp_path / "h.md"
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_daily_handoff.py",
            "--date",
            "2026-05-02",
            "--format",
            "md",
            "--output",
            str(out),
        ]
        with patch.object(handoff_cli, "build_catstyle_daily_handoff", return_value=_minimal_handoff()):
            assert handoff_cli.main() == 0
    finally:
        sys.argv = old
    text = out.read_text(encoding="utf-8")
    assert "# Catstyle Daily Handoff" in text
    assert "## Production Checklist" in text


def test_cli_writes_json(handoff_cli, tmp_path: Path) -> None:
    out = tmp_path / "h.json"
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_daily_handoff.py",
            "--date",
            "2026-05-02",
            "--format",
            "json",
            "--output",
            str(out),
        ]
        with patch.object(handoff_cli, "build_catstyle_daily_handoff", return_value=_minimal_handoff()):
            assert handoff_cli.main() == 0
    finally:
        sys.argv = old
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["date"] == "2026-05-02"
    assert data["items"][0]["caption_draft"] == "cap draft"
