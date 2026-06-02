"""Tests for Catstyle v0 prompt generator (no image APIs)."""
from __future__ import annotations

from pathlib import Path

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


def test_saturn_venus_planet_reference_mode_omits_business_meeting_story_language(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
        APPROVED_PLANET_REFERENCE_LOCK_MARKER,
        ApprovedPlanetReferenceEntry,
        write_planet_registry_entries,
    )
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    reg = tmp_path / "approved_planet_references.json"
    saturn_png = tmp_path / "saturn.png"
    venus_png = tmp_path / "venus.png"
    saturn_png.write_bytes(b"s")
    venus_png.write_bytes(b"v")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="saturn_v1",
                planet="Saturn",
                image_path=str(saturn_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="venus_v1",
                planet="Venus",
                image_path=str(venus_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="square",
            mode="tension",
            use_planet_reference_auto=True,
            render_style_profile_key="premium_cg_keyart_v1",
        )
    )
    blob = " ".join(pack.image_prompts)
    low = blob.lower()
    assert "business meeting" not in low
    assert "fashion sketches" not in low
    assert "jewelry or watch layout" not in low
    assert "preserve [CANON v1 base]" not in blob
    assert "preserve approved planet reference identity" in blob
    assert APPROVED_PLANET_REFERENCE_LOCK_MARKER in blob
    assert "[CG MATERIAL FINISH HARDLOCK v2]" in blob
    assert "gravity fields" in low or "spatial pressure" in low


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
            disable_approved_reference_prompt_lock=True,
            disable_arena_reference_auto=True,
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
    assert "painted into the flag cloth" in blob
    assert "clearly readable distant earth or earth-like blue-green planet" in blob
    assert "visible cloud and/or continent pattern" in blob
    assert "human-world impact cue" in blob
    assert "smaller than characters but visually legible" in blob
    assert "clearly above and behind the arena" in blob
    assert "do not replace the earth impact cue with moon/jupiter/mars/saturn" in blob
    assert (
        "planet identity belongs on characters, costume/props, faction banner glyphs, and arena symbols"
        in blob
    )
    assert "for moon aspects specifically" in blob
    assert "avoid ambiguous moon-like background orb" in blob
    assert "large moon sky-body as the main celestial cue" in blob
    assert "[moon–saturn emblem discipline v1 — painted banner heraldry]" in blob or (
        "[moon-saturn emblem discipline v1 — painted banner heraldry]" in blob.replace("–", "-")
    )
    assert "canonical moon" in blob or "\u263d" in " ".join(pack.image_prompts).lower()
    assert "ringed-sphere silhouette" in blob
    assert "painted into the cloth" in blob
    assert "moon/saturn epic arena scale hard lock" in blob
    assert "benchmark alignment note (approved jupiter/mars epic arena scale as distant composition reference target)" in blob
    assert "pull the camera back further than baseline epic mode" in blob
    assert "characters must occupy slightly less of the overall frame" in blob
    assert "coliseum walls must recede clearly into the distance" in blob
    assert "avoid compositions where arena walls feel pasted or attached flat immediately behind the characters" in blob
    assert "bias extra recession versus default epic framing" in blob
    assert "moon side reads lunar" in blob
    assert "night-atmosphere brightness lift" in blob
    assert "arena-floor glow" in blob and "lunar rim" in blob
    assert "[catstyle approved reference anchor v1 - moon/saturn square+tension]" in blob
    assert "registry_key=moon_saturn_square_tension_v1" in blob
    assert "[moon-saturn epic arena action staging v5 - balanced lock]" in blob
    assert all(29_000 <= len(p) <= 38_500 for p in pack.image_prompts)
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
    assert "saturn's faction banner cloth" in blob
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


def test_premium_cg_keyart_render_style_in_prompt_and_opener_contract() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            premium_art_direction=False,
            render_style_profile_key="premium_cg_keyart_v1",
            world_template_key="cosmic_zodiac_arena",
            shot_mode="epic_arena_showdown",
        )
    )
    p0 = pack.image_prompts[0]
    low = p0.lower()
    assert low.startswith("premium cg key art illustration")
    assert "[style hardlock cg v1 - key art mandate]" in low
    assert "[render style v1 - high-priority visual finish]" in low
    assert "[catstyle global quality lock cg v1]" in low
    assert "2.5d" in low or "3d-hybrid" in low
    assert "crisp silhouette" in low
    assert "material separation" in low
    assert "high-contrast" in low
    assert "volumetric" in low
    assert "not watercolor" in low
    assert pack.render_style_profile is not None
    assert pack.render_style_profile["key"] == "premium_cg_keyart_v1"
    assert "gouache" in low
    assert "sketchbook" in low
    neg = pack.negative_prompt.lower()
    assert "watercolor" in neg
    assert "storybook" in neg or "children's illustration" in neg or "sketchbook" in neg


