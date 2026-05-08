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
    assert "premium cinematic comic-poster illustration" in joined
    assert "contour" in joined or "silhouette" in joined
    assert "rounded comic-body proportions" in joined or "planet-cats" in joined


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
    assert "kawaii" in neg or "chibi" in neg
    assert "sticker" in neg or "flat mascot" in neg
    assert "childish" in neg or "nursery" in neg


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
    assert "tug-of-war" in blob or "travel" in blob or "adventure" in blob


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


def test_prompt_pack_includes_identity_markers_v1_block() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    low = pack.image_prompts[0].lower()
    assert "[identity markers v1]" in low
    assert "jupiter glyph" in low and "mars glyph" in low


def test_prompt_pack_without_skins_unchanged_shape() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    req = CatstylePromptRequest(
        planet_a="Jupiter",
        planet_b="Mars",
        aspect_type="square",
        mode="tension",
    )
    pack = generate_catstyle_prompt_pack(req)
    assert len(pack.image_prompts) == 2
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
    assert "mars planet-cat [canon v1 base]" in blob
    assert "shield" in blob or "spear" in blob or "cliff" in blob
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


def test_default_premium_injects_world_template_block() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            premium_art_direction=True,
        )
    )
    low = pack.image_prompts[0].lower()
    assert "[world template v1 - high-priority setting direction]" in low
    assert pack.world_template_profile is not None
    assert pack.world_template_profile["template_key"] == "cosmic_zodiac_arena"


def test_premium_off_skips_default_world_shell() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    low = pack.image_prompts[0].lower()
    assert "[world template v1" not in low
    assert pack.world_template_profile is None


def test_explicit_world_and_scene_blocks_in_prompt() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            world_template_key="cosmic_zodiac_arena",
            scene_template_key="mars_spartan_cliff_kick",
            skin_b="spartan_king",
        )
    )
    raw = pack.image_prompts[0].lower()
    assert "[world template v1 - high-priority setting direction]" in raw
    assert "[scene template v1 - high-priority frame direction]" in raw
    assert "[canon v1 base]" in raw
    assert "[identity markers v1]" in raw
    assert "cliff" in raw or "kick" in raw
    assert "shield" in raw and "spear" in raw
    assert "mars glyph" in raw
    assert pack.scene_template_profile is not None
    assert pack.scene_template_profile["template_key"] == "mars_spartan_cliff_kick"


def test_venus_wind_grate_scene_prompt_lines() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Uranus",
            planet_b="Venus",
            aspect_type="square",
            mode="tension",
            world_template_key="cosmic_zodiac_arena",
            scene_template_key="venus_marilyn_wind_grate",
        )
    )
    raw = pack.image_prompts[0].lower()
    assert "[scene template v1 - high-priority frame direction]" in raw
    assert "grate" in raw
    assert "skirt" in raw or "dress" in raw
    assert "venus glyph" in raw


def test_invalid_world_template_raises() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    with pytest.raises(ValueError, match="Unknown Catstyle world template"):
        generate_catstyle_prompt_pack(
            CatstylePromptRequest(
                planet_a="Jupiter",
                planet_b="Mars",
                aspect_type="square",
                mode="tension",
                world_template_key="bad_world",
            )
        )


def test_invalid_scene_template_raises() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    with pytest.raises(ValueError, match="Unknown Catstyle scene template"):
        generate_catstyle_prompt_pack(
            CatstylePromptRequest(
                planet_a="Jupiter",
                planet_b="Mars",
                aspect_type="square",
                mode="tension",
                scene_template_key="nope_scene",
            )
        )


def test_incompatible_scene_template_raises() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    with pytest.raises(ValueError, match="incompatible"):
        generate_catstyle_prompt_pack(
            CatstylePromptRequest(
                planet_a="Jupiter",
                planet_b="Mars",
                aspect_type="square",
                mode="tension",
                scene_template_key="venus_marilyn_wind_grate",
            )
        )


def test_default_render_style_is_premium_poster_v2() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    req = CatstylePromptRequest(
        planet_a="Moon",
        planet_b="Uranus",
        aspect_type="opposition",
        mode="tension",
        premium_art_direction=False,
    )
    assert req.render_style_profile_key == "premium_comic_poster_v2"


def test_prompt_includes_render_style_block_default_profile() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Pluto",
            planet_b="Venus",
            aspect_type="conjunction",
            mode="tension",
            premium_art_direction=False,
        )
    )
    raw = pack.image_prompts[0].lower()
    assert "[render style v1 - high-priority visual finish]" in raw
    assert pack.render_style_profile is not None
    assert pack.render_style_profile["key"] == "premium_comic_poster_v2"


