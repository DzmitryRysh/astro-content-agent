"""Catstyle planet identity markers v1 - symbol and placement cues layered on canon (prompt layer)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import PlanetIdentityMarkerProfile
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

_PLANET_ORDER = (
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
)

PLANET_IDENTITY_MARKER_PROFILES: dict[str, PlanetIdentityMarkerProfile] = {
    "Sun": PlanetIdentityMarkerProfile(
        planet_name="Sun",
        planet_symbol="\u2609",
        symbol_name="Sun glyph",
        primary_marker="Warm solar medallion or chest emblem (flat icon)",
        secondary_marker="Tiny corona rim line echo on silhouette",
        signature_prop="Director chair fold-line or stage medallion collar",
        placement_rules=[
            "Place sun glyph on chest emblem, crown band, or collar medallion - never tiny illegible speck.",
            "Keep emblem large enough to read at thumbnail scale beside the face.",
        ],
        must_show_markers=[
            "Visible Sun glyph OR unmistakable corona+crown staging tied to Sun identity.",
            "Warm gold palette cue from canon remains visible.",
        ],
        optional_label_ideas=["crown stud chip", "spotlight oval rim behind head"],
        visual_read_rule=(
            "Keep Sun identity readable in every scene: visible Sun glyph on emblem/crown/medallion plus regal warm staging."
        ),
        avoid_marker_mistakes=[
            "Replacing Sun read with generic lion only",
            "Readable English words on props",
            "Cool monochrome hero with no warm solar cue",
        ],
        short_prompt_line=(
            "Sun read: chest/crown Sun glyph + warm corona cue - leader medallion, not vague sparkle."
        ),
    ),
    "Moon": PlanetIdentityMarkerProfile(
        planet_name="Moon",
        planet_symbol="\u263e",
        symbol_name="Moon crescent glyph",
        primary_marker="Crescent mark on pillow corner, blanket fold, or sleepwear pin",
        secondary_marker="Tide-line belly stripe from canon",
        signature_prop="Soft pillow + pled blanket fold with optional crescent chip",
        placement_rules=[
            "Moon glyph sits on pillow embroidery patch, blanket corner, or hairpin - flat graphic.",
            "One placement only - do not scatter many moons.",
        ],
        must_show_markers=[
            "Visible crescent glyph OR clear pillow+pled nest with crescent ear tufts from canon.",
            "Cool pearlescent palette cue remains.",
        ],
        optional_label_ideas=["felt star lure chip", "sleep mask band"],
        visual_read_rule=(
            "Keep Moon identity readable: crescent glyph on soft goods OR unmistakable cozy nest + crescent ears."
        ),
        avoid_marker_mistakes=[
            "Night sky filled with dozens of moon shapes",
            "Horror hollow eyes tied only to moon shape",
        ],
        short_prompt_line="Moon read: crescent on pillow/pled/pin - cozy nest staging, one clear glyph.",
    ),
    "Mercury": PlanetIdentityMarkerProfile(
        planet_name="Mercury",
        planet_symbol="\u263f",
        symbol_name="Mercury glyph",
        primary_marker="Tiny Mercury mark on glasses temple, pen cap, or messenger flap",
        secondary_marker="Notepad corner seal (blank)",
        signature_prop="Messenger bag flap pin + pencil from canon",
        placement_rules=[
            "Glyph on glasses case edge, pen ferrule disk, or bag clasp plate - flat stamp.",
            "Keep student/analyst props clustered - avoid prop haystack.",
        ],
        must_show_markers=[
            "Visible Mercury glyph OR glasses+satchel+note card trio clearly Mercury-coded.",
        ],
        optional_label_ideas=["stamp on star-map card corner"],
        visual_read_rule=(
            "Keep Mercury identity readable: Mercury glyph on stationery/bag/glasses plus nimble student props."
        ),
        avoid_marker_mistakes=[
            "Readable checklist text",
            "Too many competing stamps",
        ],
        short_prompt_line="Mercury read: glyph on glasses/pen/bag - messenger-student stamp cluster.",
    ),
    "Venus": PlanetIdentityMarkerProfile(
        planet_name="Venus",
        planet_symbol="\u2640",
        symbol_name="Venus glyph",
        primary_marker="Venus mark on clasp, handbag plate, mirror back, or single jewelry accent",
        secondary_marker="Rose stem + pearl strand from canon (keep minimal)",
        signature_prop="Exactly one refined accessory focal carrying the glyph",
        placement_rules=[
            "Choose ONE primary placement for the Venus glyph - clasp, mirror back, or gem pin face.",
            "Fashion silhouette stays elegant - glyph reads at thumbnail without extra bling.",
        ],
        must_show_markers=[
            "Visible Venus glyph on accessory OR rose+pearl pairing with one glyph stamp.",
            "Never overload: respect canon one-accent rule alongside glyph.",
        ],
        optional_label_ideas=["ribbon buckle chip", "compact clutch plate"],
        visual_read_rule=(
            "Keep Venus identity readable: Venus glyph on fashion detail plus elegant silhouette - one refined focal."
        ),
        avoid_marker_mistakes=[
            "Stacking many luxury props",
            "Micro-filigree glyph lost at small size",
            "Readable brand marks",
        ],
        short_prompt_line="Venus read: female-sign on clasp/mirror/pin - chic minimal, never glam clutter.",
    ),
    "Mars": PlanetIdentityMarkerProfile(
        planet_name="Mars",
        planet_symbol="\u2642",
        symbol_name="Mars male sign glyph",
        primary_marker="Mars glyph as shoulder tattoo, shield emblem, or armor plaque",
        secondary_marker="Foam weapon motif plane carrying matching emblem chip",
        signature_prop="Bandana + flame tuft + bitten ear nick from canon (always)",
        placement_rules=[
            "Glyph on skin patch, shield face, belt plate, or pauldron - high contrast flat icon.",
            "If shield exists, emblem occupies center mass - not edge sliver.",
        ],
        must_show_markers=[
            "Visible Mars glyph (tattoo, shield, or armor mark)",
            "Bandana knot visible",
            "Tiny flame ear tuft visible",
            "Bitten ear nick visible",
        ],
        optional_label_ideas=["helm crest chip", "gauntlet buckle stamp"],
        visual_read_rule=(
            "Keep Mars identity readable in every scene: visible Mars symbol plus bandana, flame tuft, and bitten ear nick."
        ),
        avoid_marker_mistakes=[
            "Hiding all Mars cues under helmet without emblem elsewhere",
            "Realistic gore tied to emblem",
        ],
        short_prompt_line=(
            "Mars read: male-sign tattoo/shield/armor + bandana + flame tuft + ear nick - fight-ready stamp."
        ),
    ),
    "Jupiter": PlanetIdentityMarkerProfile(
        planet_name="Jupiter",
        planet_symbol="\u2643",
        symbol_name="Jupiter glyph",
        primary_marker="Jupiter mark on book cover seal, robe clasp, brooch, or ring face",
        secondary_marker="Laurel outline chip pairing with glyph",
        signature_prop="Open wisdom book + pointer from canon",
        placement_rules=[
            "Glyph on book seal, clasp, or brooch - centered readable silhouette.",
            "Keep sage/teaching props adjacent so glyph reads as Jupiter authority.",
        ],
        must_show_markers=[
            "Visible Jupiter glyph OR book+brooch pairing with clear glyph stamp.",
            "Big-cheek sage silhouette from canon remains.",
        ],
        optional_label_ideas=["lecture baton end cap disk"],
        visual_read_rule=(
            "Keep Jupiter identity readable: Jupiter glyph on teaching regalia plus sage book/pointer staging."
        ),
        avoid_marker_mistakes=[
            "Readable textbook pages",
            "Tiny lost glyph on busy robe pattern",
        ],
        short_prompt_line="Jupiter read: glyph on book seal/clasp/brooch - sage teacher medallion.",
    ),
    "Saturn": PlanetIdentityMarkerProfile(
        planet_name="Saturn",
        planet_symbol="\u2644",
        symbol_name="Saturn glyph",
        primary_marker="Saturn mark on wristwatch face center, cufflink, hat band plaque, or belt buckle",
        secondary_marker="Ring-hoop belt echo beside glyph",
        signature_prop="Wide-brim hat + blank watch from canon",
        placement_rules=[
            "Glyph replaces dial center icon OR sits on hat band plaque - crisp contrast.",
            "Keep business-structure silhouette while placing glyph.",
        ],
        must_show_markers=[
            "Visible Saturn glyph on watch/cuff/hat/belt OR structured hat+watch with glyph on accessory.",
        ],
        optional_label_ideas=["briefcase clasp medallion"],
        visual_read_rule=(
            "Keep Saturn identity readable: Saturn glyph on time/structure accessory plus hat/pinstripe boss read."
        ),
        avoid_marker_mistakes=[
            "Readable clock numerals",
            "Glyph shrunk inside watch bezel unreadably",
        ],
        short_prompt_line="Saturn read: glyph on watch/hat plaque/belt - time-and-structure boss stamp.",
    ),
    "Uranus": PlanetIdentityMarkerProfile(
        planet_name="Uranus",
        planet_symbol="\u2645",
        symbol_name="Uranus glyph",
        primary_marker="Uranus mark as neon patch, hoop earring disk, jacket back patch, or portal rim stamp",
        secondary_marker="Lightning tail tip echo near glyph",
        signature_prop="Electric portal hoop from canon",
        placement_rules=[
            "Glyph sits on glowing patch, earring face, or portal ring stamp - high contrast.",
            "Pair with punk silhouette - avoid washing out under jacket folds.",
        ],
        must_show_markers=[
            "Visible Uranus glyph OR portal hoop with Uranus stamp on rim/patch.",
        ],
        optional_label_ideas=["sneaker strap buckle plate"],
        visual_read_rule=(
            "Keep Uranus identity readable: Uranus glyph on neon/patch/earring/portal plus punk electric palette."
        ),
        avoid_marker_mistakes=[
            "Readable graffiti words",
            "Glyph lost in chaotic pattern spam",
        ],
        short_prompt_line="Uranus read: glyph on neon patch/earring/portal rim - punk electric badge.",
    ),
    "Neptune": PlanetIdentityMarkerProfile(
        planet_name="Neptune",
        planet_symbol="\u2646",
        symbol_name="Neptune glyph",
        primary_marker="Neptune glyph on trident head, staff disk, wave buckle, or fog medallion",
        secondary_marker="Twin bubbles + single tiny fish shape supporting glyph placement",
        signature_prop="Quiet trident/wave ornament + fog pocket from canon tone",
        placement_rules=[
            "Glyph on trident plane, staff top disk, or belt wave plaque - flat graphic.",
            "Pair bubbles/fish as framing only - do not crowd schools.",
        ],
        must_show_markers=[
            "Visible Neptune glyph OR trident/wave ornament with Neptune stamp plus bubble/fish motif.",
            "Misty outline read from canon preserved.",
        ],
        optional_label_ideas=["bottle cap seal disk", "surf sash buckle"],
        visual_read_rule=(
            "Keep Neptune identity readable: Neptune glyph on trident/wave accessory plus bubbles/fish support cues."
        ),
        avoid_marker_mistakes=[
            "Busy fish swarm hiding glyph",
            "Hyperreal water simulation obscuring symbol",
        ],
        short_prompt_line="Neptune read: glyph on trident/wave disk - bubbles/fish frame, fog stays minimal.",
    ),
    "Pluto": PlanetIdentityMarkerProfile(
        planet_name="Pluto",
        planet_symbol="\u2647",
        symbol_name="Pluto glyph",
        primary_marker="Pluto glyph on cauldron face, amulet disk, glove plate, or shadow sigil plaque",
        secondary_marker="Spiral pupil echo beside stamped glyph (readable cartoon)",
        signature_prop="Mini cauldron + spike cuffs + shadow smoke wisps from canon",
        placement_rules=[
            "Glyph on cauldron belly, pendant face, or glove back - high contrast flat stamp.",
            "Shadow wisps frame glyph - never obscure it entirely.",
        ],
        must_show_markers=[
            "Visible Pluto glyph OR cauldron/amulet with clear Pluto stamp.",
            "Spiral eyes + shadow smoke intensity from canon preserved.",
        ],
        optional_label_ideas=["cloak clasp octagon", "ritual spoon handle disk"],
        visual_read_rule=(
            "Keep Pluto identity readable: Pluto glyph on cauldron/amulet/glove/shadow plaque plus spiral-eye cue."
        ),
        avoid_marker_mistakes=[
            "Readable occult words",
            "Gore tied to glyph area",
        ],
        short_prompt_line="Pluto read: glyph on cauldron/amulet/glove - underworld stamp with spiral-eye cue.",
    ),
}


def format_identity_markers_prompt_block(
    planet: str,
    marker: PlanetIdentityMarkerProfile,
    *,
    has_skin: bool,
) -> str:
    """Deterministic paragraph appended after [CANON v1 base] in image prompts."""
    placement = " | ".join(marker.placement_rules)
    must_show = " | ".join(marker.must_show_markers)
    optional = " | ".join(marker.optional_label_ideas) if marker.optional_label_ideas else "none required"
    avoid_m = " | ".join(marker.avoid_marker_mistakes)
    skin_clause = ""
    if has_skin:
        skin_clause = (
            " Skin/costume overlay is optional: preserve this entire marker block alongside [CANON v1 base] "
            "- place glyph on armor, shield face, gear plaque, tattoo, fabric patch, or jewelry plane so symbol stays readable."
        )
    return (
        f"[IDENTITY MARKERS v1] for {planet}:{skin_clause} "
        f"- Planet symbol: {marker.planet_symbol} ({marker.symbol_name}). "
        f"- Primary marker: {marker.primary_marker}. "
        f"- Secondary marker: {marker.secondary_marker}. "
        f"- Signature prop: {marker.signature_prop}. "
        f"- Placement guidance: {placement}. "
        f"- Must remain visible: {must_show}. "
        f"- Optional accent ideas: {optional}. "
        f"- Visual read rule: {marker.visual_read_rule}. "
        f"- Avoid marker mistakes: {avoid_m}. "
        f"- Compact cue: {marker.short_prompt_line}"
    )


def get_planet_identity_marker_profile(planet_name: str) -> PlanetIdentityMarkerProfile:
    key = normalize_planet_name(planet_name)
    return PLANET_IDENTITY_MARKER_PROFILES[key]


def list_planet_identity_marker_profiles() -> list[PlanetIdentityMarkerProfile]:
    return [PLANET_IDENTITY_MARKER_PROFILES[p] for p in _PLANET_ORDER]


__all__ = [
    "PLANET_IDENTITY_MARKER_PROFILES",
    "format_identity_markers_prompt_block",
    "get_planet_identity_marker_profile",
    "list_planet_identity_marker_profiles",
]
