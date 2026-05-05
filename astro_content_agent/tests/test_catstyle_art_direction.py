"""Tests for deterministic Catstyle premium art-direction v0."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstylePromptPack
from astro_content_agent.services.content.catstyle_art_direction import (
    CatstyleArtDirectionProfile,
    apply_art_direction_to_prompt_pack,
    build_catstyle_art_direction_profile,
    compose_premium_catstyle_prompt,
    resolve_art_energy,
    strengthen_negative_prompt,
)


def test_resolve_art_energy_editorial_charged_overrides_mixed_mode() -> None:
    assert resolve_art_energy("charged", "mixed") == "charged"


def test_resolve_art_energy_editorial_supportive_overrides_tension_mode() -> None:
    assert resolve_art_energy("supportive", "tension") == "supportive"


def test_resolve_art_energy_balanced_uses_mode_tension() -> None:
    assert resolve_art_energy("balanced", "tension") == "charged"


def test_resolve_art_energy_balanced_uses_mode_compensation() -> None:
    assert resolve_art_energy("balanced", "compensation") == "supportive"


def test_resolve_art_energy_none_falls_through_mode() -> None:
    assert resolve_art_energy(None, "mixed") == "balanced"


def test_charged_profile_includes_action_language() -> None:
    prof = build_catstyle_art_direction_profile(
        editorial_profile="charged",
        mode="tension",
        planet_a="Jupiter",
        planet_b="Mars",
        skin_a=None,
        skin_b=None,
    )
    out = compose_premium_catstyle_prompt("BASE SEMANTIC PROMPT.", prof)
    low = out.lower()
    assert "premium comic direction" in low
    assert "scene energy (charged)" in low
    assert "dynamic action read" in low
    assert "meme/movie-archetype" in low


def test_supportive_profile_includes_collaboration_language() -> None:
    prof = build_catstyle_art_direction_profile(
        editorial_profile="supportive",
        mode="compensation",
        planet_a="Saturn",
        planet_b="Venus",
        skin_a=None,
        skin_b=None,
    )
    out = compose_premium_catstyle_prompt("BASE.", prof)
    low = out.lower()
    assert "scene energy (supportive)" in low
    assert "elegant collaboration" in low


def test_skin_block_emphasizes_hooks_and_is_scene_defining() -> None:
    prof = build_catstyle_art_direction_profile(
        editorial_profile="charged",
        mode="tension",
        planet_a="Jupiter",
        planet_b="Mars",
        skin_a="philosopher_mentor",
        skin_b="spartan_king",
    )
    out = compose_premium_catstyle_prompt("BASE.", prof)
    low = out.lower()
    assert "character skin mandate" in low
    assert "scene-defining overlays" in low
    assert "philosopher mentor" in low
    assert "spartan king" in low
    assert "cliff edge silhouette" in low or "wind dust" in low


def test_negative_prompt_strengthens_anti_bland() -> None:
    prof = CatstyleArtDirectionProfile(
        energy="charged",
        planet_a="Jupiter",
        planet_b="Mars",
        mode="tension",
        editorial_profile="charged",
        skin_a=None,
        skin_b=None,
    )
    neg = strengthen_negative_prompt("text, photorealistic", prof).lower()
    assert "bland mascot pose" in neg
    assert "sticker-like centered character" in neg
    assert "weak unclear interaction" in neg
    assert "babyish" in neg


def test_apply_pack_sets_art_direction_metadata() -> None:
    prof = build_catstyle_art_direction_profile(
        editorial_profile=None,
        mode="tension",
        planet_a="Jupiter",
        planet_b="Mars",
        skin_a=None,
        skin_b=None,
    )
    base = CatstylePromptPack(
        image_prompts=["p1"],
        animation_prompt="anim",
        negative_prompt="neg",
        carousel_idea="car",
        world_template_profile={"template_key": "cosmic_zodiac_arena"},
        scene_template_profile={"template_key": "mars_spartan_cliff_kick"},
    )
    enriched = apply_art_direction_to_prompt_pack(base, prof)
    assert enriched.art_direction_profile is not None
    assert enriched.art_direction_profile["version"] == "catstyle-art-direction-v0"
    assert enriched.art_direction_profile["energy"] == "charged"
    assert "Premium comic direction" in enriched.image_prompts[0]
    assert enriched.world_template_profile == base.world_template_profile
    assert enriched.scene_template_profile == base.scene_template_profile
    low = enriched.image_prompts[0].lower()
    assert "honor locked world shell" in low
    assert "honor locked scene_template_profile beat" in low


def test_compose_premium_respects_template_profiles_optional() -> None:
    prof = build_catstyle_art_direction_profile(
        editorial_profile="charged",
        mode="tension",
        planet_a="Jupiter",
        planet_b="Mars",
        skin_a=None,
        skin_b=None,
    )
    out = compose_premium_catstyle_prompt(
        "BASE.",
        prof,
        world_template_profile={"template_key": "cosmic_zodiac_arena"},
        scene_template_profile={"template_key": "mars_spartan_cliff_kick"},
    ).lower()
    assert "honor locked world shell" in out
    assert "honor locked scene_template_profile beat" in out