def test_premium_render_style_keywords_movie_poster_lighting() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            render_style_profile_key="premium_comic_poster_v1",
        )
    )
    raw = pack.image_prompts[0].lower()
    assert "premium cinematic comic" in raw
    assert "movie-poster" in raw or "movie poster" in raw.replace("-", " ")
    assert "bold" in raw and "contour" in raw
    assert "rim light" in raw or "rim-light" in raw.replace(" ", "-")


def test_negative_prompt_includes_render_style_anti_flat_additions() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Uranus",
            aspect_type="square",
            mode="tension",
        )
    )
    neg = pack.negative_prompt.lower()
    assert "flat mascot sticker aesthetic" in neg or "flat mascot" in neg
    assert "photorealistic" in neg or "photoreal" in neg


def test_clean_cartoon_render_style_differs_from_premium() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
            render_style_profile_key="clean_cartoon_action_v1",
        )
    )
    raw = pack.image_prompts[0].lower()
    assert "[render style v1 - high-priority visual finish]" in raw
    assert "cel" in raw or "graphic cartoon action" in raw
    assert pack.render_style_profile is not None
    assert pack.render_style_profile["key"] == "clean_cartoon_action_v1"


def test_invalid_render_style_profile_raises() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    with pytest.raises(ValueError, match="Unknown Catstyle render style profile"):
        generate_catstyle_prompt_pack(
            CatstylePromptRequest(
                planet_a="Jupiter",
                planet_b="Mars",
                aspect_type="square",
                mode="tension",
                render_style_profile_key="bogus_render_style",
            )
        )


def test_prompt_pack_model_dump_includes_render_style_profile() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Pluto",
            planet_b="Moon",
            aspect_type="conjunction",
            mode="tension",
        )
    )
    blob = pack.model_dump(mode="json")
    assert blob.get("render_style_profile") is not None
    assert blob["render_style_profile"]["key"] == "premium_comic_poster_v2"
    assert blob.get("image_prompt_shot_roles") == ["hero_poster", "alternate_action_angle"]


def test_default_hero_pair_assigns_distinct_shot_roles_and_banners() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Pluto",
            planet_b="Moon",
            aspect_type="conjunction",
            mode="tension",
        )
    )
    assert pack.image_prompt_shot_roles == ["hero_poster", "alternate_action_angle"]
    low0 = pack.image_prompts[0].lower()
    low1 = pack.image_prompts[1].lower()
    assert "[shot role v1 - premium hero framing] hero_poster:" in low0
    assert "[shot role v1 - premium hero framing] alternate_action_angle:" in low1
    assert "alternate_action_angle:" not in low0


def test_shot_mode_standard_omits_shot_role_labels() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Pluto",
            planet_b="Moon",
            aspect_type="conjunction",
            mode="tension",
            shot_mode="standard",
        )
    )
    assert pack.image_prompt_shot_roles == [None, None]
    joined = " ".join(pack.image_prompts).lower()
    assert "[shot role v1" not in joined


