"""Reusable premium cosmic zodiac arena environment baseline."""
from __future__ import annotations

from astro_content_agent.content.catstyle.cosmic_zodiac_arena_premium_environment_v1 import (
    COSMIC_ZODIAC_ARENA_PREMIUM_COLISEUM_BLOCK,
    COSMIC_ZODIAC_ARENA_PREMIUM_ENVIRONMENT_LOCK_BLOCK,
    COSMIC_ZODIAC_ARENA_PREMIUM_ENVIRONMENT_NEGATIVE_EXTRAS,
    COSMIC_ZODIAC_ARENA_PREMIUM_SKY_BLOCK,
    COSMIC_ZODIAC_ARENA_PREMIUM_SPECTACLE_BLOCK,
    applies_cosmic_zodiac_arena_premium_environment,
    cosmic_zodiac_arena_premium_environment_blocks,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_premium_environment_blocks_brighter_coliseum_and_rich_sky() -> None:
    blob = cosmic_zodiac_arena_premium_environment_blocks().lower()
    assert "[cosmic zodiac arena premium environment v1]" in blob
    assert "[cosmic zodiac arena premium coliseum v1]" in blob
    assert "[cosmic zodiac arena premium sky v1]" in blob
    assert "[cosmic zodiac arena premium spectacle v1]" in blob
    assert "illuminated arches" in blob
    assert "readable tiers" in blob or "tier" in blob
    assert "asymmetry" in blob
    assert "semicircle" in blob
    assert "colorful milky way" in blob or "galaxy band" in blob
    assert "many visible stars" in blob or "rich starfield" in blob
    assert "nebula" in blob
    assert "cinematic" in blob or "high-contrast" in blob
    assert "electric rings" in blob or "orbit halo" in blob


def test_applies_helper_cosmic_arena_premium_cg_and_epic_showdown() -> None:
    assert applies_cosmic_zodiac_arena_premium_environment(
        world_template_key="cosmic_zodiac_arena",
        render_style_profile_key="premium_cg_keyart_v1",
    )
    assert applies_cosmic_zodiac_arena_premium_environment(
        world_template_key="cosmic_zodiac_arena",
        premium_art_direction=True,
    )
    assert not applies_cosmic_zodiac_arena_premium_environment(
        world_template_key="cosmic_zodiac_arena",
        render_style_profile_key="premium_comic_poster_v2",
        premium_art_direction=False,
        shot_mode="epic_arena_showdown",
    )


def test_environment_negative_extras_reject_dark_wall_and_weak_sky() -> None:
    joined = ", ".join(COSMIC_ZODIAC_ARENA_PREMIUM_ENVIRONMENT_NEGATIVE_EXTRAS).lower()
    assert "dark flat semicircle" in joined
    assert "empty sky" in joined
    assert "weak sparse starfield" in joined


def test_mars_pluto_pack_includes_premium_environment_baseline() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Pluto",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_cg_keyart_v1",
            shot_mode="epic_arena_showdown",
            disable_approved_reference_prompt_lock=True,
        )
    )
    low = "\n".join(pack.image_prompts).lower()
    assert "[cosmic zodiac arena premium environment v1]" in low
    assert "[cosmic zodiac arena premium coliseum v1]" in low
    assert "[cosmic zodiac arena premium sky v1]" in low
    assert "colorful milky way" in low or "galaxy band" in low
    assert "illuminated arches" in low
    assert len(pack.negative_prompt) <= 1200
