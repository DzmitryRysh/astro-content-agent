"""Tests for Catstyle daily handoff builder."""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.models import CatstyleDailyPackResult
from astro_content_agent.services.content.catstyle_daily_handoff import (
    build_catstyle_daily_handoff,
    render_catstyle_daily_handoff_markdown,
)


def _fake_pack_one() -> CatstyleDailyPackResult:
    return CatstyleDailyPackResult(
        date="2026-05-02",
        scan_mode="day-window",
        step_hours=2,
        ranked_candidates_count=3,
        selected_count=1,
        selected_candidates=[
            {
                "planet_a": "Saturn",
                "planet_b": "Venus",
                "aspect_type": "sextile",
                "mode_recommendation": "compensation",
                "total_score": 38,
                "orb": 0.24,
                "source": "deep",
                "recommended_scene_angle": "design studio beat",
                "window_first_seen_hour_utc": 0,
                "window_last_seen_hour_utc": 22,
                "window_samples_seen": 12,
                "closest_hour_utc": 0,
                "is_moon_aspect": False,
            }
        ],
        prompt_packs=[
            {
                "image_prompts": ["prompt a", "prompt b", "prompt c", "prompt d"],
                "animation_prompt": "anim line",
                "negative_prompt": "no text",
                "carousel_idea": "carousel line",
            }
        ],
    )


def _fake_pack_empty() -> CatstyleDailyPackResult:
    return CatstyleDailyPackResult(
        date="2026-06-01",
        scan_mode="day-window",
        step_hours=2,
        ranked_candidates_count=0,
        selected_count=0,
        selected_candidates=[],
        prompt_packs=[],
    )


def test_handoff_contains_prompts_checklist_and_summary() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_handoff.generate_catstyle_daily_pack",
        return_value=_fake_pack_one(),
    ):
        h = build_catstyle_daily_handoff(date(2026, 5, 2), top=1)
    assert h.selected_count == 1
    assert len(h.items) == 1
    it = h.items[0]
    assert it.candidate.planet_a == "Saturn"
    assert it.image_prompts == ["prompt a", "prompt b", "prompt c", "prompt d"]
    assert it.animation_prompt == "anim line"
    assert it.negative_prompt == "no text"
    assert it.carousel_idea == "carousel line"
    assert len(h.next_steps_checklist) == 5
    assert "Cloudinary" in h.next_steps_checklist[3]
    assert it.why_this_post
    assert it.production_plan.recommended_format
    assert it.caption_draft


def test_markdown_includes_required_sections() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_handoff.generate_catstyle_daily_pack",
        return_value=_fake_pack_one(),
    ):
        h = build_catstyle_daily_handoff(date(2026, 5, 2))
    md = render_catstyle_daily_handoff_markdown(h)
    for needle in (
        "## Selected Aspect",
        "## Why this post",
        "## Visual Direction",
        "## Image Prompts",
        "### Prompt 1",
        "## Animation Prompt",
        "## Negative Prompt",
        "## Carousel Idea",
        "## Caption Draft",
        "## Production Checklist",
        "Generate 4 image options",
    ):
        assert needle in md


def test_json_dump_keys() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_handoff.generate_catstyle_daily_pack",
        return_value=_fake_pack_one(),
    ):
        h = build_catstyle_daily_handoff(date(2026, 5, 2))
    blob = h.model_dump(mode="json")
    assert blob["date"] == "2026-05-02"
    assert "items" in blob and len(blob["items"]) == 1
    assert "next_steps_checklist" in blob
    assert "production_plan" in blob["items"][0]


def test_no_candidates_handoff() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_handoff.generate_catstyle_daily_pack",
        return_value=_fake_pack_empty(),
    ):
        h = build_catstyle_daily_handoff(date(2026, 6, 1))
    assert h.selected_count == 0
    assert h.no_post_reason
    assert h.items == []
    md = render_catstyle_daily_handoff_markdown(h)
    assert "No post" in md or "nothing to hand off" in md.lower()