def test_epic_arena_showdown_profile_includes_environment_scale_and_readable_subjects() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Saturn",
            aspect_type="square",
            mode="tension",
            shot_mode="epic_arena_showdown",
            world_template_key="cosmic_zodiac_arena",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[shot/composition profile v4 - epic_arena_showdown]" in blob
    assert "mythic showdown poster" in blob
    assert "ceremonial cosmic arena" in blob
    assert "environment is a co-star" in blob
    assert "heroic medium-wide to wide cinematic composition" in blob
    assert "pull the camera back slightly into wider poster framing" in blob
    assert "characters occupy slightly less of the frame" in blob
    assert "preserve negative space and breathing room around central action" in blob
    assert "coliseum recedes into the distance" in blob
    assert "arena walls rise behind the characters" in blob
    assert "more visible arena floor and more upper architecture" in blob
    assert "elevated rather than attached directly behind characters" in blob
    assert "clearly readable zodiac floor ring" in blob
    assert "layered coliseum walls" in blob
    assert "visible upper arches" in blob
    assert "deep stadium tiers/perspective" in blob
    assert "additional side architectural structures" in blob
    assert "stronger monumental arena feeling" in blob
    assert "two large readable faction banners on opposite arena sides" in blob
    assert "one side marker per planet" in blob
    assert "clearly readable distant earth or earth-like blue-green planet" in blob
    assert "visible cloud and/or continent pattern" in blob
    assert "human-world impact cue" in blob
    assert "smaller than characters but visually legible" in blob
    assert "clearly above and behind the arena" in blob
    assert "do not replace the earth impact cue with moon/jupiter/mars/saturn" in blob
    assert "planet identity belongs on characters, banners, props, glyphs, and arena symbols" in blob
    assert "for moon aspects specifically" in blob
    assert "avoid ambiguous moon-like background orb" in blob
    assert "large moon sky-body as the main celestial cue" in blob
    assert "exact glyph + emblem recognizability lock for moon/saturn" in blob
    assert "prefer moon banner exact glyph '☾'" in blob
    assert "saturn banner exact glyph '♄'" in blob
    assert "if saturn glyph rendering becomes unstable or unreadable" in blob
    assert "ringed-planet silhouette / ringed sphere icon" in blob
    assert "fake letters" in blob and "faux-alphabet glyphs" in blob
    assert "smaller accessory glyphs/emblems are secondary only" in blob
    assert "moon/saturn epic arena scale hard lock" in blob
    assert "benchmark alignment note (approved jupiter/mars epic arena scale as distant composition reference target)" in blob
    assert "pull the camera back further than baseline epic mode" in blob
    assert "characters must occupy slightly less of the overall frame" in blob
    assert "coliseum walls must recede clearly into the distance" in blob
    assert "avoid compositions where arena walls feel pasted or attached flat immediately behind the characters" in blob
    assert "[catstyle approved reference anchor v1 - moon/saturn square+tension]" in blob
    assert "registry_key=moon_saturn_square_tension_v1" in blob
    assert "[moon-saturn epic arena action staging v5 - balanced lock]" in blob
    assert all(29000 <= len(p) <= 31800 for p in pack.image_prompts)
    assert "premium cinematic comic-poster illustration" in blob
    assert "high-drama heroic comic-cover battle splash" in blob
    assert "polished 2d/2.5d comic" in blob
    assert "collectible-cover polish" in blob
    assert "dramatic focal and rim-impact lighting" in blob
    assert "layered foreground/midground/background depth" in blob
    assert "dark-but-vivid" in blob
    assert "forbid muddy darkness" in blob
    assert "not soft nursery art" in blob or "not cute nursery" in blob
    assert "washed-out painterly blur" in blob or "not flat mascot" in blob
    assert "saturn may use chain/control as saturnian restraint" in blob
    assert "moon may hold, brace, swing, or strike with pillow energy" in blob
    assert "exactly one earth-like sphere above and behind arena" in blob
    assert "avoid duplicate earth-like globes" in blob
    assert "ringed-planet silhouette / ringed sphere icon" in blob or "saturn banner exact glyph '♄'" in blob
    assert "coliseum recedes into the distance" in blob
    assert "more visible arena floor and more upper architecture" in blob
    assert "movie-one-sheet readability" in blob
    assert "controlled detail density" in blob
    assert "first-glance cause/effect readability" in blob
    assert "clear faces, readable poses, clean silhouette separation" in blob
    assert "avoid tight crop and character-dominant framing" in blob
    assert "vague background darkness" in blob
    assert "disappearing coliseum" in blob
    assert "tiny/barely readable earth cue" in blob
    assert "only one visible side banner" in blob
    assert "environment reduced to a backdrop afterthought" in blob


def test_epic_arena_showdown_moon_saturn_soft_aspect_skips_hard_action_staging() -> None:
    """Hard-aspect dynamic staging applies only to square/opposition."""
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Saturn",
            aspect_type="trine",
            mode="mixed",
            shot_mode="epic_arena_showdown",
            world_template_key="cosmic_zodiac_arena",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[moon-saturn epic arena action staging v5" not in blob
    assert "[moon-saturn final quality lock v2]" not in blob
    assert "[catstyle approved reference anchor v1" not in blob


def test_epic_arena_showdown_moon_saturn_square_mixed_has_staging_without_registry_anchor() -> None:
    """Approved-reference anchor matches registry square+tension only."""
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Saturn",
            aspect_type="square",
            mode="mixed",
            shot_mode="epic_arena_showdown",
            world_template_key="cosmic_zodiac_arena",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[moon-saturn epic arena action staging v5 - balanced lock]" in blob
    assert "registry_key=moon_saturn_square_tension_v1" not in blob


def test_epic_arena_showdown_moon_saturn_opposition_has_staging_without_square_tension_anchor() -> None:
    """Hard-aspect staging applies; registry anchor only matches square+tension."""
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Saturn",
            aspect_type="opposition",
            mode="tension",
            shot_mode="epic_arena_showdown",
            world_template_key="cosmic_zodiac_arena",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[moon-saturn epic arena action staging v5 - balanced lock]" in blob
    assert "exactly one earth-like sphere above and behind arena" in blob
    assert "registry_key=moon_saturn_square_tension_v1" not in blob


def test_premium_render_style_opens_prompt_without_legacy_flat_cartoon_anchor() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            render_style_profile_key="premium_comic_poster_v1",
            world_template_key="cosmic_zodiac_arena",
            scene_template_key="mars_spartan_cliff_kick",
        )
    )
    p0 = pack.image_prompts[0]
    low = p0.lower()
    assert low.startswith("premium cinematic comic-poster illustration")
    assert "simple adult-cartoon" not in low
    assert "flat colors" not in low[:520]
    assert "[canon v1 base]" in low
    assert "[identity markers v1]" in low
    assert "[world template v1 - high-priority setting direction]" in low
    assert "[scene template v1 - high-priority frame direction]" in low
    assert "[render style v1 - high-priority visual finish]" in low
    assert "[shot role v1 - premium hero framing]" in low


