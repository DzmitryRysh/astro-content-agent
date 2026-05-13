"""Tests for Catstyle planet identity markers v1."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.content.catstyle.planet_identity_markers_v1 import (
    PLANET_IDENTITY_MARKER_PROFILES,
    format_identity_markers_prompt_block,
    get_planet_identity_marker_profile,
    list_planet_identity_marker_profiles,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack

_EXPECTED = {
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
}


def test_all_ten_planets_in_registry() -> None:
    assert set(PLANET_IDENTITY_MARKER_PROFILES) == _EXPECTED


def test_list_stable_order_matches_canon_roster() -> None:
    names = [p.planet_name for p in list_planet_identity_marker_profiles()]
    assert names == [
        "Sun",
        "Moon",
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
    ]


def test_each_profile_has_core_fields() -> None:
    for p in list_planet_identity_marker_profiles():
        assert p.planet_symbol.strip()
        assert p.symbol_name.strip()
        assert p.primary_marker.strip()
        assert p.secondary_marker.strip()
        assert p.signature_prop.strip()
        assert p.placement_rules
        assert p.must_show_markers
        assert p.visual_read_rule.strip()
        assert p.short_prompt_line.strip()


def test_unknown_planet_raises() -> None:
    with pytest.raises(ValueError, match="Unknown planet"):
        get_planet_identity_marker_profile("Eris")


def test_format_block_includes_symbol_and_must_show() -> None:
    m = get_planet_identity_marker_profile("Mars")
    txt = format_identity_markers_prompt_block("Mars", m, has_skin=False)
    assert "[IDENTITY MARKERS v1]" in txt
    assert "Mars glyph" in txt or "male sign" in txt.lower()
    assert "Staging objectives" in txt


def test_format_block_skin_clause_when_overlay() -> None:
    m = get_planet_identity_marker_profile("Mars")
    txt = format_identity_markers_prompt_block("Mars", m, has_skin=True)
    assert "Skin/costume overlay" in txt


def test_prompt_mars_includes_identity_markers_and_canon() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = pack.image_prompts[0].lower()
    assert "[identity markers v1]" in blob
    assert "mars glyph" in blob
    assert "bandana" in blob
    assert "[canon v1 base]" in blob


def test_prompt_venus_symbol_guidance() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="opposition",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = pack.image_prompts[0].lower()
    assert "[identity markers v1]" in blob
    assert "venus glyph" in blob
    assert "clasp" in blob or "mirror" in blob or "jewelry" in blob or "handbag" in blob


def test_prompt_neptune_trident_or_glyph() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Neptune",
            planet_b="Mercury",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = pack.image_prompts[0].lower()
    assert "[identity markers v1]" in blob
    assert "neptune glyph" in blob
    assert "trident" in blob


def test_prompt_mars_spartan_preserves_canon_markers_and_skin() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            skin_b="spartan_king",
            premium_art_direction=False,
        )
    )
    low = pack.image_prompts[0].lower()
    assert "[canon v1 base]" in low
    assert "[identity markers v1]" in low
    assert "optional costume overlay only" in low
    assert "spartan king" in low
    assert "skin/costume overlay" in low
    assert "preserve the full [canon v1 base]" in low and "[identity markers v1]" in low


def test_no_skin_still_has_identity_markers() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Moon",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    assert "[IDENTITY MARKERS v1]" in pack.image_prompts[0]