def test_premium_comic_poster_v2_still_default_and_opener_unchanged() -> None:
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
    assert pack.render_style_profile["key"] == "premium_comic_poster_v2"
    assert pack.image_prompts[0].lower().startswith("premium cinematic comic-poster illustration")
    assert "not 3d cgi" in pack.image_prompts[0].lower()


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


def test_moon_saturn_square_tension_includes_visual_canon_v1() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Moon",
            planet_b="Saturn",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
            disable_arena_reference_auto=True,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[moon-saturn square tension visual canon v1]" in blob
    assert "[aspect choreography v1 - square]" in blob
    assert "crescent sickle" in blob
    assert "secondary" in blob and ("cushion" in blob or "sleep relic" in blob)
    assert "lecturer" in blob or "strategist" in blob
    assert "psychological enforcer" in blob or "psychological" in blob
    assert "generic brawl" in blob or "generic brawl" in (pack.negative_prompt or "").lower()
    assert "[moon-saturn visual correction patch v1" not in blob
    assert "pillow strike" not in blob
    assert "vulnerability versus repression" in blob or "emotional pressure versus rigid control" in blob
    assert "niche statue" in blob or "background niche statues" in blob
    assert "warm golden" in blob or "golden lights" in blob or "golden arcade" in blob
    assert "[moon-saturn saturn identity hard lock v1]" in blob
    assert "orange" in blob and ("fire" in blob or "fiery" in blob)
    assert "lead" in blob and ("iron" in blob or "stone" in blob)
    assert "brute-warrior moon" in (pack.negative_prompt or "").lower() or "brute warrior" in (
        pack.negative_prompt or ""
    ).lower()


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


def test_tense_square_includes_active_battle_choreography_v2() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Uranus",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[tense aspect choreography v2 - square]" in blob
    assert "explosive" in blob or "impact" in blob or "counterattack" in blob
    assert "[tense aspect anti-static v1]" in blob
    assert "do not show characters simply standing" in blob
    assert "[tense aspect premium cg style lock v1]" in blob
    assert "watercolor" in blob and "painterly" in blob
    assert "[planetary combat lexicon v2 - mars]" in blob
    assert "[planetary combat lexicon v2 - uranus]" in blob


def test_tense_opposition_includes_active_polarity_clash_v2() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Pluto",
            aspect_type="opposition",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[tense aspect choreography v2 - opposition]" in blob
    assert "polarity clash" in blob or "force clash" in blob or "beam clash" in blob
    assert "[tense aspect anti-static v1]" in blob
    assert "combat already in progress" in blob
    assert "[planetary combat lexicon v2 - sun]" in blob
    assert "[planetary combat lexicon v2 - pluto]" in blob


def test_tense_square_flow_mode_skips_battle_v2_layer() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Uranus",
            aspect_type="square",
            mode="flow",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[tense aspect choreography v2 - square]" not in blob
    assert "[tense aspect anti-static v1]" not in blob
    assert "[catstyle flow mode v1" in blob


def test_tense_trine_does_not_include_battle_v2_layer() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Venus",
            planet_b="Neptune",
            aspect_type="trine",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "[tense aspect choreography v2" not in blob
    assert "[tense aspect anti-static v1]" not in blob


def test_mars_uranus_square_includes_arena_glyph_and_battle_staging() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Uranus",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts)
    low = blob.lower()
    assert "[catstyle visual composition hardlock v1]" in low
    assert "[catstyle arena scale lock v2]" in low
    assert "three visible tiers" in low or "at least three visible tiers" in low
    assert "[catstyle camera / framing lock v1]" in low
    assert "[catstyle premium cgi render lock v1]" in low
    assert "[catstyle environment dominance v1]" in low
    assert "painterly" in low and "watercolor" in low
    assert "[planet banner glyph lock v2]" in low
    assert "left/port banner" in low and "mars glyph" in low and "♂" in blob
    assert "right/starboard banner" in low and "uranus glyph" in low and "♅" in blob
    assert "[tense aspect anti-static v1]" in low
    assert "active collision" in low or "counterattack" in low
    assert "do not crop away arena scale" in low


