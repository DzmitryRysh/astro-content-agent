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


def _fake_pack_charged_with_secondary() -> CatstyleDailyPackResult:
    primary = {
        "planet_a": "Jupiter",
        "planet_b": "Mars",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 38,
        "orb": 1.34,
        "source": "seed",
        "recommended_scene_angle": "Mars charges Jupiter; timing gag.",
        "window_first_seen_hour_utc": 0,
        "window_last_seen_hour_utc": 22,
        "window_samples_seen": 12,
        "closest_hour_utc": 22,
        "is_moon_aspect": False,
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
        "orb": 0.24,
        "source": "deep",
        "recommended_scene_angle": "Design studio / editorial frame.",
        "editorial_selection_score": 52,
        "editorial_bonus": 6,
    }
    return CatstyleDailyPackResult(
        date="2026-05-02",
        scan_mode="day-window",
        step_hours=2,
        editorial_profile="charged",
        ranked_candidates_count=3,
        selected_count=1,
        ranked_candidates=[dict(primary), dict(secondary)],
        selected_candidates=[primary],
        primary_candidate=primary,
        secondary_supportive_candidate=secondary,
        prompt_packs=[
            {
                "image_prompts": ["p1", "p2", "p3", "p4"],
                "animation_prompt": "anim",
                "negative_prompt": "neg",
                "carousel_idea": "car idea",
            }
        ],
    )


def _fake_pack_one() -> CatstyleDailyPackResult:
    sel = {
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
        "editorial_profile": "charged",
        "editorial_bonus": -3,
        "editorial_selection_score": 35,
    }
    return CatstyleDailyPackResult(
        date="2026-05-02",
        scan_mode="day-window",
        step_hours=2,
        editorial_profile="charged",
        ranked_candidates_count=3,
        selected_count=1,
        ranked_candidates=[dict(sel)],
        selected_candidates=[sel],
        primary_candidate=sel,
        secondary_supportive_candidate=None,
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
        editorial_profile="charged",
        ranked_candidates_count=0,
        selected_count=0,
        ranked_candidates=[],
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
    assert it.why_this_aspect_won
    assert "charged" in it.why_this_aspect_won.lower()
    assert h.editorial_profile == "charged"
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
        "## Main Charged Aspect",
        "## Why this aspect won",
        "Editorial profile **charged**",
        "## Why this post",
        "## Visual Direction",
        "## Image Prompts",
        "### Prompt 1",
        "## Animation Prompt",
        "## Negative Prompt",
        "## Carousel Idea (from prompt pack)",
        "## Caption Draft",
        "## Production Checklist",
        "Generate 4 image options",
    ):
        assert needle in md


def test_charged_handoff_with_secondary_includes_pairing_and_carousel_sections() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_handoff.generate_catstyle_daily_pack",
        return_value=_fake_pack_charged_with_secondary(),
    ):
        h = build_catstyle_daily_handoff(date(2026, 5, 2), editorial_profile="charged")
    assert h.secondary_supportive_candidate is not None
    md = render_catstyle_daily_handoff_markdown(h)
    for needle in (
        "## Main Charged Aspect",
        "## Supportive / Compensation Aspect",
        "## Why this pairing works",
        "## Suggested Carousel Structure",
        "**Cover:**",
        "**Slide 4:**",
        "**Final:**",
        "Saturn",
        "Venus",
        "Jupiter",
        "Mars",
    ):
        assert needle in md


def test_supportive_handoff_uses_selected_aspect_not_main_charged() -> None:
    sel = {
        "planet_a": "Saturn",
        "planet_b": "Venus",
        "aspect_type": "sextile",
        "mode_recommendation": "compensation",
        "total_score": 46,
        "orb": 0.24,
        "source": "deep",
        "recommended_scene_angle": "studio beat",
        "editorial_profile": "supportive",
        "editorial_bonus": 6,
        "editorial_selection_score": 52,
    }
    pack = CatstyleDailyPackResult(
        date="2026-05-02",
        scan_mode="day-window",
        step_hours=2,
        editorial_profile="supportive",
        ranked_candidates_count=1,
        selected_count=1,
        ranked_candidates=[dict(sel)],
        selected_candidates=[sel],
        primary_candidate=sel,
        secondary_supportive_candidate=None,
        prompt_packs=[
            {
                "image_prompts": ["a", "b", "c", "d"],
                "animation_prompt": "x",
                "negative_prompt": "y",
                "carousel_idea": "z",
            }
        ],
    )
    with patch(
        "astro_content_agent.services.content.catstyle_daily_handoff.generate_catstyle_daily_pack",
        return_value=pack,
    ):
        h = build_catstyle_daily_handoff(date(2026, 5, 2), editorial_profile="supportive")
    md = render_catstyle_daily_handoff_markdown(h)
    assert "## Selected Aspect" in md
    assert "## Main Charged Aspect" not in md


def test_json_dump_keys() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_handoff.generate_catstyle_daily_pack",
        return_value=_fake_pack_one(),
    ):
        h = build_catstyle_daily_handoff(date(2026, 5, 2))
    blob = h.model_dump(mode="json")
    assert blob["date"] == "2026-05-02"
    assert blob["editorial_profile"] == "charged"
    assert "items" in blob and len(blob["items"]) == 1
    assert "why_this_aspect_won" in blob["items"][0]
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
    assert "Editorial profile: **charged**" in md
