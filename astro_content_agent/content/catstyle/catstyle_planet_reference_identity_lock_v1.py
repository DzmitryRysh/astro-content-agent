"""Strong per-planet identity enforcement when approved planet references are active (v1)."""
from __future__ import annotations

from typing import Any, Final

from astro_content_agent.content.catstyle.catstyle_aspect_staging_locks_v1 import (
    PLANET_CAT_BODY_MATERIAL_INTENSITY_BLOCK,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER: Final[str] = "[CATSTYLE PLANET REFERENCE IDENTITY HARDLOCK v1]"

PLANET_REFERENCE_IDENTITY_ENFORCEMENT_BODY: Final[str] = (
    "Approved per-planet image references are mandatory identity anchors—not soft suggestions. "
    "For each planet with an attached reference, lock and preserve from the reference image: "
    "face morphology and facial language, body material and surface treatment, costume silhouette, "
    "aura and energy language, palette, and overall archetypal identity. "
    "Do not simplify into a generic colored cat. Do not replace the approved planet-cat identity with a "
    "generic mage, warrior, fantasy cat trope, or stock RPG character. Do not revert to a normal house-cat face, "
    "ordinary pet-cat fur, or costume-first mascot. Aspect choreography may change pose and action only—"
    "never replace referenced identity."
)

NEPTUNE_ANTI_GENERIC_IDENTITY_BLOCK: Final[str] = (
    "[NEPTUNE ANTI-GENERIC IDENTITY v1] Neptune must not collapse into just a blue cat or plain blue furry pet. "
    "Preserve the approved Neptune reference identity: dreamlike, oceanic, abyssal, mystical; integrated water, "
    "vapor, and tide energy; complex layered material identity beyond flat blue fur; strong stylized Neptune "
    "face—not a generic domestic cat face."
)

NEPTUNE_PREMIUM_IDENTITY_HARDLOCK_BLOCK: Final[str] = (
    "[NEPTUNE PREMIUM IDENTITY HARDLOCK v2] When Neptune has an approved planet reference, preserve Neptune's "
    "specific reference identity: regal oceanic-cosmic feline, nuanced cool blue/cyan/silver palette, layered "
    "premium CGI materials with surface variation, refined face structure, trident/oceanic regal magic, costume "
    "and jewel detailing. Reject flat monochrome blue fur, generic elemental-water-cat design, simplified "
    "cartoon-blue body, blob-like glow mass, and over-saturated neon-blue rendering."
)

NEPTUNE_PREMIUM_IDENTITY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "generic blue cat",
    "solid monochrome blue body",
    "water elemental cat trope",
    "oversaturated neon-blue fur",
    "simple fantasy blue cat",
    "flat blue mascot look",
)

URANUS_REFERENCE_HARDLOCK_V2: Final[str] = (
    "[URANUS REFERENCE HARDLOCK v2] Match approved Uranus ref: slender cyan/turquoise cat; anti-gravity/levitation; "
    "visible orbital electric ring(s); crackling plasma energy; floating debris/rocks; sci-fi cosmic disruptor—not "
    "generic blue cat or Neptune water mage. Sharp cyan eyes; metallic bands; unstable motion. Keep orbital rings and "
    "anti-gravity identity visible in combat—do not ground flat or collapse to generic blue cat."
)

# Legacy export name used by full-stack identity layer and tests.
URANUS_FEATURE_HARDLOCK_BLOCK = URANUS_REFERENCE_HARDLOCK_V2

URANUS_FEATURE_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "normal blue cat Uranus",
    "generic blue cat",
    "Uranus standing flat on ground",
    "generic lightning cat",
    "neptune-like water mage uranus",
    "no orbital rings",
    "missing floating debris",
    "no anti-gravity pose",
    "simple blue fighter cat",
    "Uranus without spatial distortion",
    "generic fantasy costume drift",
)

