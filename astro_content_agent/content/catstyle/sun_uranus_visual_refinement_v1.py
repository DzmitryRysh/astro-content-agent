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
from astro_content_agent.content.catstyle.sun_uranus_hard_art_direction_override_v1 import (
    SUN_URANUS_HARD_ART_DIRECTION_OVERRIDE_BLOCK,
)

BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK: Final[str] = (
    "[BANNER-ONLY APPROVED REFERENCE DECOUPLING v2] When an approved Sun/Uranus style reference is active, inherit **only** "
    "campaign **finish**: render density, premium CG/comic-poster polish, lighting contrast, character volume, "
    "scale, and overall world quality. **For Uranus:** match the reference's **accessory richness and hardware silhouette** "
    "(brighter cyan body, strong electric rings, tech hardware, inventor debris, anarchist rebel genius energy)—"
    "**do NOT** inherit any Uranus glyph / emblem / symbol on chest, collar, harness, medallion, accessory, or body. "
    "**Do NOT** inherit a **leather jacket** from the reference. "
    "**Do NOT** inherit from the reference: body emblems, chest symbols, collar glyph disks, torso glyphs, belt sigils, "
    "accessory marks, medallion-like signs, or any planetary glyph on characters. Banner cloth may inform **heraldic gold finish** "
    "only—canonical glyphs stay on **left/port (Sun)** and **right/starboard (Uranus)** faction banners per banner-only discipline."
)

BODY_GLYPH_REJECTION_BLOCK: Final[str] = (
    "[BODY GLYPH REJECTION v2] **Zero** planetary glyphs on torso, chest, collar, harness, belts, "
    "armor plates, jewelry, **punk/tech accessories** (wrist cuffs, hoop earrings, magnetic cuffs, "
    "portal-tech hardware, orbit fragments), body ornaments, or portal-hoop rims. **Especially reject** Uranus "
    "\u2645 (\u2645) or Sun \u2609 (\u2609) on body, collar, harness, **or on accessories**—glyphs stay **banner cloth only** "
    "(left/port Sun, right/starboard Uranus)—no reference-emblem behavior off-banner."
)

SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK: Final[str] = (
    "[SUN BANNER GLYPH HARDENING v2 — NON-OPTIONAL] **Left/port Sun banner ONLY:** paint canonical **\u2609 (\u2609)** "
    "as a **full circular ring WITH a clearly visible FILLED central dot**—the dot is **solid, opaque, and large** "
    "(occupying meaningful center mass inside the ring), **not** a pinhole, **not** implied, **not** optional. "
    "**High-priority reject:** hollow ring, empty circle, coin rim, letter **O**, zero / donut / washer shapes, "
    "missing center dot, partial arc, or crescent-only Sun mark. The filled central dot must survive generation and "
    "stay **readable at Instagram / mobile thumbnail scale**—largest clean heraldic mark on the Sun flag field."
)

COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK: Final[str] = (
    "[COSMIC ENVIRONMENT POWER LOCK v5 — DELEGATES TO BASELINE] Sun/Uranus scenes use the reusable "
    "**[COSMIC ZODIAC ARENA PREMIUM ENVIRONMENT v1]** baseline for coliseum, sky, and spectacle—do not drift to dark "
    "flat semicircle walls or sparse Earth-only sky."
)

SUN_URANUS_PREMIUM_SPECTACLE_COMPOSITION_BLOCK: Final[str] = (
    "[SUN-URANUS PREMIUM SPECTACLE COMPOSITION v1] Overall image: **brighter, richer, more premium, more cinematic** "
    "fantasy-cosmic poster—**strong contrast** between **orange-gold Sun energy** and **blue-cyan Uranus energy**. "
    "Preserve **epic-arena-showdown** staging and scale. **Minimize body glyph clutter**—☉ left red banner, ♅ right blue banner only."
)

SUN_URANUS_VISUAL_REFINEMENT_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "planetary glyph on chest or torso",
    "glyph on collar or regal collar",
    "Uranus glyph on body",
    "Sun glyph off left banner",
    "incomplete Sun glyph without central dot",
    "hollow sun ring without central dot",
    "hollow sun banner ring",
    "sun glyph empty circle or letter O",
    "missing filled central dot on sun banner",
    "floating detached hoop earring",
    "single wrist band only on uranus",
    "naked plain uranus without rebel accessories",
    "weak uranus without collar harness hardware",
    "uranus glyph on hoop earring or wrist band",
    "planetary glyph on accessories",
    "soft plush uranus cat",
    "rounded toy-like uranus",
    "generic floating rocks near uranus",
    "uranus without tesla or inventor energy",
    "leather jacket on uranus",
    "cropped leather biker jacket",
    "generic floating rocks only near uranus",
    "uranus collar only no leather jacket",
    "uranus generic electric fighter without inventor gear",
    "weak uranus electric rings",
    "uranus without orbiting debris or stones",
)


def sun_uranus_visual_refinement_blocks() -> str:
    """Focused locks for Sun/Uranus conjunction+tension (banner-only safe)."""
    return " ".join(
        (
            catplanet_core_body_blocks(),
            sun_uranus_catplanet_body_lock_blocks(),
            SUN_URANUS_HARD_ART_DIRECTION_OVERRIDE_BLOCK,
            BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK,
            BODY_GLYPH_REJECTION_BLOCK,
            SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK,
            COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK,
            SUN_URANUS_PREMIUM_SPECTACLE_COMPOSITION_BLOCK,
        )
    ).strip()


__all__ = [
    "BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK",
    "BODY_GLYPH_REJECTION_BLOCK",
    "COSMIC_ENVIRONMENT_POWER_LOCK_BLOCK",
    "SUN_URANUS_PREMIUM_SPECTACLE_COMPOSITION_BLOCK",
    "SUN_URANUS_HARD_ART_DIRECTION_OVERRIDE_BLOCK",
    "SUN_BANNER_GLYPH_PHONE_SCALE_BLOCK",
    "SUN_URANUS_VISUAL_REFINEMENT_NEGATIVE_EXTRAS",
    "is_sun_uranus_conjunction_tension",
    "sun_uranus_visual_refinement_blocks",
]