def test_saturn_venus_square_planet_refs_includes_glyph_lock_and_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
        APPROVED_PLANET_REFERENCE_LOCK_MARKER,
        ApprovedPlanetReferenceEntry,
        write_planet_registry_entries,
    )
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    reg = tmp_path / "approved_planet_references.json"
    saturn_png = tmp_path / "saturn.png"
    venus_png = tmp_path / "venus.png"
    saturn_png.write_bytes(b"s")
    venus_png.write_bytes(b"v")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="saturn_v1",
                planet="Saturn",
                image_path=str(saturn_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="venus_v1",
                planet="Venus",
                image_path=str(venus_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="square",
            mode="tension",
            use_planet_reference_auto=True,
            premium_art_direction=False,
        )
    )
    blob = " ".join(pack.image_prompts)
    low = blob.lower()
    assert "[planet banner glyph lock v2]" in low
    assert "saturn glyph" in low and "♄" in blob
    assert "venus glyph" in low and "♀" in blob
    assert "do not use venus glyph for mars" in low
    assert APPROVED_PLANET_REFERENCE_LOCK_MARKER in blob
    assert "[reference role declaration v1]" in low
    assert "[planet-cat body material intensity v1]" in low


def test_opposition_includes_equal_force_duel_language() -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Pluto",
            aspect_type="opposition",
            mode="tension",
            premium_art_direction=False,
        )
    )
    low = " ".join(pack.image_prompts).lower()
    assert "[tense aspect choreography v2 - opposition]" in low
    assert "equal-force duel" in low or "central axis" in low
    assert "polarity clash" in low or "force clash" in low or "beam clash" in low
    assert "passive face-off" in low


def test_mercury_jupiter_sextile_flow_avoids_battle_language_keeps_premium_poster() -> None:
    """Flow mode must not inherit v2 battle-poster vocabulary; still reads as premium comic poster."""
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mercury",
            planet_b="Jupiter",
            aspect_type="sextile",
            mode="flow",
            premium_art_direction=True,
            variants_count=1,
        )
    )
    blob = " ".join(pack.image_prompts).lower()
    assert "comic-cover battle splash" not in blob
    assert "heroic comic-cover battle" not in blob
    assert "monumental duel staging" not in blob
    assert "body-on-body" not in blob
    assert "heroic battle splash" not in blob
    assert "collectible comic-cover / battle splash poster energy" not in blob
    assert "catstyle flow mode v1" in blob
    assert "planetary bodies first" in blob
    assert "alliance" in blob or "co-discovery" in blob or "discovery" in blob
    assert "premium cinematic comic-poster" in blob or "co-discovery alliance splash" in blob
    assert "instagram-mobile readable" in blob or "instagram-thumb" in blob
    assert "luminous golden" in blob and "portal" in blob
    assert "midtone" in blob or "luminous midtones" in blob
    assert "mercury rim" in blob or "mercury rim light" in blob
    assert "jupiter" in blob and "fill" in blob
    neg = pack.negative_prompt.lower()
    assert "underexposed overall scene" in neg or "underexposed" in neg
    assert "muddy crushed shadows" in neg or "muddy" in neg
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


