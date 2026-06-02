"""Reference material fidelity tests (clean refs mode, all planets)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
    CLEAN_PROMPT_MAX_CHARS,
    build_clean_refs_image_prompt,
    generate_catstyle_clean_refs_prompt_pack,
)
from astro_content_agent.content.catstyle.catstyle_reference_material_fidelity_v1 import (
    REFERENCE_MATERIAL_FIDELITY_BLOCK,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest


def _assert_global_material_fidelity(prompt: str) -> None:
    low = prompt.lower()
    assert "[reference material fidelity v1]" in low
    assert "approved planet references define not only identity, but also render quality" in low
    assert REFERENCE_MATERIAL_FIDELITY_BLOCK in prompt
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
    assert "catstyle visual composition hardlock" not in low


def _assert_material_negatives(pack_neg: str) -> None:
    neg = pack_neg.lower()
    assert "lost reference material quality" in neg
    assert "flat painted fur" in neg
    assert "low material separation" in neg


def test_venus_saturn_clean_refs_reference_material_fidelity() -> None:
    prompt = build_clean_refs_image_prompt("Venus", "Saturn", "square", "tension")
    _assert_global_material_fidelity(prompt)
    low = prompt.lower()
    assert "[venus material fidelity]" in low
    assert "[saturn material fidelity]" in low
    assert "pearl-pink/rose-gold" in low
    assert "translucent flowing ribbons" in low
    assert "glossy gems" in low
    assert "black-and-gold heavy layered robes" in low
    assert "metallic chains" in low
    assert "ringed saturn hat" in low

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
    _assert_material_negatives(pack.negative_prompt)


def test_mars_uranus_clean_refs_reference_material_fidelity() -> None:
    prompt = build_clean_refs_image_prompt("Mars", "Uranus", "square", "tension")
    _assert_global_material_fidelity(prompt)
    low = prompt.lower()
    assert "[mars material fidelity]" in low
    assert "[uranus material fidelity]" in low
    assert "red/orange martial body" in low
    assert "cyan/turquoise electric fur" in low
    assert "orbital plasma rings" in low


def test_mercury_neptune_clean_refs_reference_material_fidelity() -> None:
    prompt = build_clean_refs_image_prompt("Mercury", "Neptune", "square", "tension")
    _assert_global_material_fidelity(prompt)
    low = prompt.lower()
    assert "[mercury material fidelity]" in low
    assert "[neptune material fidelity]" in low
    assert "silver/blue messenger body" in low
    assert "oceanic blue/cyan/silver" in low
    assert "trident identity" in low


def test_material_fidelity_only_for_active_planets() -> None:
    prompt = build_clean_refs_image_prompt("Mars", "Jupiter", "square", "tension")
    low = prompt.lower()
    assert "[reference material fidelity v1]" in low
    assert "[mars material fidelity]" in low
    assert "[jupiter material fidelity]" in low
    assert "[venus material fidelity]" not in low
    assert "[saturn material fidelity]" not in low
    assert "[uranus material fidelity]" not in low
