"""Sun/Uranus visual refinement locks — prompt and approved-reference decoupling."""
from __future__ import annotations

from astro_content_agent.content.catstyle.approved_reference_prompt_lock_v1 import (
    build_approved_reference_prompt_lock_text,
)
from astro_content_agent.content.catstyle.approved_reference_registry import (
    ResolvedApprovedReference,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.content.catstyle.catplanet_body_identity_lock_v1 import (
    URANUS_HARD_EDGED_ATTITUDE_BLOCK,
    URANUS_INVENTOR_GENIUS_BLOCK,
    URANUS_REFERENCE_SPECTACLE_BLOCK,
    URANUS_REBEL_GENIUS_ACCESSORY_LOCK_BLOCK,
)
from astro_content_agent.content.catstyle.banner_glyph_reference_v1 import (
    banner_only_prompt_forbidden_phrases,
)
from astro_content_agent.content.catstyle.sun_uranus_hard_art_direction_override_v1 import (
    SUN_URANUS_HARD_ART_DIRECTION_OVERRIDE_BLOCK,
)
from astro_content_agent.content.catstyle.cosmic_zodiac_arena_premium_environment_v1 import (
    cosmic_zodiac_arena_premium_environment_blocks,
)
from astro_content_agent.content.catstyle.sun_uranus_visual_refinement_v1 import (
    BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK,
    BODY_GLYPH_REJECTION_BLOCK,
    COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK,
    SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK,
    SUN_URANUS_VISUAL_REFINEMENT_NEGATIVE_EXTRAS,
    sun_uranus_visual_refinement_blocks,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _sun_uranus_pack(*, disable_approved: bool = False) -> str:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_comic_poster_v2",
            shot_mode="epic_arena_showdown",
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=disable_approved,
        )
    )
    return "\n".join(pack.image_prompts)


def test_refinement_module_blocks_present() -> None:
    blob = sun_uranus_visual_refinement_blocks()
    assert BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK in blob
    assert SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK in blob
    assert COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK in blob
    assert URANUS_REBEL_GENIUS_ACCESSORY_LOCK_BLOCK in blob
    assert "body emblems" in blob.lower()
    assert "cosmic zodiac arena premium environment v1" in blob.lower()
    assert URANUS_HARD_EDGED_ATTITUDE_BLOCK in blob
    assert "illuminated arches" in cosmic_zodiac_arena_premium_environment_blocks().lower()


def test_sun_banner_glyph_rejects_hollow_ring_and_requires_filled_center_dot() -> None:
    low = SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK.lower()
    assert "non-optional" in low
    assert "filled central dot" in low or "filled central" in low
    assert "solid" in low and "opaque" in low
    assert "hollow ring" in low
    assert "empty circle" in low
    assert "letter o" in low or "letter **o**" in low
    assert "missing center dot" in low
    assert "instagram" in low or "mobile" in low


def test_uranus_rebel_genius_accessory_lock_non_glyph_punk_tech() -> None:
    low = URANUS_REBEL_GENIUS_ACCESSORY_LOCK_BLOCK.lower()
    assert "rebel genius" in low or "anarchist rebel" in low
    assert "wrist" in low and ("cuff" in low or "bracelet" in low)
    assert "two+" in URANUS_REBEL_GENIUS_ACCESSORY_LOCK_BLOCK or "two visible" in low or "multiple" in low
    assert "collar" in low and "harness" in low
    assert "hoop earring" in low
    assert "attached to the ear" in low or "physically attached" in low
    assert "never floating" in low or "not floating" in low
    assert "portal-tech" in low or "magnetic cuff" in low or "tech-strap" in low
    assert "reference" in low and ("spectacle" in low or "premium spectacle" in low)
    assert "hardware silhouette" in low
    assert "do not" in low and "inherit" in low and ("glyph" in low or "emblem" in low)
    assert "accessory glyph ban" in low
    assert "not** contain" in low or "any planetary" in low
    assert "bright cyan" in low or "ice-gas" in low
    assert "hard-edged" in low or "industrial" in low
    assert "stamp-zone" not in low
    assert "emblem zone" not in low
    assert "no medallion" in low
    assert "plush" in low or "soft" in low
    assert "angular" in low or "hard-edged" in low


