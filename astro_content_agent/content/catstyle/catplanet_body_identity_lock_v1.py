"""Catplanet body identity and Sun/Uranus pair-specific body locks (visual fidelity)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

CATPLANET_BODY_IDENTITY_LOCK_BLOCK: Final[str] = (
    "[CATPLANET BODY IDENTITY LOCK v2] **Non-negotiable:** fighters are **anthropomorphic cat-planets**—"
    "**living planetary bodies** with feline anatomy, **NOT ordinary furry cats in costumes** and **NOT "
    "costume-first mascots with elemental VFX pasted on**. "
    "**Primary read = planetary body material:** star-surface, ice-gas atmosphere, molten core, gas bands, "
    "aurora, corona-integrated silhouette—**surface texture and glow carry identity before fur, cloth, or props**. "
    "Reject plush tabby/soft-fur dominance, generic orange or blue pet cats, mascot simplification, and "
    "weak planet texture hidden under armor."
)

CATPLANET_BODY_PRIORITY_BLOCK: Final[str] = (
    "[CATPLANET BODY PRIORITY v1] **Render hierarchy:** (1) **planetary body material + aura** (dominant), "
    "(2) face, paws, pose, silhouette, (3) minimal costume trim that **follows** the body surface—"
    "(4) faction banners with cloth-integrated glyphs (**secondary**—never steal focus from catplanet bodies)."
)

CATPLANET_FLAGS_SECONDARY_BLOCK: Final[str] = (
    "[CATPLANET FLAGS SECONDARY v1] Keep faction banners and heraldic glyphs, but they are **supporting** "
    "identity cues—**catplanet body material must win** at thumbnail over flags, jewelry, or costume badges."
)

SUN_CATPLANET_BODY_LOCK_BLOCK: Final[str] = (
    "[SUN CATPLANET BODY LOCK v2] Sun = **living solar-core cat-planet**, NOT a normal orange furry cat. "
    "Body mass reads as **molten plasma / star-surface texture** with **glowing orange-gold celestial surface**; "
    "**corona halo integrated into body silhouette** (light from the star-body, not a separate fire effect). "
    "**Costume/armor is secondary trim** on solar body material—reduce cloth dominance; "
    "reject plush orange tabby, soft fur-first mascot, costume-first Leo cosplay, and fire VFX on ordinary fur."
)

URANUS_CATPLANET_BODY_LOCK_BLOCK: Final[str] = (
    "[URANUS CATPLANET BODY LOCK v2] Uranus = **cyan ice-gas atmospheric cat-planet**, NOT a normal blue furry cat. "
    "Body reads as **cyan ice-gas planetary atmosphere** with **subtle gas bands / cloud layers**, "
    "**tilted-axis orbital-field motif**, and **electric magnetic-field arcs** through volumetric surface. "
    "Orbital debris / fractured electric geometry allowed—reject plush fur, mascot softness, striped-tiger palette, "
    "and costume-first trickster cat with lightning stickers."
)

CATPLANET_BODY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "ordinary cats with effects",
    "ordinary furry cat",
    "furry cat with elemental effects",
    "costume-first mascot design",
    "costume dominates over planet body",
    "generic elemental cats",
    "orange tabby sun cat",
    "blue furry uranus cat",
    "plush fur dominance",
    "soft fur mascot body",
    "weak planet texture",
    "plush toy body",
    "mascot redraw",
    "normal cat in costume",
    "circular chest badge",
    "collar medallion disk",
    "round torso emblem badge",
)


def is_sun_uranus_pair(planet_a: str, planet_b: str) -> bool:
    return {normalize_planet_name(planet_a), normalize_planet_name(planet_b)} == {"Sun", "Uranus"}


def catplanet_core_body_blocks() -> str:
    """Global catplanet DNA blocks for every Catstyle pair image prompt."""
    return " ".join(
        (
            CATPLANET_BODY_IDENTITY_LOCK_BLOCK,
            CATPLANET_BODY_PRIORITY_BLOCK,
            CATPLANET_FLAGS_SECONDARY_BLOCK,
        )
    ).strip()


def sun_uranus_catplanet_body_lock_blocks() -> str:
    """Sun + Uranus planetary-surface locks (any aspect when pair is Sun/Uranus)."""
    return " ".join((SUN_CATPLANET_BODY_LOCK_BLOCK, URANUS_CATPLANET_BODY_LOCK_BLOCK)).strip()


def sun_uranus_body_and_flag_lock_blocks() -> str:
    """Backward-compatible alias: body locks only (flag fidelity lives in flag_glyph_fidelity_lock_v1)."""
    return sun_uranus_catplanet_body_lock_blocks()


__all__ = [
    "CATPLANET_BODY_IDENTITY_LOCK_BLOCK",
    "CATPLANET_BODY_NEGATIVE_EXTRAS",
    "CATPLANET_BODY_PRIORITY_BLOCK",
    "CATPLANET_FLAGS_SECONDARY_BLOCK",
    "SUN_CATPLANET_BODY_LOCK_BLOCK",
    "URANUS_CATPLANET_BODY_LOCK_BLOCK",
    "catplanet_core_body_blocks",
    "is_sun_uranus_pair",
    "sun_uranus_body_and_flag_lock_blocks",
    "sun_uranus_catplanet_body_lock_blocks",
]