_PLANET_SLOT_IDENTITY_BLOCKS: Final[dict[str, str]] = {
    "Sun": (
        "[PLANET A IDENTITY HARDLOCK — Sun] Lock from approved Sun reference: solar-core face morphology, "
        "molten star-surface body material, corona-integrated silhouette, golden authority aura, commanding "
        "costume logic; never generic orange tabby or ordinary pet cat."
    ),
    "Moon": (
        "[PLANET A IDENTITY HARDLOCK — Moon] Lock from approved Moon reference: pearlescent lunar face language, "
        "soft silver body material, crescent/tidal silhouette, intuitive emotional aura; never generic white "
        "plush house cat."
    ),
    "Mercury": (
        "[PLANET A IDENTITY HARDLOCK — Mercury] Lock from approved Mercury reference: quick clever face morphology, "
        "rocky gray-blue surface material, messenger/scribe costume silhouette, signal-glyph energy; never generic "
        "gray pet cat or stock trickster mage trope."
    ),
    "Venus": (
        "[PLANET A IDENTITY HARDLOCK — Venus] Lock from approved Venus reference: rose-glow facial language, "
        "beauty-force body material, elegant silhouette, magnetism/radiance aura, refined costume logic; never generic "
        "cute pink house cat or passive flower-holding mascot."
    ),
    "Mars": (
        "[PLANET A IDENTITY HARDLOCK — Mars] Lock from approved Mars reference: fierce warrior face read, "
        "volcanic/iron body material, combat-forward silhouette, flame-trail energy; never generic red tabby or "
        "stock brawler cat."
    ),
    "Jupiter": (
        "[PLANET A IDENTITY HARDLOCK — Jupiter] Lock from approved Jupiter reference: generous wise face morphology, "
        "banded gas-giant body material, expansive noble silhouette, auroral blessing-force aura; never generic "
        "fat orange cat or king costume cliché only."
    ),
    "Saturn": (
        "[PLANET A IDENTITY HARDLOCK — Saturn] Lock from approved Saturn reference: stern architectural face, "
        "stone/ringed body material, time-structure costume silhouette, cold gravity aura; never generic dark boss "
        "cat or fiery Mars-coded Saturn."
    ),
    "Uranus": (
        "[PLANET A IDENTITY HARDLOCK — Uranus] Lock from approved Uranus reference: electric rebel face planes, "
        "cyan ice-gas atmospheric body, asymmetrical tech silhouette, lightning-ring energy; never generic blue "
        "fur pet or leather-jacket humanoid cat."
    ),
    "Neptune": (
        "[PLANET A IDENTITY HARDLOCK — Neptune] Lock from approved Neptune reference: dream-mist face morphology, "
        "oceanic vapor/tide body material, abyssal mystical silhouette, integrated water-magic aura; never plain "
        "blue cat—see [NEPTUNE ANTI-GENERIC IDENTITY v1]."
    ),
    "Pluto": (
        "[PLANET A IDENTITY HARDLOCK — Pluto] Lock from approved Pluto reference: underworld-intense face, shadow "
        "mass body material, transformation-pressure silhouette, abyssal aura; never generic dark round cat or "
        "stock villain blob."
    ),
}

_PLANET_SLOT_IDENTITY_BLOCKS_B: Final[dict[str, str]] = {
    k: v.replace("PLANET A IDENTITY HARDLOCK", "PLANET B IDENTITY HARDLOCK", 1)
    for k, v in _PLANET_SLOT_IDENTITY_BLOCKS.items()
}

PLANET_REFERENCE_IDENTITY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "generic colored cat instead of planet-cat",
    "ordinary house-cat face on planet character",
    "generic mage cat trope replacing planet identity",
    "generic warrior fantasy cat trope",
    "stock RPG character cat",
    "costume-first mascot with weak planet read",
    "plain blue cat for Neptune",
    "neptune simplified to generic blue furry pet",
    *NEPTUNE_PREMIUM_IDENTITY_NEGATIVE_EXTRAS,
    "painterly poster feel",
    "hand-painted fantasy illustration feel",
    "matte painting look",
    "brush-texture rendering",
    "dry canvas feel",
    "storybook shading",
    "soft illustrated finish",
)