def test_hard_art_direction_override_reference_spectacle_no_jacket() -> None:
    low = SUN_URANUS_HARD_ART_DIRECTION_OVERRIDE_BLOCK.lower()
    assert "approved reference target" in low or "approved reference" in low
    assert "no leather jacket" in low
    assert "floating stones" in low or "orbiting" in low and "debris" in low
    assert "lightning rings" in low or "electric" in low and "rings" in low
    assert "cosmic zodiac arena premium environment" in low
    assert "semicircle" in low or "flat semicircle" in low
    assert "filled central dot" in low
    assert "staff" in low
    assert "orange sun vs blue uranus" in low or ("orange" in low and "uranus" in low)


def test_prompt_drops_leather_jacket_direction() -> None:
    blob = sun_uranus_visual_refinement_blocks().lower()
    assert "reject leather jacket" in blob or "no leather jacket" in blob
    assert "must wear" not in blob or "open cropped leather jacket" not in blob
    assert URANUS_REFERENCE_SPECTACLE_BLOCK.lower() in blob
    assert "leather jacket" in blob  # only as reject


def test_uranus_reference_spectacle_electric_rings_no_glyph() -> None:
    low = URANUS_REFERENCE_SPECTACLE_BLOCK.lower()
    assert "visual target" in low or "approved reference" in low
    assert "reject leather jacket" in low
    assert "lightning rings" in low or "electric" in low and "rings" in low
    assert "stones" in low or "debris" in low
    assert "banner" in low and "glyph" in low


def test_uranus_inventor_genius_anti_gravity_tesla_tech() -> None:
    low = URANUS_INVENTOR_GENIUS_BLOCK.lower()
    assert "v4" in low
    assert "rebel genius" in low or "disruptor" in low
    assert "floating stones" in low or "stones" in low and "debris" in low
    assert "lightning rings" in low or "electric" in low and "rings" in low
    assert "tesla" in low or "magnetic" in low
    assert "not soft plush" in low or "not" in low and "plush" in low
    assert "banner" in low and "glyph" in low


def test_cosmic_environment_lock_delegates_to_reusable_baseline() -> None:
    low = COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK.lower()
    assert "v5" in low
    assert "cosmic zodiac arena premium environment v1" in low
    assert "semicircle" in low


def test_sun_uranus_assembled_prompt_uses_reusable_premium_environment() -> None:
    low = _sun_uranus_pack(disable_approved=True).lower()
    assert "[cosmic zodiac arena premium environment v1]" in low
    assert "[cosmic zodiac arena premium coliseum v1]" in low
    assert "[cosmic zodiac arena premium sky v1]" in low
    assert "colorful milky way" in low or "galaxy band" in low
    assert "illuminated arches" in low


def test_refinement_blocks_include_hard_override_first() -> None:
    blob = sun_uranus_visual_refinement_blocks()
    assert SUN_URANUS_HARD_ART_DIRECTION_OVERRIDE_BLOCK in blob
    assert blob.index(SUN_URANUS_HARD_ART_DIRECTION_OVERRIDE_BLOCK) < blob.index(
        BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK
    )


def test_sun_uranus_premium_cg_reference_spectacle_art_direction() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_cg_keyart_v1",
            shot_mode="epic_arena_showdown",
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    low = "\n".join(pack.image_prompts).lower()
    assert "[sun-uranus hard art-direction override v3" in low
    assert "no leather jacket" in low or ("reject" in low and "leather jacket" in low)
    assert "must wear" not in low or "open cropped leather jacket" not in low
    assert "[uranus reference spectacle v2]" in low
    assert "[uranus inventor genius v4" in low
    assert "lightning rings" in low or ("electric" in low and "rings" in low)
    assert "floating stones" in low or "orbiting" in low
    assert "[cosmic zodiac arena premium sky v1]" in low
    assert "[cosmic zodiac arena premium coliseum v1]" in low
    assert "brighter" in low and "coliseum" in low
    assert "illuminated" in low or "asymmetry" in low
    assert "[sun-uranus premium spectacle composition v1]" in low
    assert "[body glyph rejection v2]" in low
    assert "banner cloth only" in low or "right/starboard" in low
    assert "filled central dot" in low
    assert banner_only_prompt_forbidden_phrases("\n".join(pack.image_prompts)) == []