def test_clean_cartoon_render_style_opens_with_cartoon_action_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            render_style_profile_key="clean_cartoon_action_v1",
        )
    )
    assert pack.image_prompts[0].lower().startswith("clean premium cartoon-action illustration")


def test_negative_prompt_includes_strengthened_anti_childish_flat_guidance() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(planet_a="Moon", planet_b="Uranus", aspect_type="opposition", mode="tension")
    )
    neg = pack.negative_prompt.lower()
    assert "sticker mascot" in neg
    assert "childish nursery" in neg
    assert "kawaii" in neg and "chibi" in neg
    assert "3d game render finish" in neg or "3d cgi" in neg
    assert "game splash render" in neg
    assert "microtexture" in neg and "tiny crack" in neg


def test_moon_saturn_prompt_preserves_distinct_identity_and_saturn_anti_fire() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Saturn",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[planet canon v1 - moon]" in blob
    assert "[planet canon v1 - saturn]" in blob
    assert "soft" in blob and ("comfort" in blob or "safety" in blob)
    assert "cold" in blob and ("stone" in blob or "iron" in blob)
    assert "do not depict saturn with flames" in blob
    assert "saturn must-not traits lock" in blob


def test_moon_saturn_square_tension_includes_visual_correction_patch() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Saturn",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[moon-saturn visual correction patch v1" in blob
    assert "[aspect choreography v1 - square]" in blob
    assert "strike/counterstrike" in blob or "tense collision" in blob
    assert "pillow strike" in blob and "moonlight wave" in blob
    assert ("stone block" in blob or "gravity press" in blob) and (
        "freeze/frost field" in blob or "time-lock" in blob
    )
    assert "generic action-hero brawl" in blob or "fire ninja" in blob
    assert "do not let saturn inherit mars visual traits" in blob
    assert "vulnerability vs discipline" in blob
    assert "stone gate of time and responsibility" in blob
    assert "cozy doorway/window" in blob
    assert "martial-arts duel choreography" in blob or "no martial-arts duel choreography" in blob
    assert "not 3d cgi figurine" in blob
    assert "[arena composition boost v1]" in blob
    assert "medium-wide dramatic arena framing" in blob
    assert "zodiac symbols around the ring" in blob
    assert "curved coliseum wall" in blob
    assert "arches/stadium tiers/layered architecture depth" in blob
    assert "avoid overly tight crop on the two characters" in blob
    assert "avoid background collapsing into vague darkness" in blob


def test_aspect_choreography_square_vs_trine_tone() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    square_pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mercury",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    trine_pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mercury",
            aspect_type="trine",
            mode="tension",
            premium_art_direction=False,
        )
    )
    sextile_pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mercury",
            aspect_type="sextile",
            mode="tension",
            premium_art_direction=False,
        )
    )
    sq_blob = " ".join(square_pack.image_prompts).lower()
    tri_blob = " ".join(trine_pack.image_prompts).lower()
    sex_blob = " ".join(sextile_pack.image_prompts).lower()
    assert "[aspect choreography v1 - square]" in sq_blob
    assert "friction" in sq_blob or "strike/counterstrike" in sq_blob
    assert "[aspect choreography v1 - trine]" in tri_blob
    assert "dance-like harmony" in tri_blob or "synchronized movement" in tri_blob
    assert "[aspect choreography v1 - sextile]" in sex_blob
    assert "playful cooperation" in sex_blob or "coordinated exchange" in sex_blob