def test_mercury_neptune_clean_refs_mode_short_prompt_without_legacy_hardlocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
        ApprovedPlanetReferenceEntry,
        write_planet_registry_entries,
    )
    from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
        CATSTYLE_CLEAN_REFS_PROFILE_KEY,
        CLEAN_REFERENCE_ROLES_BLOCK,
    )
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    reg = tmp_path / "approved_planet_references.json"
    neptune_png = tmp_path / "neptune.png"
    mercury_png = tmp_path / "mercury.png"
    neptune_png.write_bytes(b"n")
    mercury_png.write_bytes(b"m")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="neptune_v1",
                planet="Neptune",
                image_path=str(neptune_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="mercury_v1",
                planet="Mercury",
                image_path=str(mercury_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    clean = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mercury",
            planet_b="Neptune",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            use_planet_reference_auto=True,
            render_style_profile_key="premium_cg_keyart_v1",
            clean_refs_mode=True,
            premium_art_direction=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    full = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mercury",
            planet_b="Neptune",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            use_planet_reference_auto=True,
            render_style_profile_key="premium_cg_keyart_v1",
        )
    )
    clean_blob = clean.image_prompts[0]
    full_blob = full.image_prompts[0]
    clean_low = clean_blob.lower()
    assert CLEAN_REFERENCE_ROLES_BLOCK.split("]")[0] + "]" in clean_blob
    assert "mercury" in clean_low
    assert "neptune" in clean_low
    assert "square" in clean_low
    assert "[arena opulence hardlock v1]" in clean_low
    assert "[true premium cgi render hardlock v1]" in clean_low
    assert "high-end cinematic 3d cgi key art" in clean_low
    assert "central clash" in clean_low or "central rupture" in clean_low
    assert "tide/mist" in clean_low or "dissolving wave-force" in clean_low
    assert "[catstyle planet reference identity hardlock" not in clean_low
    assert "[catstyle visual composition hardlock" not in clean_low
    assert "[tense aspect choreography v2" not in clean_low
    assert "canon v1 base" not in clean_low
    assert "sun-uranus" not in clean_low
    assert "corona flare" not in clean_low
    assert "lightning zig" not in clean_low
    assert "do not turn mercury into sun" in clean_low
    assert "flat monochrome blue fur" in clean_low or "water-elemental" in clean_low
    assert len(clean_blob) < len(full_blob) * 0.35
    from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import CLEAN_PROMPT_MAX_CHARS

    assert len(clean_blob) <= CLEAN_PROMPT_MAX_CHARS


def test_mercury_neptune_clean_prompt_includes_contrast_block_under_budget() -> None:
    from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
        CLEAN_PROMPT_MAX_CHARS,
        build_clean_refs_image_prompt,
    )
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    prompt = build_clean_refs_image_prompt("Mercury", "Neptune", "square", "tension")
    low = prompt.lower()
    assert "sibling blue-gray mage cats" in low or "not sibling" in low
    assert "[mercury vs neptune contrast]" in low
    assert "[neptune scale / presence]" in low
    assert "not smaller than mercury" in low
    assert "equal/larger presence" in low or "equal or slightly larger" in low
    assert "oceanic aura" in low
    assert "vast" in low and "mythic" in low
    assert "visible central rupture" in low or "central clash" in low
    assert "polite magical exchange" in low
    assert "signal" in low and "tide" in low and "mist" in low
    assert "generic blue cat" in low or "generic blue neptune" in low or "blue-mascot neptune" in low
    assert "[arena opulence hardlock v1]" in low
    assert "[arena lighting richness v1]" in low
    assert "[arena scale dominance v3]" in low
    assert "warm golden torchlight" in low
    assert "monumental" in low
    assert "[true premium cgi render hardlock v1]" in low
    assert "high-end cinematic 3d cgi key art" in low
    assert "physically based rendering" in low
    assert "pbr" in low
    assert "[zodiac floor hardlock v2]" in low
    assert "only real zodiac glyphs" in low
    assert "aries through pisces" in low
    assert "35–65%" in low
    assert "extends beyond" in low
    assert "not small magic disc" in low or "not a small" in low
    assert "[neptune material fidelity]" in low
    assert "flat solid-blue water mascot" in low
    assert "no arena or full-scene image refs" in low
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
    assert "style hardlock cg" not in low
    assert "catstyle visual composition hardlock" not in low
    assert "tense aspect choreography" not in low

    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mercury",
            planet_b="Neptune",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            clean_refs_mode=True,
            use_planet_reference_auto=False,
        )
    )
    assert len(pack.image_prompts[0]) <= CLEAN_PROMPT_MAX_CHARS
    neg = pack.negative_prompt.lower()
    assert "tiny neptune" in neg
    assert "neptune smaller than mercury" in neg
    assert "sidekick neptune" in neg
    assert "small blue cat" in neg


