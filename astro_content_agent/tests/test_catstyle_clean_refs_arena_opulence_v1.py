"""Clean-refs arena opulence hardlock tests."""
from __future__ import annotations

from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
    CLEAN_PROMPT_MAX_CHARS,
    build_clean_refs_image_prompt,
    generate_catstyle_clean_refs_prompt_pack,
)
from astro_content_agent.content.catstyle.catstyle_clean_refs_arena_opulence_lock_v1 import (
    ARENA_LIGHTING_RICHNESS_BLOCK,
    ARENA_OPULENCE_HARDLOCK_BLOCK,
    ARENA_OPULENCE_HARDLOCK_MARKER,
    ARENA_PRIORITY_SAFETY_BLOCK,
    ARENA_SCALE_DOMINANCE_BLOCK,
    CLEAN_REFS_ARENA_OPULENCE_NEGATIVE_EXTRAS,
)
from astro_content_agent.content.catstyle.catstyle_reference_material_fidelity_v1 import (
    REFERENCE_MATERIAL_FIDELITY_MARKER,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest


def test_clean_refs_arena_opulence_hardlocks_venus_saturn() -> None:
    prompt = build_clean_refs_image_prompt("Venus", "Saturn", "square", "tension")
    low = prompt.lower()
    assert ARENA_OPULENCE_HARDLOCK_BLOCK in prompt
    assert ARENA_LIGHTING_RICHNESS_BLOCK in prompt
    assert ARENA_SCALE_DOMINANCE_BLOCK in prompt
    assert "[arena opulence hardlock v1]" in low
    assert "[arena lighting richness v1]" in low
    assert "[arena scale dominance v3]" in low
    assert "golden/amber" in low
    assert "warm golden torchlight" in low
    assert "monumental" in low or "epic coliseum" in low
    assert ARENA_PRIORITY_SAFETY_BLOCK in prompt
    assert "arena opulence is background support only" in low
    assert prompt.index(REFERENCE_MATERIAL_FIDELITY_MARKER) < prompt.index(ARENA_OPULENCE_HARDLOCK_MARKER)
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
    assert "catstyle visual composition hardlock" not in low

    pack = generate_catstyle_clean_refs_prompt_pack(
        CatstylePromptRequest(
            planet_a="Venus",
            planet_b="Saturn",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            clean_refs_mode=True,
        )
    )
    neg = pack.negative_prompt.lower()
    for phrase in CLEAN_REFS_ARENA_OPULENCE_NEGATIVE_EXTRAS:
        assert phrase in neg
    assert "plain empty hall" in neg
    assert "no golden richness" in neg


def test_clean_refs_arena_opulence_mars_uranus_and_mercury_neptune() -> None:
    for pa, pb in (("Mars", "Uranus"), ("Mercury", "Neptune")):
        prompt = build_clean_refs_image_prompt(pa, pb, "square", "tension")
        low = prompt.lower()
        assert "[arena opulence hardlock v1]" in low
        assert "[arena lighting richness v1]" in low
        assert "[arena scale dominance v3]" in low
        assert "[arena priority safety v1]" in low
        assert "arena opulence is background support only" in low
        assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