def _planet_slot_block(
    planet: str,
    slot: str,
    *,
    planet_references_meta: dict[str, Any],
) -> str:
    if not _planet_ref_used(planet_references_meta, slot):
        return ""
    name = normalize_planet_name(planet)
    if slot == "planet_b":
        return _PLANET_SLOT_IDENTITY_BLOCKS_B.get(name, "")
    return _PLANET_SLOT_IDENTITY_BLOCKS.get(name, "")


def _planet_ref_used(meta: dict[str, Any], slot: str) -> bool:
    row = meta.get(slot) if isinstance(meta.get(slot), dict) else {}
    return bool(row.get("used") and row.get("image_path"))


def _planet_references_active(meta: dict[str, Any]) -> bool:
    return _planet_ref_used(meta, "planet_a") or _planet_ref_used(meta, "planet_b")


def build_planet_reference_identity_hardlock_layer(
    planet_a: str,
    planet_b: str,
    planet_references_meta: dict[str, Any],
) -> str:
    """Strong per-planet identity blocks when approved references are active for that slot."""
    if not _planet_references_active(planet_references_meta):
        return ""
    chunks: list[str] = [
        f"{PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER} {PLANET_REFERENCE_IDENTITY_ENFORCEMENT_BODY}",
        PLANET_CAT_BODY_MATERIAL_INTENSITY_BLOCK,
    ]
    pa_block = _planet_slot_block(planet_a, "planet_a", planet_references_meta=planet_references_meta)
    pb_block = _planet_slot_block(planet_b, "planet_b", planet_references_meta=planet_references_meta)
    if pa_block:
        chunks.append(pa_block)
    if pb_block:
        chunks.append(pb_block)
    pair = {normalize_planet_name(planet_a), normalize_planet_name(planet_b)}
    if "Neptune" in pair and (_planet_ref_used(planet_references_meta, "planet_a") or _planet_ref_used(planet_references_meta, "planet_b")):
        chunks.append(NEPTUNE_ANTI_GENERIC_IDENTITY_BLOCK)
        chunks.append(NEPTUNE_PREMIUM_IDENTITY_HARDLOCK_BLOCK)
    if _uranus_reference_active(planet_a, planet_b, planet_references_meta):
        chunks.append(URANUS_FEATURE_HARDLOCK_BLOCK)
    return " ".join(c for c in chunks if c).strip()


def _uranus_reference_active(
    planet_a: str,
    planet_b: str,
    planet_references_meta: dict[str, Any],
) -> bool:
    if "Uranus" not in {normalize_planet_name(planet_a), normalize_planet_name(planet_b)}:
        return False
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    if pa == "Uranus" and _planet_ref_used(planet_references_meta, "planet_a"):
        return True
    if pb == "Uranus" and _planet_ref_used(planet_references_meta, "planet_b"):
        return True
    return False


def pair_includes_uranus(planet_a: str, planet_b: str) -> bool:
    return "Uranus" in {normalize_planet_name(planet_a), normalize_planet_name(planet_b)}


__all__ = [
    "NEPTUNE_ANTI_GENERIC_IDENTITY_BLOCK",
    "NEPTUNE_PREMIUM_IDENTITY_HARDLOCK_BLOCK",
    "NEPTUNE_PREMIUM_IDENTITY_NEGATIVE_EXTRAS",
    "URANUS_FEATURE_HARDLOCK_BLOCK",
    "URANUS_REFERENCE_HARDLOCK_V2",
    "URANUS_FEATURE_NEGATIVE_EXTRAS",
    "PLANET_REFERENCE_IDENTITY_ENFORCEMENT_BODY",
    "PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER",
    "PLANET_REFERENCE_IDENTITY_NEGATIVE_EXTRAS",
    "build_planet_reference_identity_hardlock_layer",
    "pair_includes_uranus",
]
