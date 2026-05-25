"""Sun/Uranus visual refinement locks — prompt and approved-reference decoupling."""
from __future__ import annotations

from astro_content_agent.content.catstyle.approved_reference_prompt_lock_v1 import (
    build_approved_reference_prompt_lock_text,
)
from astro_content_agent.content.catstyle.approved_reference_registry import (
    ResolvedApprovedReference,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.content.catstyle.sun_uranus_visual_refinement_v1 import (
    BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK,
    COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK,
    SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK,
    sun_uranus_visual_refinement_blocks,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _sun_uranus_pack(*, disable_approved: bool = False) -> str:
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
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=disable_approved,
        )
    )
    return "\n".join(pack.image_prompts)


def test_refinement_module_blocks_present() -> None:
    blob = sun_uranus_visual_refinement_blocks()
    assert BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK in blob
    assert SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK in blob
    assert COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK in blob
    assert "body emblems" in blob.lower()
    assert "starfield" in blob.lower()
    assert "nebula" in blob.lower()
    assert "stadium tiers" in blob.lower() or "arches" in blob.lower()


def test_sun_uranus_assembled_prompt_refinement_locks() -> None:
    low = _sun_uranus_pack().lower()
    assert "[banner-only approved reference decoupling v1]" in low
    assert "[body glyph rejection v1]" in low
    assert "[sun banner glyph hardening v1]" in low
    assert "[cosmic environment power lock v1]" in low
    assert "central dot" in low
    assert "phone" in low or "instagram" in low
    assert "starfield" in low
    assert "nebula" in low
    assert "monumental" in low and "coliseum" in low
    assert "earth disk" in low or "earth above" in low
    assert "zodiac floor" in low or "zodiac wheel" in low
    assert "torso" in low or "chest" in low
    assert "collar" in low
    assert "uranus" in low and ("off-banner" in low or "banner cloth only" in low or "right/starboard" in low)
    assert "glyph on torso" in low or "zero" in low and "glyph" in low


def test_sun_uranus_prompt_forbids_body_glyph_attractors() -> None:
    low = _sun_uranus_pack().lower()
    assert "glyph on torso" in low or "zero" in low and "planetary glyphs on torso" in low
    assert "chest symbols" in low or "chest" in low and "collar symbols" in low
    assert "medallion-like" in low or "medallion" not in low


def test_approved_reference_lock_includes_decoupling_for_sun_uranus() -> None:
    hit = ResolvedApprovedReference(
        registry_key="sun_uranus_conjunction_tension",
        image_path="references/approved/sun_uranus.png",
        label="Sun/Uranus conjunction tension",
        notes="test",
        priority=100,
    )
    lock = build_approved_reference_prompt_lock_text(
        hit, "Sun", "Uranus", "conjunction", "tension"
    )
    assert BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK in lock
    assert "do not" in lock.lower() and "body emblems" in lock.lower()


def test_sun_uranus_with_approved_lock_still_has_refinement() -> None:
    low = _sun_uranus_pack(disable_approved=False).lower()
    assert "[banner-only approved reference decoupling v1]" in low
    assert "layered starfield" in low or "starfield" in low
