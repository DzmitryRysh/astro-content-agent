"""Catplanet body identity lock module and Sun/Uranus prompt integration."""
from __future__ import annotations

from astro_content_agent.content.catstyle.catplanet_body_identity_lock_v1 import (
    CATPLANET_BODY_IDENTITY_LOCK_BLOCK,
    CATPLANET_BODY_NEGATIVE_EXTRAS,
    SUN_CATPLANET_BODY_LOCK_BLOCK,
    URANUS_CATPLANET_BODY_LOCK_BLOCK,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _sun_uranus_req() -> CatstylePromptRequest:
    return CatstylePromptRequest(
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


def test_catplanet_lock_module_catplanets_not_ordinary_cats() -> None:
    low = CATPLANET_BODY_IDENTITY_LOCK_BLOCK.lower()
    assert "cat-planets" in low or "cat-planet" in low
    assert "not ordinary cats" in low
    assert "body material" in low
    assert "surface texture" in low
    assert "living planetary" in low
    assert "mascot simplification" in low


def test_catplanet_negative_extras() -> None:
    joined = ", ".join(CATPLANET_BODY_NEGATIVE_EXTRAS).lower()
    assert "ordinary cats with effects" in joined
    assert "generic elemental cats" in joined
    assert "weak planet texture" in joined
    assert "plush toy body" in joined
    assert "mascot redraw" in joined


def test_sun_catplanet_body_lock_solar_plasma_leo() -> None:
    low = SUN_CATPLANET_BODY_LOCK_BLOCK.lower()
    assert "living solar cat-planet" in low
    assert "orange-gold" in low
    assert "plasma" in low
    assert "corona" in low
    assert "leo" in low


def test_uranus_catplanet_body_lock_ice_gas_electric() -> None:
    low = URANUS_CATPLANET_BODY_LOCK_BLOCK.lower()
    assert "ice-gas" in low
    assert "cyan" in low
    assert "tilted-axis" in low or "tilted axis" in low
    assert "magnetic-field" in low or "magnetic field" in low
    assert "floating rocks" in low or "orbital debris" in low
    assert "striped tiger" in low


def test_global_catplanet_body_identity_lock_in_prompt() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts).lower()
    assert "[catplanet body identity lock v1]" in joined
    assert "cat-planets" in joined or "cat-planet" in joined
    assert "not ordinary cats" in joined
    assert "surface texture" in joined


def test_sun_uranus_prompt_includes_all_three_visual_locks() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts)
    low = joined.lower()
    assert "[catplanet body identity lock v1]" in low
    assert "[sun catplanet body lock v1]" in low
    assert "[uranus catplanet body lock v1]" in low
    assert "[flag glyph fidelity lock v1]" in low
    assert "[sun-uranus flag glyph fidelity v1]" in low
    assert "[zodiac arena floor lock v1]" in low
    assert pack.image_prompts[0].lower().startswith("premium cinematic comic-poster illustration")


def test_negative_prompt_body_and_glyph_extras_compact_deduped() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    neg = pack.negative_prompt
    assert len(neg) <= 1200
    parts = [p.strip() for p in neg.split(",") if p.strip()]
    norm = [" ".join(p.lower().split()) for p in parts]
    assert len(parts) == len(set(norm)), "exact duplicate negative chunks"
    low = neg.lower()
    assert "ordinary cats with effects" in low
    assert "generic elemental cats" in low
    assert "incomplete flag glyphs" in low
    assert "random magic circle" in low
    assert "mascot redraw" in low


def test_approved_reference_lock_preserves_body_identity_and_depth() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts).lower()
    assert "[approved catstyle reference lock v1]" in joined
    assert "visual dna" in joined or "strict visual dna" in joined
    assert "arena depth" in joined or "coliseum depth" in joined
    assert "sibling image from the same campaign" in joined
