"""Tests for Catstyle Planet Canon v1 deterministic identity layer."""
from __future__ import annotations

from astro_content_agent.content.catstyle.planet_canon import (
    PLANET_CANON_V1,
    build_planet_canon_prompt_fragment,
    get_planet_canon,
    list_planet_canons,
)


def test_canon_exists_for_all_ten_planets() -> None:
    expected = {
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
    assert set(PLANET_CANON_V1) == expected
    assert {p.planet_name for p in list_planet_canons()} == expected


def test_each_canon_has_non_empty_must_have_and_must_not_have() -> None:
    for canon in PLANET_CANON_V1.values():
        assert canon.must_have
        assert canon.must_not_have
        assert all(str(x).strip() for x in canon.must_have)
        assert all(str(x).strip() for x in canon.must_not_have)


def test_get_saturn_canon_has_cold_stone_metal_language() -> None:
    saturn = get_planet_canon("Saturn")
    blob = " ".join(
        [
            saturn.core_mood,
            saturn.visual_language,
            saturn.materials,
            " ".join(saturn.must_have),
            " ".join(saturn.must_not_have),
        ]
    ).lower()
    assert "cold" in blob
    assert "stone" in blob
    assert "iron" in blob or "metal" in blob
    frag = build_planet_canon_prompt_fragment("Saturn").lower()
    assert "[planet canon v1 - saturn]" in frag
