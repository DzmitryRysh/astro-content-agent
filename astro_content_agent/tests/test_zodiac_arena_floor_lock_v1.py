"""Zodiac arena floor lock module and prompt integration."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.content.catstyle.zodiac_arena_floor_lock_v1 import (
    ZODIAC_ARENA_FLOOR_LOCK_BLOCK,
    ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS,
    ZODIAC_FLOOR_SCALE_FRAMING_BLOCK,
    ZODIAC_FLOOR_SCALE_NEGATIVE_EXTRAS,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_zodiac_floor_block_wheel_and_stone_language() -> None:
    assert "[ZODIAC ARENA FLOOR LOCK v1]" in ZODIAC_ARENA_FLOOR_LOCK_BLOCK
    low = ZODIAC_ARENA_FLOOR_LOCK_BLOCK.lower()
    assert "only real zodiac glyphs" in low
    assert "correct astrological order" in low
    assert "no fake runes" in low
    assert "engraved" in low or "inlaid" in low
    assert "stone brick" in low
    assert "twelve" in low or "aries through pisces" in low
    assert "compass hub" in low or "compass" in low
    assert "magic circle" in low


def test_zodiac_floor_negative_extras() -> None:
    joined = ", ".join(ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS).lower()
    assert "random magic circle" in joined
    assert "fake runes instead of zodiac glyphs" in joined
    assert "wrong zodiac sign order" in joined
    assert "fake zodiac symbols" in joined
    assert "vague occult floor markings" in joined


def test_zodiac_floor_scale_framing_allows_partial_circle() -> None:
    low = ZODIAC_FLOOR_SCALE_FRAMING_BLOCK.lower()
    assert "[zodiac floor scale / framing v1]" in low
    assert "monumental" in low
    assert "35–65%" in low
    assert "extend beyond" in low or "extending beyond" in low
    assert "entire circle neatly" in low or "entire circle neatly centered" in low
    joined = ", ".join(ZODIAC_FLOOR_SCALE_NEGATIVE_EXTRAS).lower()
    assert "tiny complete zodiac disc" in joined
    assert "entire zodiac wheel fitted neatly in frame" in joined
    assert "miniature zodiac platform" in joined


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
    assert "[zodiac floor scale / framing v1]" in joined
    assert "only real zodiac glyphs" in joined
    neg = pack.negative_prompt.lower()
    assert "random magic circle" in neg
    assert "fake zodiac symbols" in neg
