"""Flag glyph fidelity lock module and Sun/Uranus prompt integration."""
from __future__ import annotations

from astro_content_agent.content.catstyle.flag_glyph_fidelity_lock_v1 import (
    FLAG_GLYPH_FIDELITY_LOCK_BLOCK,
    FLAG_GLYPH_FIDELITY_NEGATIVE_EXTRAS,
    SUN_URANUS_FLAG_GLYPH_FIDELITY_BLOCK,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_flag_glyph_fidelity_block_canonical_cloth_language() -> None:
    assert "[FLAG GLYPH FIDELITY LOCK v1]" in FLAG_GLYPH_FIDELITY_LOCK_BLOCK
    low = FLAG_GLYPH_FIDELITY_LOCK_BLOCK.lower()
    assert "canonical" in low
    assert "painted" in low or "woven" in low
    assert "partial" in low
    assert "fake runes" in low or "fake rune" in low
    assert "cropped" in low
    assert "sticker" in low


def test_flag_glyph_negative_extras() -> None:
    joined = ", ".join(FLAG_GLYPH_FIDELITY_NEGATIVE_EXTRAS).lower()
    assert "incomplete flag glyphs" in joined
    assert "fake uranus glyph" in joined
    assert "partial sun glyph" in joined
    assert "hollow sun ring" in joined
    assert "random rune" in joined
    assert "cropped banner glyphs" in joined


def test_sun_uranus_flag_block_glyphs_and_banner_sides() -> None:
    assert "\u2609" in SUN_URANUS_FLAG_GLYPH_FIDELITY_BLOCK
    assert "\u2645" in SUN_URANUS_FLAG_GLYPH_FIDELITY_BLOCK
    low = SUN_URANUS_FLAG_GLYPH_FIDELITY_BLOCK.lower()
    assert "left sun banner" in low
    assert "right uranus banner" in low
    assert "filled central dot" in low
    assert "hollow ring" in low
    assert "vertical stem" in low
    assert "side arcs" in low
    assert "lower circle" in low
    assert "random rune" in low


def test_sun_uranus_prompt_includes_flag_glyph_fidelity_locks() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_comic_poster_v2",
            shot_mode="epic_arena_showdown",
        )
    )
    joined = "\n".join(pack.image_prompts)
    assert "[FLAG GLYPH FIDELITY LOCK v1]" in joined
    assert "[SUN-URANUS FLAG GLYPH FIDELITY v2]" in joined
    assert "\u2609" in joined and "\u2645" in joined
    neg = pack.negative_prompt.lower()
    assert "incomplete flag glyphs" in neg
    assert "cropped banner glyphs" in neg