def test_sun_uranus_premium_cg_prompt_includes_sky_richness_block() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_cg_keyart_v1",
            shot_mode="epic_arena_showdown",
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    low = "\n".join(pack.image_prompts).lower()
    assert "[cosmic zodiac arena premium sky v1]" in low
    assert "[uranus inventor genius v4]" in low
    assert "tesla" in low or "magnetic" in low
    assert "floating stones" in low or "orbiting" in low
    assert "banner cloth only" in low or "right/starboard" in low
    assert "colorful milky way" in low or "galaxy band" in low
    assert "earth" in low
    assert "[uranus reference spectacle v2]" in low
    assert "reject leather jacket" in low or "no leather jacket" in low
    assert "[uranus rebel genius accessory lock v7" in low
    assert "filled central dot" in low


def test_reusable_baseline_module_matches_sun_uranus_environment_intent() -> None:
    low = cosmic_zodiac_arena_premium_environment_blocks().lower()
    assert "illuminated arches" in low
    assert "colorful milky way" in low or "galaxy band" in low
    assert "electric rings" in low or "orbit halo" in low
    assert "premium coliseum" in low


def test_uranus_hard_edged_attitude_rejects_plush_mascot() -> None:
    low = URANUS_HARD_EDGED_ATTITUDE_BLOCK.lower()
    assert "plush" in low
    assert "angular" in low or "sharper" in low
    assert "inventor" in low or "anarchist" in low or "rebel" in low
    assert "harness" in low or "collar" in low
    assert "tesla" in low or "magnetic" in low


def test_banner_decoupling_matches_uranus_hardware_without_glyph_inheritance() -> None:
    low = BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK.lower()
    assert "accessory richness" in low
    assert "hardware silhouette" in low
    assert "collar" in low and "harness" in low
    assert "do not" in low and "inherit" in low
    assert "chest" in low and "harness" in low
    assert "right/starboard" in low or "right/starboard (uranus)" in low
    assert "left/port" in low or "left/port (sun)" in low


def test_sun_uranus_refinement_negative_extras_sun_dot_and_uranus_accessories() -> None:
    joined = ", ".join(SUN_URANUS_VISUAL_REFINEMENT_NEGATIVE_EXTRAS).lower()
    assert "hollow sun" in joined
    assert "missing filled central dot" in joined or "hollow sun ring" in joined
    assert "floating detached hoop earring" in joined
    assert "single wrist band" in joined
    assert "planetary glyph on accessories" in joined or "uranus glyph on hoop" in joined
    assert "plush" in joined or "toy-like" in joined or "leather jacket" in joined


def test_body_glyph_rejection_forbids_glyphs_on_accessories() -> None:
    low = BODY_GLYPH_REJECTION_BLOCK.lower()
    assert "accessories" in low
    assert "banner cloth only" in low or "banner only" in low
    assert "hoop" in low or "wrist" in low