def test_clean_refs_text_only_arena_blocks_without_arena_image() -> None:
    from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
        CLEAN_PROMPT_MAX_CHARS,
        build_clean_refs_image_prompt,
        generate_catstyle_clean_refs_prompt_pack,
    )
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    prompt = build_clean_refs_image_prompt("Saturn", "Venus", "square", "tension")
    low = prompt.lower()
    assert "[arena opulence hardlock v1]" in low
    assert "[arena scale dominance v3]" in low
    assert "[true premium cgi render hardlock v1]" in low
    assert "[zodiac floor hardlock v2]" in low
    assert "35–65%" in low
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS

    pack = generate_catstyle_clean_refs_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            disable_arena_reference_auto=True,
        )
    )
    assert "[arena opulence hardlock v1]" in pack.image_prompts[0].lower()


def test_build_jobs_clean_refs_mode_reference_order_without_pair_style(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import date
    import json

    from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import CLEAN_PROMPT_MAX_CHARS
    from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
        APPROVED_PLANET_REFERENCE_LOCK_MARKER,
        ApprovedPlanetReferenceEntry,
        write_planet_registry_entries,
    )
    from astro_content_agent.services.content.catstyle_image_generation_jobs import (
        build_catstyle_image_generation_jobs,
    )

    reg = tmp_path / "approved_planet_references.json"
    mercury_png = tmp_path / "mercury.png"
    neptune_png = tmp_path / "neptune.png"
    pair_png = tmp_path / "pair.png"
    for p in (mercury_png, neptune_png, pair_png):
        p.write_bytes(b"x")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="mercury_v1",
                planet="Mercury",
                image_path=str(mercury_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="neptune_v1",
                planet="Neptune",
                image_path=str(neptune_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    monkeypatch.setattr(
        "astro_content_agent.services.content.catstyle_image_generation_jobs._resolve_final_style_reference",
        lambda **kwargs: (str(pair_png.resolve()), {"source": "explicit"}),
    )
    out = tmp_path / "jobs"
    r = build_catstyle_image_generation_jobs(
        date(2026, 6, 1),
        output_dir=out,
        planet_a_override="Mercury",
        planet_b_override="Neptune",
        aspect_type_override="square",
        mode_override="tension",
        render_style_profile_key="premium_cg_keyart_v1",
        shot_mode="epic_arena_showdown",
        clean_refs_mode=True,
        use_planet_reference_auto=True,
        jobs_count=1,
    )
    job = r.jobs[0]
    prompt_file = (out / "job_01_prompt.txt").read_text(encoding="utf-8").strip()
    assert prompt_file == job.prompt_text.strip()
    low = prompt_file.lower()
    assert len(prompt_file) <= CLEAN_PROMPT_MAX_CHARS
    assert "[arena opulence hardlock v1]" in low
    assert "[arena lighting richness v1]" in low
    assert "[true premium cgi render hardlock v1]" in low
    assert "[zodiac floor hardlock v2]" in low
    assert "only real zodiac glyphs" in low
    assert "35–65%" in low
    assert "extends beyond" in low
    assert "[square conflict law v1]" in low
    assert "central clash" in low or "central rupture" in low
    assert "polite magical exchange" in low
    assert "tide/mist" in low or "dissolving wave-force" in low
    assert "sibling blue-gray mage cats" in low or "not sibling" in low
    assert "signal" in low and "tide" in low and "mist" in low
    assert "[REFERENCE ROLES]" in prompt_file
    assert "mercury" in low
    assert "neptune" in low
    assert APPROVED_PLANET_REFERENCE_LOCK_MARKER not in prompt_file
    assert "style hardlock cg" not in low
    assert "render style v1" not in low
    assert "catstyle approved arena reference" not in low
    assert "catplanet body identity" not in low
    assert "cosmic zodiac arena premium environment" not in low
    assert "catstyle visual composition hardlock" not in low
    assert "tense aspect choreography" not in low
    assert "world template" not in low
    assert "scene beat" not in low
    assert "catstyle global quality lock" not in low
    assert "catstyle planet reference override" not in low
    assert "pair/style reference is active" not in low
    assert [row["role"] for row in job.reference_images] == ["planet_a", "planet_b"]
    assert job.arena_reference_image_path is None
    assert job.render_style_profile_key == "catstyle_clean_refs_v1"
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["clean_refs_mode"] is True
    assert manifest.get("arena_reference", {}).get("clean_refs_text_only_arena") is True
    assert manifest.get("arena_reference", {}).get("arena_reference_used") is False

