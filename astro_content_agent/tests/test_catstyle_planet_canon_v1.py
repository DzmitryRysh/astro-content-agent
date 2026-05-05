"""Tests for Catstyle planet canon v1."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.planet_canon_v1 import (
    PLANET_CAT_CANONS,
    get_planet_canon,
    list_planet_canons,
    normalize_planet_name,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


_EXPECTED_TEN = {
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
    assert set(PLANET_CAT_CANONS) == _EXPECTED_TEN


def test_list_planet_canons_stable_order() -> None:
    names = [c.planet_name for c in list_planet_canons()]
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


def test_normalize_planet_name_case_insensitive() -> None:
    assert normalize_planet_name("mars") == "Mars"


def test_get_unknown_planet_raises_clear_message() -> None:
    with pytest.raises(ValueError, match="Unknown planet .*canon v1 supports"):
        get_planet_canon("Eris")


def test_mars_canon_bandana_flame_nick() -> None:
    m = get_planet_canon("Mars")
    blob = f"{m.short_prompt_line} {m.signature_props} {m.recognizability_rule}".lower()
    assert "bandana" in blob
    assert "flame" in blob
    assert "nick" in blob or "bitten" in blob


def test_moon_canon_pillow_blanket_cozy() -> None:
    m = get_planet_canon("Moon")
    low = f"{m.signature_props} {m.short_prompt_line} {m.recognizability_rule}".lower()
    assert "pillow" in low
    assert "blanket" in low or "pled" in low


def test_saturn_canon_hat_watch_structure() -> None:
    s = get_planet_canon("Saturn")
    block = f"{s.silhouette_notes} {s.signature_props} {s.short_prompt_line}".lower()
    assert "hat" in block
    assert "watch" in block
    assert "pinstripe" in block or "suit" in block


def test_pluto_canon_hypnotic_shadow_cauldron() -> None:
    p = get_planet_canon("Pluto")
    low = f"{p.signature_props} {p.short_prompt_line} {p.recognizability_rule}".lower()
    assert "spiral" in low
    assert "shadow" in low or "smoke" in low
    assert "cauldron" in low


def test_uranus_canon_punk_portal_electric() -> None:
    u = get_planet_canon("Uranus")
    low = f"{u.short_prompt_line} {u.signature_props} {u.role_archetype}".lower()
    assert "punk" in low or "rebel" in low
    assert "portal" in low
    assert "electric" in low or "lightning" in low


def test_venus_canon_elegant_not_clutter() -> None:
    v = get_planet_canon("Venus")
    low_vis = v.visual_avoid.lower()
    assert "clutter" in low_vis or "overload" in low_vis or "bling" in low_vis
    assert "exactly one" in v.signature_props.lower() or "one rose" in v.signature_props.lower()


def test_prompt_generator_emits_canon_v1_base_block() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(planet_a="Jupiter", planet_b="Mars", aspect_type="square", mode="tension")
    )
    blob = pack.image_prompts[0].lower()
    assert "[canon v1 base]" in blob
    assert "recognizability rule:" in blob


def test_mars_skin_preserves_canon_language() -> None:
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
    text = pack.image_prompts[0].lower()
    assert "[canon v1 base]" in text
    assert "bandana" in text or "flame" in text
    assert "optional costume overlay only" in text
    assert "preserve the full [canon v1 base]" in text
    assert "[identity markers v1]" in text
    assert "spartan king" in text
