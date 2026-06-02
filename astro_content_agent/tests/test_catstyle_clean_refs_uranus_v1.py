"""Clean refs Uranus feature hardlock (Mars square Uranus identity fidelity)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
    CLEAN_PROMPT_MAX_CHARS,
    build_clean_refs_image_prompt,
    generate_catstyle_clean_refs_prompt_pack,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest


def test_mars_uranus_clean_prompt_uranus_feature_hardlock_under_budget() -> None:
    prompt = build_clean_refs_image_prompt("Mars", "Uranus", "square", "tension")
    low = prompt.lower()
    assert "[uranus reference hardlock v2]" in low
    assert "levitating" in low or "anti-gravity" in low
    assert "orbital electric ring" in low
    assert "floating debris" in low
    assert "match approved mars reference" in low
    assert "collapse to generic blue cat" in low
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
    assert "catstyle planet reference identity hardlock" not in low
    assert "tense aspect choreography" not in low

    pack = generate_catstyle_clean_refs_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Uranus",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            clean_refs_mode=True,
            use_planet_reference_auto=False,
        )
    )
    neg = pack.negative_prompt.lower()
    assert "normal blue cat uranus" in neg
    assert "no orbital rings" in neg
    assert len(pack.image_prompts[0]) <= CLEAN_PROMPT_MAX_CHARS


def test_uranus_feature_block_absent_without_uranus_in_pair() -> None:
    prompt = build_clean_refs_image_prompt("Mars", "Jupiter", "square", "tension")
    assert "[uranus reference hardlock v2]" not in prompt.lower()
