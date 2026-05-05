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
    control_language = (
        "hypnotic" in blob
        or "spiral" in blob
        or "shadow" in blob
        or "orbit" in blob
        or "puppet" in blob
        or "tendril" in blob
        or "mesmer" in blob
        or "dazed" in blob
        or "strings" in blob
    )
    assert control_language
    venus_strain_language = (
        "overwhelmed" in blob
        or "trapped" in blob
        or "dazed" in blob
        or "mesmer" in blob
        or "caught" in blob
        or "spell" in blob
    )
    assert venus_strain_language
    neg = pack.negative_prompt.lower()
    assert "horror" in neg or "gore" in neg
    assert "fetish" in neg or "explicit" in neg


def test_uranus_moon_prompt_includes_pillow_and_blanket_comfort() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Uranus",
            planet_b="Moon",
            aspect_type="square",
            mode="tension",
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "pillow" in blob
    assert "blanket" in blob


def test_neptune_mars_prompt_includes_fish_or_bubble_motif() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Neptune",
            aspect_type="square",
            mode="tension",
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert ("fish" in blob or "bubble" in blob)


def test_saturn_venus_includes_hat_watch_and_design_compensation() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    tension_pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="opposition",
            mode="tension",
        )
    )
    tblob = " ".join(tension_pack.image_prompts).lower()
    assert "wristwatch" in tblob or "watch" in tblob
    assert "hat" in tblob or "pinstripe" in tblob
    assert "business" in tblob or "audit" in tblob or "clipboard" in tblob or "contract" in tblob

    comp_pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="trine",
            mode="compensation",
        )
    )
    cblob = " ".join(comp_pack.image_prompts).lower()
    assert "design" in cblob or "studio" in cblob or "jewelry" in cblob or "architecture" in cblob or "business" in cblob


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
    assert "star map" in blob or "star-map" in blob.replace(" ", "")
    assert "travel" in blob


def test_unknown_pair_raises() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    with pytest.raises(ValueError, match="No Catstyle content.*outer-to-personal"):
        generate_catstyle_prompt_pack(
            CatstylePromptRequest(
                planet_a="Sun",
                planet_b="Mars",
                aspect_type="conjunction",
                mode="tension",
            )
        )


def test_pluto_moon_prompt_uses_seed_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Pluto",
            planet_b="Moon",
            aspect_type="conjunction",
            mode="tension",
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "pillow" in blob or "blanket" in blob
    assert "shadow" in blob or "cauldron" in blob or "spiral" in blob


def test_saturn_mars_prompt_uses_seed_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(planet_a="Saturn", planet_b="Mars", aspect_type="square", mode="tension")
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "watch" in blob or "flame" in blob or "calendar" in blob or "ruler" in blob


def test_neptune_mercury_prompt_fish_fog_checklist_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(planet_a="Neptune", planet_b="Mercury", aspect_type="square", mode="tension")
    )
    blob = " ".join(pack.image_prompts).lower()
    assert ("fish" in blob or "fog" in blob) and ("checklist" in blob or "clipboard" in blob or "note" in blob)


def test_uranus_venus_prompt_electric_beauty_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(planet_a="Uranus", planet_b="Venus", aspect_type="opposition", mode="tension")
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "electric" in blob or "neon" in blob or "portal" in blob or "zig" in blob
    assert "venus" in blob


def test_jupiter_sun_prompt_spotlight_expansion_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(planet_a="Jupiter", planet_b="Sun", aspect_type="trine", mode="tension")
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "podium" in blob or "crown" in blob or "spotlight" in blob or "constellation" in blob or "stage" in blob


def test_pluto_venus_still_uses_deep_aspect_library_wording() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(planet_a="Pluto", planet_b="Venus", aspect_type="conjunction", mode="tension")
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "cauldron" in blob
    assert "half-submerged" in blob or "purple" in blob or "potion" in blob


def test_normalize_planet_name_case_insensitive() -> None:
    assert normalize_planet_name("VENUS") == "Venus"


def test_prompt_pack_without_skins_unchanged_shape() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    req = CatstylePromptRequest(
        planet_a="Jupiter",
        planet_b="Mars",
        aspect_type="square",
        mode="tension",
    )
    pack = generate_catstyle_prompt_pack(req)
    assert len(pack.image_prompts) == 4
    joined = " ".join(pack.image_prompts).lower()
    assert "archetype skin" not in joined


def test_premium_art_direction_disabled_skips_enrichment_block() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    req = CatstylePromptRequest(
        planet_a="Jupiter",
        planet_b="Mars",
        aspect_type="square",
        mode="tension",
        premium_art_direction=False,
    )
    pack = generate_catstyle_prompt_pack(req)
    assert "Premium comic direction" not in pack.image_prompts[0]
    assert pack.art_direction_profile is None


def test_jupiter_mars_charged_editorial_includes_premium_action_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            editorial_profile="charged",
        )
    )
    blob = pack.image_prompts[0].lower()
    assert "premium comic direction" in blob
    assert "scene energy (charged)" in blob
    assert "dynamic action read" in blob
    assert pack.art_direction_profile is not None
    assert pack.art_direction_profile["energy"] == "charged"


def test_saturn_venus_supportive_compensation_includes_collaboration_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="trine",
            mode="compensation",
            editorial_profile="supportive",
        )
    )
    blob = pack.image_prompts[0].lower()
    assert "scene energy (supportive)" in blob
    assert "elegant collaboration" in blob


def test_negative_prompt_includes_anti_bland_additions() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            editorial_profile="charged",
        )
    )
    neg = pack.negative_prompt.lower()
    assert "bland mascot pose" in neg
    assert "sticker-like" in neg


def test_spartan_skin_prompt_includes_skin_mandate_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            editorial_profile="charged",
            skin_b="spartan_king",
        )
    )
    low = pack.image_prompts[0].lower()
    assert "character skin mandate" in low
    assert "prioritize staging from hooks" in low


def test_prompt_pack_includes_spartan_skin_on_mars() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            skin_b="spartan_king",
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "archetype skin" in blob
    assert "spartan king" in blob
    assert "spear" in blob or "shield" in blob
    assert "mars planet-cat:" in blob
    assert "bandana" in blob
    assert "archetype overlays" in pack.animation_prompt.lower()
    assert "mars in spartan king skin" in pack.animation_prompt.lower()


def test_prompt_pack_includes_rambo_skin_on_mars() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            skin_b="rambo",
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "rambo" in blob
    assert "ammo" in blob or "machine gun" in blob or "tattoo" in blob


def test_skin_on_unsupported_planet_raises() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    with pytest.raises(ValueError, match="only support|Character skins"):
        generate_catstyle_prompt_pack(
            CatstylePromptRequest(
                planet_a="Moon",
                planet_b="Uranus",
                aspect_type="opposition",
                mode="tension",
                skin_a="spartan_king",
            )
        )


def test_jupiter_philosopher_skin_on_planet_a() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            skin_a="philosopher_mentor",
        )
    )
    blob = pack.image_prompts[0].lower()
    assert "philosopher mentor" in blob
    assert "scroll" in blob or "robe" in blob

