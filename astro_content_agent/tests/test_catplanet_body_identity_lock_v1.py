"""Catplanet body identity and Sun/Uranus flag-glyph precision locks."""
from __future__ import annotations

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


def test_global_catplanet_body_identity_lock_in_prompt() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts).lower()
    assert "[catplanet body identity lock v1]" in joined
    assert "anthropomorphic planet-cats" in joined or "catplanets" in joined
    assert "planetary texture" in joined or "planetary texture/material" in joined
    assert "elemental glow" in joined or "elemental effects" in joined


def test_sun_catplanet_body_lock_plasma_corona() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts).lower()
    assert "[sun catplanet body lock v1]" in joined
    assert "living solar core" in joined or "solar core" in joined
    assert "plasma" in joined
    assert "corona" in joined


def test_uranus_catplanet_body_lock_ice_gas_tilt_ring() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts).lower()
    assert "[uranus catplanet body lock v1]" in joined
    assert "ice-gas" in joined
    assert "tilted-axis" in joined or "tilted axis" in joined
    assert "ring" in joined or "magnetic-field" in joined or "magnetic field" in joined


def test_flag_glyph_precision_lock_sun_uranus() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts)
    assert "[FLAG GLYPH PRECISION LOCK v1]" in joined
    assert "\u2609" in joined
    assert "\u2645" in joined
    low = joined.lower()
    assert "central dot" in low
    assert "vertical stem" in low
    assert "side arcs" in low
    assert "lower circle" in low


def test_approved_reference_lock_preserves_body_identity_and_depth() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts).lower()
    assert "[approved catstyle reference lock v1]" in joined
    assert "planet-body identity" in joined or "catplanet body identity" in joined
    assert "premium depth" in joined or "reference-level premium depth" in joined
    assert "ordinary cats with effects" in joined or "not ordinary cats with effects" in joined


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
    assert "fake uranus glyph" in low
    assert "partial sun glyph" in low
    assert "plush toy body" in low
    assert "weak planet texture" in low