def test_opposition_prompt_includes_conflict_choreography_not_trine_flow() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="opposition",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[aspect choreography v1 - opposition]" in blob
    assert ("mirrored duel" in blob or "push-pull" in blob) and "dance-like harmony" not in blob


def test_mars_heavy_style_reference_finisher_decouple_guard_for_non_mars_pair() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Saturn",
            aspect_type="square",
            mode="tension",
            mars_heavy_style_reference_finisher=True,
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[mars-heavy style reference decoupling v1]" in blob
    assert "do not import mars choreography" in blob


def test_mars_named_scene_template_triggers_decouple_for_saturn_mars_pair() -> None:
    """mars_* scene with Mars actually in the pair should not inject decouple noise."""
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            scene_template_key="mars_spartan_cliff_kick",
            skin_b="spartan_king",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[mars-heavy style reference decoupling v1]" not in blob



def test_venus_pluto_prompt_keeps_distinct_planet_identities() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Venus",
            planet_b="Pluto",
            aspect_type="opposition",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[planet canon v1 - venus]" in blob
    assert "[planet canon v1 - pluto]" in blob
    assert "venus must-have traits lock" in blob
    assert "pluto must-have traits lock" in blob
    assert "charm" in blob or "beauty" in blob
    assert "underworld" in blob or "subterranean" in blob or "depth" in blob


def test_animation_prompt_uses_render_style_opening_not_legacy_style_core() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(planet_a="Pluto", planet_b="Moon", aspect_type="conjunction", mode="tension")
    )
    anim = pack.animation_prompt.lower()
    assert anim.startswith("premium cinematic comic-poster illustration")
    assert "[style hardlock v2 - premium poster mandate]" in anim
    assert "simple adult-cartoon" not in anim
    assert "thick black outlines" not in anim


def test_premium_comic_poster_v2_jupiter_mars_charged_arena_scene_hardlock() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            editorial_profile="charged",
            world_template_key="cosmic_zodiac_arena",
            scene_template_key="mars_spartan_cliff_kick",
            render_style_profile_key="premium_comic_poster_v2",
            premium_art_direction=False,
        )
    )
    raw = pack.image_prompts[0].lower()
    assert pack.render_style_profile["key"] == "premium_comic_poster_v2"
    assert raw.startswith("premium cinematic comic-poster illustration")
    assert "poster-grade comic splash illustration" in raw
    assert "high-drama heroic" in raw
    assert "not photoreal, not 3d cgi, not game splash render" in raw
    assert "[style hardlock v2 - premium poster mandate]" in raw
    assert "no dense microtexture layering" in raw
    assert "less detailed than characters" in raw
    assert "coliseum" in raw
    assert "battle" in raw
    assert "[arena composition boost v1]" in raw
    assert "readable arena floor plane" in raw
    assert "curved coliseum wall" in raw
    assert "zodiac symbols around the ring" in raw
    assert "environmental breathing room" in raw
    assert "not tight close-up" in raw
    assert "not tiny distant characters" in raw
    assert "[canon v1 base]" in raw
    assert "[identity markers v1]" in raw
    assert "[world template v1" in raw
    assert "[scene template v1" in raw
    assert "[render style v1 - high-priority visual finish]" in raw


def test_arena_composition_boost_block_present_for_non_hard_aspect_baseline() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Pluto",
            planet_b="Venus",
            aspect_type="conjunction",
            mode="tension",
            premium_art_direction=False,
            shot_mode="standard",
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[arena composition boost v1]" in blob
    assert "medium-wide dramatic framing with environmental breathing room" in blob
    assert "keep both planet-cats prominent" in blob


def test_v2_negative_prompt_is_deduped_compact_and_keeps_forbidden_categories() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            editorial_profile="charged",
            world_template_key="cosmic_zodiac_arena",
            scene_template_key="mars_spartan_cliff_kick",
            render_style_profile_key="premium_comic_poster_v2",
        )
    )
    neg = pack.negative_prompt
    parts = [p.strip() for p in neg.split(",") if p.strip()]
    norm = [" ".join(p.lower().split()) for p in parts]
    assert len(norm) == len(set(norm))
    assert len(neg) <= 1200
    low = neg.lower()
    assert "photoreal" in low
    assert "cgi" in low
    assert "game splash render" in low or "game render" in low
    assert "microtexture" in low
    assert "tiny crack" in low
    assert "particles" in low
    assert "nursery" in low
    assert "kawaii" in low
    assert "chibi" in low
    assert "sticker" in low
    assert "flat vector" in low
    assert "architecture" in low
    assert "weak bland composition" in low