def test_sun_uranus_assembled_prompt_refinement_locks() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_comic_poster_v2",
            shot_mode="epic_arena_showdown",
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    low = "\n".join(pack.image_prompts).lower()
    assert "[banner-only approved reference decoupling v2]" in low
    assert "accessory richness" in low
    assert "hardware silhouette" in low
    assert "[body glyph rejection v2]" in low
    assert "[sun banner glyph hardening v2" in low
    assert "filled central dot" in low
    assert "hollow ring" in low
    assert "[cosmic environment power lock v5" in low
    assert "[cosmic zodiac arena premium coliseum v1]" in low
    assert "many stars" in low or "starfield" in low
    assert "colorful milky way" in low or "galaxy band" in low
    assert "[uranus inventor genius v4]" in low
    assert "[uranus hard-edged attitude v2]" in low
    assert "plush" in low or "toy-like" in low
    assert "angular" in low or "hard-edged" in low
    assert "central dot" in low
    assert "phone" in low or "instagram" in low
    assert "[uranus reference spectacle v2]" in low
    assert "reject leather jacket" in low or "no leather jacket" in low
    assert "[uranus rebel genius accessory lock v7" in low
    assert "collar" in low and "harness" in low
    assert "floating" in low and "hoop" in low
    assert "starfield" in low
    assert "nebula" in low
    assert "monumental" in low and "coliseum" in low
    assert "earth disk" in low or "earth above" in low
    assert "zodiac floor" in low or "zodiac wheel" in low
    assert "torso" in low or "chest" in low
    assert "collar" in low
    assert "uranus" in low and ("off-banner" in low or "banner cloth only" in low or "right/starboard" in low)
    assert "glyph on torso" in low or "zero" in low and "glyph" in low


def test_sun_uranus_prompt_forbids_body_glyph_attractors() -> None:
    low = _sun_uranus_pack().lower()
    assert "glyph on torso" in low or "zero" in low and "planetary glyphs on torso" in low
    assert "chest symbols" in low or "chest" in low and "collar symbols" in low
    assert "medallion-like" in low or "medallion" not in low


def test_sun_uranus_premium_cg_dense_sky_and_hard_edged_uranus() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_cg_keyart_v1",
            shot_mode="epic_arena_showdown",
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    low = "\n".join(pack.image_prompts).lower()
    assert "[cosmic environment power lock v5" in low
    assert "[cosmic zodiac arena premium coliseum v1]" in low
    assert "many stars" in low or "starfield" in low
    assert "colorful milky way" in low or "galaxy band" in low
    assert "nebula" in low
    assert "[uranus inventor genius v4]" in low
    assert "[uranus hard-edged attitude v2]" in low
    assert "plush" in low or "toy-like" in low
    assert "banner cloth only" in low or "right/starboard" in low
    assert "filled central dot" in low


def test_sun_uranus_premium_cg_includes_uranus_rebel_accessories() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_cg_keyart_v1",
            shot_mode="epic_arena_showdown",
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    joined = "\n".join(pack.image_prompts)
    low = joined.lower()
    assert "[uranus reference spectacle v2]" in low
    assert "reject leather jacket" in low or "no leather jacket" in low
    assert "[uranus rebel genius accessory lock v7" in low
    assert "collar" in low and "harness" in low
    assert "hoop earring" in low
    assert "attached to the ear" in low or "physically attached" in low
    assert "wrist" in low and ("cuff" in low or "bracelet" in low)
    assert "two" in low and ("cuff" in low or "bracelet" in low or "arms" in low)
    assert "magnetic cuff" in low or "tech strap" in low
    assert "portal-tech" in low
    assert "accessory glyph ban" in low
    assert "not** contain" in low or "any planetary" in low
    assert "ice-gas" in low
    assert "central dot" in low
    assert "right/starboard" in low
    assert banner_only_prompt_forbidden_phrases(joined) == []
    assert "medallion" not in low
    assert "stamp-zone" not in low


def test_approved_reference_lock_includes_decoupling_for_sun_uranus() -> None:
    hit = ResolvedApprovedReference(
        registry_key="sun_uranus_conjunction_tension",
        image_path="references/approved/sun_uranus.png",
        label="Sun/Uranus conjunction tension",
        notes="test",
        priority=100,
    )
    lock = build_approved_reference_prompt_lock_text(
        hit, "Sun", "Uranus", "conjunction", "tension"
    )
    assert BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK in lock
    assert "do not" in lock.lower() and "body emblems" in lock.lower()


def test_sun_uranus_with_approved_lock_still_has_refinement() -> None:
    low = _sun_uranus_pack(disable_approved=False).lower()
    assert "[banner-only approved reference decoupling v2]" in low
    assert "accessory richness" in low
    assert "hardware silhouette" in low
    assert "layered starfield" in low or "starfield" in low
