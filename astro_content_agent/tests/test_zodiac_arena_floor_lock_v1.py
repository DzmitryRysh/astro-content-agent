"""Zodiac arena floor lock module and prompt integration."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.content.catstyle.zodiac_arena_floor_lock_v1 import (
    ZODIAC_ARENA_FLOOR_LOCK_BLOCK,
    ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_zodiac_floor_block_wheel_and_stone_language() -> None:
    assert "[ZODIAC ARENA FLOOR LOCK v1]" in ZODIAC_ARENA_FLOOR_LOCK_BLOCK
    low = ZODIAC_ARENA_FLOOR_LOCK_BLOCK.lower()
    assert "large readable zodiac wheel" in low
    assert "engraved" in low or "inlaid" in low
    assert "stone brick" in low
    assert "canonical zodiac glyphs" in low
    assert "sector divisions" in low
    assert "medallion" in low or "compass" in low
    assert "random magic circle" in low


def test_zodiac_floor_negative_extras() -> None:
    joined = ", ".join(ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS).lower()
    assert "random magic circle" in joined
    assert "fake zodiac symbols" in joined
    assert "tiny decorative floor emblem" in joined
    assert "incomplete zodiac wheel" in joined
    assert "vague occult floor markings" in joined


def test_mars_neptune_prompt_includes_zodiac_floor_lock() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Neptune",
            aspect_type="square",
            mode="tension",
            variants_count=1,
        )
    )
    joined = "\n".join(pack.image_prompts).lower()
    assert "[zodiac arena floor lock v1]" in joined
    assert "large readable zodiac wheel" in joined
    neg = pack.negative_prompt.lower()
    assert "random magic circle" in neg
    assert "fake zodiac symbols" in neg
