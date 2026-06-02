"""Tests for universal tense-aspect choreography (square / opposition)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.catstyle_tense_aspect_choreography_v1 import (
    build_tense_aspect_choreography_layer,
    is_tense_hard_aspect,
)


def test_is_tense_hard_aspect_square_tension() -> None:
    assert is_tense_hard_aspect("square", "tension")
    assert is_tense_hard_aspect("opposition", "tension")
    assert not is_tense_hard_aspect("square", "flow")
    assert not is_tense_hard_aspect("trine", "tension")


def test_build_tense_layer_includes_arena_balance() -> None:
    layer = build_tense_aspect_choreography_layer(
        "square", "tension", "Jupiter", "Saturn"
    )
    low = layer.lower()
    assert "[square conflict law v1]" in low
    assert "[tense aspect battle-arena balance v1]" in low
    assert "large monumental arena" in low or "do not crop away arena scale" in low
