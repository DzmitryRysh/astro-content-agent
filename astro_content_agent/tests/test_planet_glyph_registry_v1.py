"""Tests for canonical Catstyle planetary glyph registry and pair-flag prompt block."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.content.catstyle.planet_glyph_registry_v1 import (
    CANONICAL_PLANET_GLYPHS,
    SUPPORTED_PLANET_GLYPH_KEYS,
    canonical_glyph_char,
    format_pair_flag_glyph_system_block,
    glyph_prompt_label,
    planet_glyph_key,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_registry_contains_all_ten_planets_with_expected_unicode() -> None:
    assert SUPPORTED_PLANET_GLYPH_KEYS == frozenset(
        "sun moon mercury venus mars jupiter saturn uranus neptune pluto".split()
    )
    assert CANONICAL_PLANET_GLYPHS["sun"] == "\u2609"
    assert CANONICAL_PLANET_GLYPHS["moon"] == "\u263d"
    assert CANONICAL_PLANET_GLYPHS["mercury"] == "\u263f"
    assert CANONICAL_PLANET_GLYPHS["venus"] == "\u2640"
    assert CANONICAL_PLANET_GLYPHS["mars"] == "\u2642"
    assert CANONICAL_PLANET_GLYPHS["jupiter"] == "\u2643"
    assert CANONICAL_PLANET_GLYPHS["saturn"] == "\u2644"
    assert CANONICAL_PLANET_GLYPHS["uranus"] == "\u2645"
    assert CANONICAL_PLANET_GLYPHS["neptune"] == "\u2646"
    assert CANONICAL_PLANET_GLYPHS["pluto"] == "\u2647"


def test_planet_glyph_key_normalizes() -> None:
    assert planet_glyph_key("  JUPITER ") == "jupiter"


def test_glyph_prompt_label_shape() -> None:
    assert glyph_prompt_label("Venus") == "Venus (\u2640)"


def test_pair_block_left_right_labels_arbitrary_pair() -> None:
    txt = format_pair_flag_glyph_system_block("Mars", "Venus")
    lower = txt.lower()
    assert "left/port faction banner" in lower
    assert "right/starboard faction banner" in lower
    assert "mars (\u2642)" in lower or "mars (♂)" in txt.lower()
    assert "venus (\u2640)" in lower or "venus (♀)" in txt.lower()
    assert "heraldic gold" in lower
    assert "instagram" in lower or "mobile" in lower


def test_jupiter_saturn_pair_includes_both_hardening_blocks() -> None:
    txt = format_pair_flag_glyph_system_block("Saturn", "Jupiter")
    assert "[jupiter ♃ hardening]" in txt.lower()
    assert "[saturn ♄ hardening]" in txt.lower()


@pytest.mark.parametrize("mode", ["flow", "tension"])
def test_prompt_injects_pair_flag_glyph_system_for_any_pair(mode: str) -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Neptune",
            aspect_type="trine",
            mode=mode,
            premium_art_direction=True,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "catstyle pair flag glyph system v1" in blob
    assert "left/port faction banner" in blob
    assert "sun (\u2609)" in blob or "sun (☉)" in " ".join(pack.image_prompts).lower()
    assert "neptune" in blob
    assert "symbol overlay v1" not in blob


def test_mercury_jupiter_flow_includes_global_pair_block_and_jupiter_hardening() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mercury",
            planet_b="Jupiter",
            aspect_type="sextile",
            mode="flow",
            premium_art_direction=True,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "catstyle pair flag glyph system v1" in blob
    assert "[jupiter ♃ hardening]" in blob
    assert "[mercury ☿ hardening]" in blob
    assert "mercury–jupiter flow cast v1" in blob or "mercury-jupiter flow cast v1" in blob.replace("–", "-")


def test_identity_marker_planet_symbols_match_canonical_registry() -> None:
    from astro_content_agent.content.catstyle.planet_identity_markers_v1 import (
        PLANET_IDENTITY_MARKER_PROFILES,
    )

    for name, prof in PLANET_IDENTITY_MARKER_PROFILES.items():
        assert canonical_glyph_char(name) == prof.planet_symbol
