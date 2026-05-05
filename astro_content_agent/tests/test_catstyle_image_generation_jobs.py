"""Tests for Catstyle image generation jobs v0 (no APIs)."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.models import CatstyleDailyPackResult
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    CatstyleImageGenerationJobsResult,
    build_catstyle_image_generation_jobs,
)


def _fake_pack_one_primary() -> CatstyleDailyPackResult:
    primary = {
        "planet_a": "Jupiter",
        "planet_b": "Mars",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 38,
        "orb": 1.2,
        "source": "seed",
        "editorial_bonus": 5,
        "editorial_selection_score": 43,
    }
    secondary = {
        "planet_a": "Saturn",
        "planet_b": "Venus",
        "aspect_type": "sextile",
        "mode_recommendation": "compensation",
        "total_score": 46,
        "source": "deep",
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
                "image_prompts": ["prompt line one", "prompt line two", "three", "four"],
                "animation_prompt": "anim body",
                "negative_prompt": "neg body",
                "carousel_idea": "carousel body",
                "art_direction_profile": {
                    "version": "catstyle-art-direction-v0",
                    "energy": "charged",
                    "editorial_profile": "charged",
                    "mode": "tension",
                    "planet_a": "Jupiter",
                    "planet_b": "Mars",
                    "skin_a": None,
                    "skin_b": None,
                },
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


def test_build_jobs_four_prompts_all_pending(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            editorial_profile="charged",
            output_dir=tmp_path / "jobs",
        )
    assert isinstance(r, CatstyleImageGenerationJobsResult)
    assert len(r.jobs) == 4
    assert all(j.status == "pending" for j in r.jobs)
    assert r.jobs[0].planet_a == "Jupiter" and r.jobs[0].planet_b == "Mars"
    assert r.jobs[0].prompt_index == 1
    assert r.jobs[0].prompt_text == "prompt line one"
    assert r.jobs[0].negative_prompt == "neg body"
    assert r.jobs[0].animation_prompt == "anim body"
    assert r.jobs[0].carousel_idea == "carousel body"
    assert r.jobs[0].art_direction_profile is not None
    assert r.jobs[0].art_direction_profile.get("energy") == "charged"
    assert r.jobs[0].selection_score == 43
    assert r.jobs[0].orb == pytest.approx(1.2)
    assert r.jobs[0].job_id == "catstyle-2026-05-02-001"
    assert "jupiter_mars_square" in r.jobs[0].suggested_output_name


def test_variants_per_prompt_duplicates_jobs(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            variants_per_prompt=2,
            output_dir=tmp_path / "v",
        )
    assert len(r.jobs) == 8
    assert r.jobs[0].prompt_index == 1 and r.jobs[0].variant_index == 0
    assert r.jobs[1].prompt_index == 1 and r.jobs[1].variant_index == 1
    assert r.jobs[0].prompt_text == r.jobs[1].prompt_text


def test_output_writes_manifest_and_prompt_files(tmp_path: Path) -> None:
    out = tmp_path / "out"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(date(2026, 5, 2), output_dir=out)
    assert (out / "image_generation_jobs.json").is_file()
    assert (out / "job_01_prompt.txt").read_text(encoding="utf-8").strip() == "prompt line one"
    assert (out / "job_04_prompt.txt").read_text(encoding="utf-8").strip() == "four"
    assert "neg body" in (out / "negative_prompt.txt").read_text(encoding="utf-8")
    assert "anim body" in (out / "animation_prompt.txt").read_text(encoding="utf-8")
    summary = (out / "manifest_summary.txt").read_text(encoding="utf-8")
    assert "Saturn" in summary and "Venus" in summary
    assert "Secondary supportive" in summary
    assert "image_generation_jobs.json" in r.files_written
    assert "manifest_summary.txt" in r.files_written


def test_no_selected_returns_empty_jobs_no_files(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_empty(),
    ):
        r = build_catstyle_image_generation_jobs(date(2026, 6, 1), output_dir=tmp_path / "empty")
    assert r.jobs == []
    assert r.message
    assert r.files_written == []
    assert not (tmp_path / "empty").exists()


def test_pack_passes_skins_to_daily_pack(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ) as m:
        build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            output_dir=tmp_path / "s",
            skin_a=None,
            skin_b="spartan_king",
        )
    m.assert_called_once()
    kw = m.call_args.kwargs
    assert kw.get("skin_b") == "spartan_king"
