"""Sun/Uranus conjunction+tension visual refinement (banner-only + approved-reference decoupling)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.catplanet_body_identity_lock_v1 import (
    catplanet_core_body_blocks,
    sun_uranus_catplanet_body_lock_blocks,
)
from astro_content_agent.content.catstyle.sun_uranus_conjunction_tension_canon_v1 import (
    is_sun_uranus_conjunction_tension,
)

BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK: Final[str] = (
    "[BANNER-ONLY APPROVED REFERENCE DECOUPLING v1] When an approved style reference is active, inherit **only** "
    "campaign **finish**: render density, premium CG/comic-poster polish, lighting contrast, character volume, "
    "scale, and overall world quality. **Do NOT** inherit from the reference: body emblems, chest symbols, "
    "collar symbols, torso glyphs, belt sigils, accessory marks, medallion-like signs, or any planetary glyph "
    "on characters. Banner cloth may inform **heraldic gold finish** only—canonical glyphs stay on "
    "**left/port (Sun)** and **right/starboard (Uranus)** faction banners per banner-only discipline."
)

BODY_GLYPH_REJECTION_BLOCK: Final[str] = (
    "[BODY GLYPH REJECTION v1] **Zero** planetary glyphs on torso, chest, collar, belts, "
    "armor plates, jewelry, accessories, body ornaments, or portal-hoop rims. **Especially reject** Uranus "
    "\u2645 (\u2645) or Sun \u2609 (\u2609) drift onto the body—no reference-emblem behavior off-banner."
)

SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK: Final[str] = (
    "[SUN BANNER GLYPH HARDENING v1] **Left/port Sun banner ONLY:** canonical \u2609 (\u2609) = **complete circular "
    "ring with a bold, clearly visible central dot** (not a hollow ring, not a partial arc, not a crescent). "
    "The central dot must remain **readable at phone / Instagram thumbnail scale**—largest clean heraldic "
    "mark on the Sun flag field."
)

COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK: Final[str] = (
    "[COSMIC ENVIRONMENT POWER LOCK v1] Sky: **visible layered starfield** plus **nebula depth** "
    "(milky void gradients, distant star clusters, cosmic glow—not empty flat black). Coliseum: **monumental "
    "cosmic arena** with readable **arches**, **stadium tiers**, **receding architecture**, and **midground "
    "wall depth**—not a flat dark backdrop slab. Preserve **Earth disk above the arena vault**; **zodiac floor** "
    "engraved and readable but subordinate to fighters, sky depth, and coliseum scale."
)

SUN_URANUS_VISUAL_REFINEMENT_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "planetary glyph on chest or torso",
    "glyph on collar or regal collar",
    "Uranus glyph on body",
    "Sun glyph off left banner",
    "incomplete Sun glyph without central dot",
    "hollow sun ring without central dot",
    "weak empty cosmic sky",
    "flat dark coliseum wall",
    "arena reads as flat backdrop",
    "no visible starfield",
    "no nebula depth",
    "body emblem copied from reference",
    "reference torso glyph drift",
)


def sun_uranus_visual_refinement_blocks() -> str:
    """Focused locks for Sun/Uranus conjunction+tension (banner-only safe)."""
    return " ".join(
        (
            catplanet_core_body_blocks(),
            sun_uranus_catplanet_body_lock_blocks(),
            BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK,
            BODY_GLYPH_REJECTION_BLOCK,
            SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK,
            COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK,
        )
    ).strip()


__all__ = [
    "BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK",
    "BODY_GLYPH_REJECTION_BLOCK",
    "COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK",
    "SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK",
    "SUN_URANUS_VISUAL_REFINEMENT_NEGATIVE_EXTRAS",
    "is_sun_uranus_conjunction_tension",
    "sun_uranus_visual_refinement_blocks",
]
