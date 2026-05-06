"""Tests for Catstyle image prompt export v0."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.models import CatstyleDailyPackResult
from astro_content_agent.services.content.catstyle_prompt_export import (
    CatstylePromptExportResult,
    export_catstyle_image_prompts,
)


def _fake_pack_with_primary() -> CatstyleDailyPackResult:
    primary = {
        "planet_a": "Jupiter",
        "planet_b": "Mars",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 38,
        "orb": 1.2,
        "source": "seed",
        "recommended_scene_angle": "Mars charges Jupiter.",
        "editorial_profile": "charged",
        "editorial_bonus": 5,
        "editorial_selection_score": 43,
    }
    secondary = {
        "planet_a": "Saturn",
        "planet_b": "Venus",
        "aspect_type": "sextile",
        "mode_recommendation": "compensation",
        "total_score": 46,
        "orb": 0.2,
        "source": "deep",
        "recommended_scene_angle": "Studio frame.",
        "editorial_selection_score": 52,
    }
    return CatstyleDailyPackResult(
        date="2026-05-02",
        scan_mode="day-window",
        step_hours=2,
        editorial_profile="charged",
        ranked_candidates_count=2,
        selected_count=1,
        ranked_candidates=[dict(primary)],
        selected_candidates=[primary],
        primary_candidate=primary,
        secondary_supportive_candidate=secondary,
        prompt_packs=[
            {
                "image_prompts": ["alpha prompt", "beta prompt"],
                "animation_prompt": "loop the cats",
                "negative_prompt": "no logos",
                "carousel_idea": "two hero beats then payoff",
            }
        ],
    )


def _fake_pack_empty() -> CatstyleDailyPackResult:
    return CatstyleDailyPackResult(
        date="2026-06-01",
        scan_mode="day-window",
        step_hours=2,
        editorial_profile="charged",
        ranked_candidates_count=0,
        selected_count=0,
        ranked_candidates=[],
        selected_candidates=[],
        prompt_packs=[],
    )


def test_export_creates_dir_and_writes_prompt_files(tmp_path: Path) -> None:
    out = tmp_path / "export_here"
    with patch(
        "astro_content_agent.services.content.catstyle_prompt_export.generate_catstyle_daily_pack",
        return_value=_fake_pack_with_primary(),
    ):
        result = export_catstyle_image_prompts(date(2026, 5, 2), out)

    assert result.success
    assert result.date == "2026-05-02"
    assert set(result.files_written) == {
        "prompt_1.txt",
        "prompt_2.txt",
        "animation_prompt.txt",
        "negative_prompt.txt",
        "carousel_idea.txt",
        "selected_aspect_summary.txt",
    }
    assert (out / "prompt_1.txt").read_text(encoding="utf-8").strip() == "alpha prompt"
    assert (out / "prompt_2.txt").read_text(encoding="utf-8").strip() == "beta prompt"
    assert "loop the cats" in (out / "animation_prompt.txt").read_text(encoding="utf-8")
    assert "no logos" in (out / "negative_prompt.txt").read_text(encoding="utf-8")
    assert "two hero beats" in (out / "carousel_idea.txt").read_text(encoding="utf-8")
    summary = (out / "selected_aspect_summary.txt").read_text(encoding="utf-8")
    assert "Jupiter" in summary and "Mars" in summary
    assert "Saturn" in summary and "Venus" in summary
    assert "Secondary supportive" in summary


def test_export_short_image_prompt_list_pads_empty_slots(tmp_path: Path) -> None:
    pack = _fake_pack_with_primary()
    pack.prompt_packs[0]["image_prompts"] = ["only one"]
    with patch(
        "astro_content_agent.services.content.catstyle_prompt_export.generate_catstyle_daily_pack",
        return_value=pack,
    ):
        result = export_catstyle_image_prompts(date(2026, 5, 2), tmp_path / "out")
    assert result.success
    assert (tmp_path / "out" / "prompt_1.txt").read_text(encoding="utf-8").strip() == "only one"
    assert not (tmp_path / "out" / "prompt_2.txt").exists()


def test_export_no_candidates_returns_failure_without_crash(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_prompt_export.generate_catstyle_daily_pack",
        return_value=_fake_pack_empty(),
    ):
        result = export_catstyle_image_prompts(date(2026, 6, 1), tmp_path / "empty_out")

    assert isinstance(result, CatstylePromptExportResult)
    assert not result.success
    assert result.files_written == []
    assert result.message
    assert not (tmp_path / "empty_out").exists() or not list((tmp_path / "empty_out").iterdir())


def test_export_summary_primary_only_when_no_secondary(tmp_path: Path) -> None:
    pack = _fake_pack_with_primary()
    pack.secondary_supportive_candidate = None
    with patch(
        "astro_content_agent.services.content.catstyle_prompt_export.generate_catstyle_daily_pack",
        return_value=pack,
    ):
        result = export_catstyle_image_prompts(date(2026, 5, 2), tmp_path / "solo")
    summary = (tmp_path / "solo" / "selected_aspect_summary.txt").read_text(encoding="utf-8")
    assert "Primary" in summary
    assert "Secondary supportive" not in summary
