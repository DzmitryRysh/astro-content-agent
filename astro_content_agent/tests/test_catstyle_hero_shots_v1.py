"""Tests for deterministic hero shot roles v1."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.hero_shots_v1 import (
    format_hero_shot_prompt_block,
    shot_roles_for_variant_indices,
)


def test_shot_roles_hero_pair_alternates() -> None:
    assert shot_roles_for_variant_indices(2, "hero_pair") == ["hero_poster", "alternate_action_angle"]
    assert shot_roles_for_variant_indices(4, "hero_pair") == [
        "hero_poster",
        "alternate_action_angle",
        "hero_poster",
        "alternate_action_angle",
    ]


def test_shot_roles_standard_all_none() -> None:
    assert shot_roles_for_variant_indices(3, "standard") == [None, None, None]


def test_shot_roles_epic_arena_showdown_alternates_like_hero_pair() -> None:
    assert shot_roles_for_variant_indices(3, "epic_arena_showdown") == [
        "hero_poster",
        "alternate_action_angle",
        "hero_poster",
    ]


def test_unknown_shot_mode_raises() -> None:
    with pytest.raises(ValueError, match="Unknown shot_mode"):
        shot_roles_for_variant_indices(2, "bogus")


def test_format_blocks_distinct() -> None:
    a = format_hero_shot_prompt_block("hero_poster").lower()
    b = format_hero_shot_prompt_block("alternate_action_angle").lower()
    assert "hero_poster:" in a and "alternate_action_angle:" not in a
    assert "alternate_action_angle:" in b and ("diagonal" in b or "tilt" in b)


def test_format_flow_mode_alternate_avoids_sidewinder_tension_phrase() -> None:
    classic = format_hero_shot_prompt_block("alternate_action_angle", flow_mode=False).lower()
    flow = format_hero_shot_prompt_block("alternate_action_angle", flow_mode=True).lower()
    assert "sidewinder tension" in classic
    assert "sidewinder tension" not in flow
    assert "shared objective" in flow or "co-facing" in flow


def test_format_none_empty() -> None:
    assert format_hero_shot_prompt_block(None) == ""
