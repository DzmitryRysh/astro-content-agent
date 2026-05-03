"""Tests for scripts/aca/generate_catstyle_sky_candidates.py CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.models import CatstyleCandidate, CatstyleCandidateRankingResult


def _load_sky_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    cli_path = repo / "scripts" / "aca" / "generate_catstyle_sky_candidates.py"
    spec = importlib.util.spec_from_file_location("_generate_catstyle_sky_candidates_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def sky_cli():
    return _load_sky_cli()


def _fake_ranking() -> CatstyleCandidateRankingResult:
    return CatstyleCandidateRankingResult(
        ranked=[
            CatstyleCandidate(
                planet_a="Pluto",
                planet_b="Moon",
                aspect_type="conjunction",
                mode_recommendation="tension",
                visual_score=6,
                emotional_score=6,
                comedy_score=6,
                clarity_score=6,
                total_score=30,
                reason="Transit seed v0 (Pluto->Moon): test.",
                recommended_scene_angle="shadow / pillow",
                orb=0.4,
                orb_bonus=5,
                source="seed",
            )
        ],
        unsupported=[],
    )


def test_cli_prints_ranked(sky_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["generate_catstyle_sky_candidates.py", "--date", "2026-05-02"]
        with patch.object(sky_cli, "scan_catstyle_sky_aspects", return_value=_fake_ranking()):
            assert sky_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Pluto" in out and "Moon" in out
    assert "conjunction" in out
    assert "total_score" in out or "total_score=30" in out.replace(" ", "")


def test_cli_writes_json_output(sky_cli, tmp_path: Path) -> None:
    out_file = tmp_path / "sky.json"
    old = sys.argv[:]
    try:
        sys.argv = [
            "generate_catstyle_sky_candidates.py",
            "--date",
            "2026-01-15",
            "--output",
            str(out_file),
        ]
        with patch.object(sky_cli, "scan_catstyle_sky_aspects", return_value=_fake_ranking()):
            assert sky_cli.main() == 0
    finally:
        sys.argv = old
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["ranked"][0]["planet_a"] == "Pluto"
    assert data["ranked"][0]["orb"] == 0.4


def test_cli_date_parse_invalid(sky_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["generate_catstyle_sky_candidates.py", "--date", "not-a-date"]
        assert sky_cli.main() == 1
    finally:
        sys.argv = old
    assert "YYYY" in capsys.readouterr().err or "Date" in capsys.readouterr().err


def test_cli_no_aspects_message(sky_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["generate_catstyle_sky_candidates.py", "--date", "2026-06-01"]
        empty = CatstyleCandidateRankingResult(ranked=[], unsupported=[])
        with patch.object(sky_cli, "scan_catstyle_sky_aspects", return_value=empty):
            assert sky_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "No outer-to-personal" in out or "No outer" in out
