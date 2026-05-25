"""Catplanet body identity lock module and Sun/Uranus prompt integration."""
from __future__ import annotations

from astro_content_agent.content.catstyle.catplanet_body_identity_lock_v1 import (
    CATPLANET_BODY_IDENTITY_LOCK_BLOCK,
    CATPLANET_BODY_NEGATIVE_EXTRAS,
    CATPLANET_BODY_PRIORITY_BLOCK,
    CATPLANET_FLAGS_SECONDARY_BLOCK,
    SUN_CATPLANET_BODY_LOCK_BLOCK,
    URANUS_CATPLANET_BODY_LOCK_BLOCK,
    URANUS_REBEL_GENIUS_ACCESSORY_LOCK_BLOCK,
    catplanet_core_body_blocks,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _sun_uranus_req(*, render: str = "premium_comic_poster_v2") -> CatstylePromptRequest:
    return CatstylePromptRequest(
        planet_a="Sun",
        planet_b="Uranus",
        aspect_type="conjunction",
        mode="tension",
        variants_count=1,
        premium_art_direction=True,
        world_template_key="cosmic_zodiac_arena",
        render_style_profile_key=render,
        shot_mode="epic_arena_showdown",
        disable_approved_reference_prompt_lock=True,
    )


def test_catplanet_lock_module_catplanets_not_ordinary_cats() -> None:
    low = CATPLANET_BODY_IDENTITY_LOCK_BLOCK.lower()
    assert "v2" in low
    assert "cat-planets" in low or "cat-planet" in low
    assert "not ordinary" in low
    assert "costume-first" in low
    assert "planetary body material" in low
    assert "living planetary" in low


def test_catplanet_priority_and_flags_secondary() -> None:
    blob = catplanet_core_body_blocks().lower()
    assert "[catplanet body priority v1]" in blob
    assert "planetary body material" in blob
    assert "[catplanet flags secondary v1]" in blob
    assert "secondary" in blob
    assert CATPLANET_BODY_PRIORITY_BLOCK
    assert CATPLANET_FLAGS_SECONDARY_BLOCK


def test_catplanet_negative_extras() -> None:
    joined = ", ".join(CATPLANET_BODY_NEGATIVE_EXTRAS).lower()
    assert "ordinary cats with effects" in joined
    assert "ordinary furry cat" in joined
    assert "costume-first mascot" in joined
    assert "plush fur dominance" in joined
    assert "circular chest badge" in joined


def test_sun_catplanet_body_lock_solar_plasma_material() -> None:
    low = SUN_CATPLANET_BODY_LOCK_BLOCK.lower()
    assert "v3" in low
    assert "living solar" in low or "solar-core" in low
    assert "molten plasma" in low or "star-surface" in low
    assert "staff" in low
    assert "orange-gold" in low
    assert "corona" in low
    assert "not a normal orange" in low


def test_uranus_catplanet_body_lock_ice_gas_electric() -> None:
    low = URANUS_CATPLANET_BODY_LOCK_BLOCK.lower()
    assert "v5" in low
    assert "no leather jacket" in low
    assert "lightning rings" in low or "electric" in low and "rings" in low
    assert "stones" in low or "debris" in low
    assert "plush" in low or "toy-like" in low
    assert "rebel" in low or "disruptor" in low
    assert "bright cyan" in low
    assert "ice-gas" in low
    assert "gas bands" in low or "cloud layers" in low
    assert "normal blue fur" in low or "not normal blue" in low
    assert "mascot" in low and ("softness" in low or "cuddliness" in low or "plush" in low)


def test_global_catplanet_body_identity_lock_in_prompt() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts).lower()
    assert "[catplanet body identity lock v2]" in joined
    assert "[catplanet body priority v1]" in joined
    assert "[catplanet flags secondary v1]" in joined
    assert "[banner-only no chest badge v1]" in joined
    assert "not ordinary" in joined
    assert "planetary body material" in joined
    assert "molten plasma" in joined or "star-surface" in joined
    assert "ice-gas" in joined


def test_sun_uranus_prompt_rejects_ordinary_furry_mascot_language() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts).lower()
    neg = pack.negative_prompt.lower()
    assert "ordinary furry cat" in joined or "ordinary furry cat" in neg
    assert "costume-first" in joined or "costume-first" in neg
    assert "plush fur" in joined or "plush fur" in neg
    assert "circular chest badge" in joined or "circular chest badge" in neg


def test_sun_uranus_premium_cg_keyart_catplanet_material_priority() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req(render="premium_cg_keyart_v1"))
    joined = "\n".join(pack.image_prompts).lower()
    assert "premium cg key art" in joined
    assert "[uranus catplanet body lock v5]" in joined
    assert "[catstyle global quality lock cg v1]" in joined
    assert "planetary body material" in joined
    assert "not ordinary furry cats" in joined or "not ordinary furry" in joined
    assert "molten plasma" in joined or "star-surface" in joined
    assert "ice-gas" in joined
    assert "zodiac floor" in joined or "zodiac wheel" in joined
    assert "coliseum" in joined
    assert "starfield" in joined or "nebula" in joined
    assert "earth disk" in joined or "earth above" in joined


def test_sun_uranus_prompt_includes_body_and_flag_locks() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts)
    low = joined.lower()
    assert "[catplanet body identity lock v2]" in low
    assert "[sun catplanet body lock v3]" in low
    assert "[uranus catplanet body lock v5]" in low
    assert "[uranus reference spectacle v2]" in low
    assert "[sun-uranus hard art-direction override v3" in low
    assert "reject leather jacket" in low or "no leather jacket" in low
    assert "[uranus rebel genius accessory lock v7" in low
    assert "[uranus inventor genius v4]" in low
    assert "lightning rings" in low or ("electric" in low and "rings" in low)
    assert "tesla" in low
    assert "[uranus hard-edged attitude v2]" in low
    assert "bright cyan" in low
    assert "collectible" in low
    assert "accessory richness" in low or "hardware silhouette" in low
    assert "hoop earring" in low
    assert "attached to the ear" in low or "physically attached" in low
    assert "accessory glyph ban" in low
    assert "two" in low and ("cuff" in low or "bracelet" in low)
    assert "[flag glyph fidelity lock v1]" in low
    assert "[sun-uranus flag glyph fidelity v2]" in low
    assert "[zodiac arena floor lock v1]" in low


def test_negative_prompt_body_and_glyph_extras_compact_deduped() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    neg = pack.negative_prompt
    assert len(neg) <= 1200
    parts = [p.strip() for p in neg.split(",") if p.strip()]
    norm = [" ".join(p.lower().split()) for p in parts]
    assert len(parts) == len(set(norm)), "exact duplicate negative chunks"
    low = neg.lower()
    assert "ordinary cats with effects" in low
    assert "costume-first mascot" in low or "plush fur" in low
    assert "incomplete flag glyphs" in low
    assert "random magic circle" in low
