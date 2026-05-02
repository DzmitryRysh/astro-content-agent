"""Tests for Catstyle v0 prompt generator (no image APIs)."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.aspect_library_v0 import ASPECT_CAT_INTERACTIONS
from astro_content_agent.content.catstyle.planet_bible_v0 import PLANET_CAT_PROFILES
from astro_content_agent.services.content.catstyle_prompt_generator import (
    generate_catstyle_prompt_pack,
    normalize_planet_name,
)


def test_all_ten_planet_profiles_exist() -> None:
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
    assert set(PLANET_CAT_PROFILES) == expected
    for name, prof in PLANET_CAT_PROFILES.items():
        assert prof.planet_name == name
        assert prof.visual_identity
        assert prof.colors
        assert prof.stressed_expression
        assert prof.constructive_expression


def test_five_aspect_interactions_exist() -> None:
    assert len(ASPECT_CAT_INTERACTIONS) == 5
    keys = {tuple(sorted(k, key=str.lower)) for k in ASPECT_CAT_INTERACTIONS}
    assert ("Pluto", "Venus") in keys
    assert ("Saturn", "Venus") in keys
    assert ("Mars", "Neptune") in keys
    assert ("Moon", "Uranus") in keys
    assert ("Jupiter", "Mercury") in keys


def test_variants_count_respected() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    req = CatstylePromptRequest(
        planet_a="pluto",
        planet_b="venus",
        aspect_type="conjunction",
        mode="tension",
        variants_count=6,
    )
    pack = generate_catstyle_prompt_pack(req)
    assert len(pack.image_prompts) == 6


def test_prompts_include_planet_names_and_style_constraints() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    req = CatstylePromptRequest(
        planet_a="Mars",
        planet_b="Neptune",
        aspect_type="square",
        mode="mixed",
        variants_count=4,
    )
    pack = generate_catstyle_prompt_pack(req)
    joined = " ".join(pack.image_prompts).lower()
    assert "mars" in joined and "neptune" in joined
    assert "thick black outlines" in joined
    assert "round bodies" in joined
    assert "dark starry" in joined


def test_negative_prompt_bans_text_logos_realism_excess_detail() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Uranus",
            aspect_type="opposition",
            mode="tension",
        )
    )
    neg = pack.negative_prompt.lower()
    assert "text" in neg or "words" in neg
    assert "logo" in neg
    assert "photorealistic" in neg or "hyperreal" in neg
    assert "micro-detail" in neg or "filigree" in neg or "crowded" in neg


def test_pluto_venus_includes_cauldron_and_shadow_control_metaphor_non_explicit() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Pluto",
            planet_b="Venus",
            aspect_type="conjunction",
            mode="tension",
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "cauldron" in blob
    assert ("shadow" in blob or "control" in blob or "influence" in blob)
    assert "gore" in pack.negative_prompt.lower() or "explicit" in pack.negative_prompt.lower()


def test_jupiter_mercury_teacher_vs_analyst_theme() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mercury",
            aspect_type="trine",
            mode="tension",
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "jupiter" in blob and "mercury" in blob
    assert "teacher" in blob and "analyst" in blob


def test_unknown_pair_raises() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    with pytest.raises(ValueError, match="No Catstyle aspect library"):
        generate_catstyle_prompt_pack(
            CatstylePromptRequest(
                planet_a="Sun",
                planet_b="Mars",
                aspect_type="conjunction",
                mode="tension",
            )
        )


def test_normalize_planet_name_case_insensitive() -> None:
    assert normalize_planet_name("VENUS") == "Venus"
