"""Clean refs reference-fidelity hardlocks (planet, arena, banners, zodiac floor)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.arena_pool_registry_v1 import DEFAULT_ARENA_POOL_KEY
from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
    CLEAN_PROMPT_MAX_CHARS,
    build_clean_refs_image_prompt,
    generate_catstyle_clean_refs_prompt_pack,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest


def test_clean_refs_reference_fidelity_hardlocks_mars_uranus_with_arena_pool() -> None:
    prompt = build_clean_refs_image_prompt(
        "Mars",
        "Uranus",
        "square",
        "tension",
        arena_environment_reference_attached=True,
        arena_pool_key=DEFAULT_ARENA_POOL_KEY,
    )
    low = prompt.lower()
    assert "[reference fidelity priority v1]" in low
    assert "planet a identity" in low or "planet a ref" in low
    assert "[uranus reference hardlock v2]" in low
    assert "orbital electric ring" in low
    assert "anti-gravity" in low or "levitation" in low
    assert "floating debris" in low
    assert "[arena opulence hardlock v1]" in low
    assert "[arena lighting richness v1]" in low
    assert "[arena scale dominance v3]" in low
    assert "golden" in low or "amber" in low
    assert "warm golden torchlight" in low
    assert "without crushing blacks" in low
    assert "[banners safety lock v1]" in low
    assert "blank" in low or "placeholder" in low
    assert "deep-blue" in low or "empty" in low
    assert "[zodiac floor hardlock v2]" in low
    assert "only real zodiac glyphs" in low or "real zodiac glyphs" in low
    assert "not a neat medallion" in low or "neat medallion" in low
    assert "[planet size / presence balance v1]" not in low
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
    assert "catstyle visual composition hardlock" not in low

    pack = generate_catstyle_clean_refs_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Uranus",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            clean_refs_mode=True,
            arena_environment_reference_attached=True,
            arena_pool_key=DEFAULT_ARENA_POOL_KEY,
        )
    )
    neg = pack.negative_prompt.lower()
    assert "generic blue cat" in neg
    assert "neptune-like water mage uranus" in neg
    assert "fake planetary glyphs on banners" in neg
    assert "fake zodiac symbols" in neg
    assert "tiny complete medallion floor" in neg
    assert "dark muddy arena" in neg


def test_clean_refs_text_only_arena_has_fidelity_without_arena_hardlock() -> None:
    prompt = build_clean_refs_image_prompt("Mars", "Uranus", "square", "tension")
    low = prompt.lower()
    assert "[reference fidelity priority v1]" in low
    assert "[uranus reference hardlock v2]" in low
    assert "[arena reference hardlock v2]" not in low
    assert "[banners safety lock v1]" not in low
    assert "[arena opulence hardlock v1]" in low
    assert "[zodiac floor hardlock v2]" in low
