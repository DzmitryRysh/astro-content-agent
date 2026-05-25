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
    "[SUN CATPLANET BODY LOCK v3] Sun = **living solar-core cat-planet**—**powerful, fiery, premium** (approved-reference spirit), "
    "NOT a normal orange furry cat. **Molten plasma / star-surface** with **glowing orange-gold** celestial glow; "
    "**corona halo** integrated in silhouette; **staff** and **strong solar energy presence** at poster scale. "
    "Armor/trim secondary on solar body—**no chest emblem clutter**. "
    "Reject weak cute orange tabby, soft fur mascot, costume-first Leo cosplay."
)

URANUS_CATPLANET_BODY_LOCK_BLOCK: Final[str] = (
    "[URANUS CATPLANET BODY LOCK v5] Uranus = **bright cyan ice-gas atmospheric cat-planet** (approved-reference spirit), "
    "NOT normal blue fur, **NOT** soft plush / rounded toy-like mascot, **NO leather jacket**. Body reads as **brighter cyan "
    "planetary atmosphere** with **subtle gas bands / cloud layers**, **strong electric / lightning rings** and **dramatic "
    "orbiting stones/debris** (floating rocks, tech shards—reference spectacle, non-glyph), violet-cyan energy arcs. "
    "**Sci-fi rebel genius disruptor**—powerful, intense, **not plush**. "
    "Reject plush rounded softness, dull muted blue fur, mascot cuddliness, striped-tiger palette, naked/plain disruptor."
)

URANUS_INVENTOR_GENIUS_BLOCK: Final[str] = (
    "[URANUS INVENTOR GENIUS v4] Uranus = **sci-fi rebel genius / disruptor** with **approved-reference spectacle**. "
    "**Paint clearly:** **strong electric / lightning rings** around the body; **dramatic floating stones and debris** "
    "orbiting Uranus (stones, rock chunks, plus magnetic gadget shards / tech fragments); **Tesla-coil / magnetic field** "
    "energy woven into bright cyan ice-gas. **Powerful, tech-rebel, visually impressive**—NOT soft plush. "
    "♅ right blue banner only—no body glyphs."
)

URANUS_REFERENCE_SPECTACLE_BLOCK: Final[str] = (
    "[URANUS REFERENCE SPECTACLE v2] **Approved reference = visual target.** Match its **brighter cyan/blue** atmospheric body, "
    "**strong electric / lightning rings**, **dramatic orbiting stones/debris**, intense rebel-genius face, tech hardware "
    "(cuffs, harness). **Reject leather jacket.** **Do NOT** copy reference body glyphs—♅ **right blue banner only**; "
    "minimize extra glyph clutter on bodies."
)

URANUS_REBEL_GENIUS_ACCESSORY_LOCK_BLOCK: Final[str] = (
    "[URANUS REBEL GENIUS ACCESSORY LOCK v7 — NON-OPTIONAL] Uranus = **hard-edged electric punk genius / anarchist inventor** "
    "with **reference-style premium spectacle** (see **[URANUS REFERENCE SPECTACLE v2]**, **[URANUS INVENTOR GENIUS v4]**)—"
    "**NO leather jacket**. NOT soft/plush/toy-like, **NOT** a single lonely cuff. "
    "**Rich tech hardware silhouette (bright cyan ice-gas body):** **multiple visible asymmetrical wrist cuffs / bracelets** "
    "(clearly two+ charged forearm cuffs); **heavy collar / harness** as **NON-GLYPH** industrial design "
    "(thick rings, buckles, conduit plates, magnetic lugs, shoulder yoke—no medallion disks, no planetary marks); "
    "**portal-tech / magnetic / industrial band** details; **hoop earring attached to the ear** when visible "
    "(never floating). **Strong electric / lightning rings** and **dramatic orbiting stones/debris** (charged bands, orbit glow). "
    "**do NOT** inherit Uranus glyph / emblem on chest, collar, harness, medallion, accessory, or body. "
    "**Accessory glyph ban:** no ♅/☉/♄ or any planetary / zodiac glyph on jewelry, cuffs, harness, or body. "
    "Reject plush toy Uranus, leather jacket on uranus, detached earrings, weak minimalist hardware, chest-badge disks."
)

URANUS_HARD_EDGED_ATTITUDE_BLOCK: Final[str] = (
    "[URANUS HARD-EDGED ATTITUDE v2] Push Uranus **away from soft plush mascot** toward **dangerous anarchist inventor-genius** "
    "reads: **angular face**, **sharper cheek/jaw planes**, **intense mad-scientist eyes**, **cocky experimental energy**—"
    "paired with **dense punk-tech hardware** (collar/harness, cuffs, Tesla/magnetic accents), **not** a cuddly blue pet."
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
    return " ".join(
        (
            SUN_CATPLANET_BODY_LOCK_BLOCK,
            URANUS_CATPLANET_BODY_LOCK_BLOCK,
            URANUS_REFERENCE_SPECTACLE_BLOCK,
            URANUS_REBEL_GENIUS_ACCESSORY_LOCK_BLOCK,
            URANUS_INVENTOR_GENIUS_BLOCK,
            URANUS_HARD_EDGED_ATTITUDE_BLOCK,
        )
    ).strip()


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
    "URANUS_HARD_EDGED_ATTITUDE_BLOCK",
    "URANUS_INVENTOR_GENIUS_BLOCK",
    "URANUS_REFERENCE_SPECTACLE_BLOCK",
    "URANUS_REBEL_GENIUS_ACCESSORY_LOCK_BLOCK",
    "catplanet_core_body_blocks",
    "is_sun_uranus_pair",
    "sun_uranus_body_and_flag_lock_blocks",
    "sun_uranus_catplanet_body_lock_blocks",
]
