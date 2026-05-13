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
        primary_marker="Warm solar chest emblem zone or crown medallion plate (blank flat emblem-ready panel)",
        secondary_marker="Tiny corona rim line echo on silhouette",
        signature_prop="Director chair fold-line or stage medallion collar",
        placement_rules=[
            "Reserve a large flat emblem-ready panel on chest emblem, crown band, or collar medallion—never a tiny speck.",
            "Keep emblem zone large enough for large integrated banner glyph at thumbnail scale beside the face.",
        ],
        must_show_markers=[
            "Warm regal staging with blank solar medallion/crown stamp zone OR unmistakable corona+crown read without painted Sun glyph pixels.",
            "Warm gold palette cue from canon remains visible.",
        ],
        optional_label_ideas=["crown stud chip", "spotlight oval rim behind head"],
        visual_read_rule=(
            "Keep Sun identity readable: blank emblem-ready solar medallion/crown zone plus regal warm staging—when a solar banner appears, paint ☉ into the cloth as integrated heraldry."
        ),
        avoid_marker_mistakes=[
            "Replacing Sun read with generic lion only",
            "Readable English words on props",
            "Cool monochrome hero with no warm solar cue",
        ],
        short_prompt_line=(
            "Sun read: blank chest/crown emblem panel + warm corona cue—leader medallion zone, not vague sparkle."
        ),
    ),
    "Moon": PlanetIdentityMarkerProfile(
        planet_name="Moon",
        planet_symbol="\u263d",
        symbol_name="Moon crescent glyph (☽)",
        primary_marker="Crescent-shaped blank stamp zone on pillow corner, blanket fold, or sleepwear pin (emblem-ready)",
        secondary_marker="Tide-line belly stripe from canon",
        signature_prop="Soft pillow + pled blanket fold with optional crescent chip",
        placement_rules=[
            "Reserve one flat embroidery patch, blanket corner stamp disk, or hairpin medallion—keep the stamp area clear for cloth-integrated emblem art.",
            "One placement only - do not scatter many moons.",
        ],
        must_show_markers=[
            "Cozy pillow+pled nest with blank lunar stamp zone OR crescent ear tufts from canon—no painted crescent glyph pixels in-image.",
            "Cool pearlescent palette cue remains.",
        ],
        optional_label_ideas=["felt star lure chip", "sleep mask band"],
        visual_read_rule=(
            "Keep Moon identity readable: blank lunar stamp zone on soft goods OR unmistakable cozy nest + crescent ears—integrated canon glyph on that planet's banner when flags appear."
        ),
        avoid_marker_mistakes=[
            "Night sky filled with dozens of moon shapes",
            "Horror hollow eyes tied only to moon shape",
        ],
        short_prompt_line="Moon read: blank pillow/pled stamp patch + nest staging—☽ integrated on Moon banner cloth when shown—not floating sticker glyphs.",
    ),
    "Mercury": PlanetIdentityMarkerProfile(
        planet_name="Mercury",
        planet_symbol="\u263f",
        symbol_name="Mercury glyph (☿)",
        primary_marker="Mercury faction banner: large centered **\u263f (☿)** painted **into the flag cloth** as flat heraldic gold / embroidery—follows folds and light (not a floating sticker)",
        secondary_marker="Glasses + satchel + note-card student cluster from canon",
        signature_prop="Messenger bag flap pin + pencil from canon",
        placement_rules=[
            "Banner glyph must read as **canonical ☿**: circle with small crescent/horns above and cross below—centered on Mercury's left/port banner field in pair shots.",
            "Keep student props clustered; do not shrink the banner emblem to an unreadable speck.",
        ],
        must_show_markers=[
            "Glasses+satchel+note-card trio clearly Mercury-coded **and** Mercury's faction flag shows **one large integrated ☿** in the cloth (heraldic treatment, perspective-correct).",
        ],
        optional_label_ideas=["stamp on star-map card corner"],
        visual_read_rule=(
            "Keep Mercury identity readable: **☿ on Mercury's own banner** as in-scene heraldry plus nimble student props—never a pasted white sticker hovering over the muzzle."
        ),
        avoid_marker_mistakes=[
            "Readable checklist text",
            "Too many competing stamps",
            "Distorted pseudo-Mercury marks, random runes, or letters pretending to be ☿",
        ],
        short_prompt_line=(
            "Mercury read: **☿** integrated on Mercury's banner cloth—student props cluster; no floating sticker glyphs."
        ),
    ),
    "Venus": PlanetIdentityMarkerProfile(
        planet_name="Venus",
        planet_symbol="\u2640",
        symbol_name="Venus glyph",
        primary_marker="Blank fashion clasp plate, handbag medallion, mirror back disk, or single jewelry accent (emblem-ready)",
        secondary_marker="Rose stem + pearl strand from canon (keep minimal)",
        signature_prop="Exactly one refined accessory focal with reserved flat stamp zone (no painted Venus glyph pixels)",
        placement_rules=[
            "Choose ONE primary blank medallion/clasp zone for cloth-integrated emblem—clasp, mirror back, or gem pin face kept clean.",
            "Fashion silhouette stays elegant—stamp zone large enough for a clear cloth emblem without micro-filigree clutter.",
        ],
        must_show_markers=[
            "Rose+pearl pairing with one blank emblem-ready accessory stamp zone (no readable Venus glyph pixels in-image).",
            "Never overload: respect canon one-accent rule alongside reserved stamp zone.",
        ],
        optional_label_ideas=["ribbon buckle chip", "compact clutch plate"],
        visual_read_rule=(
            "Keep Venus identity readable: blank fashion stamp zone plus elegant silhouette—integrated canon glyph on that planet's banner when flags appear."
        ),
        avoid_marker_mistakes=[
            "Stacking many luxury props",
            "Micro-filigree glyph lost at small size",
            "Readable brand marks",
        ],
        short_prompt_line="Venus read: blank clasp/mirror/pin medallion—chic minimal; integrated heraldic glyph on faction banner when visible.",
    ),
    "Mars": PlanetIdentityMarkerProfile(
        planet_name="Mars",
        planet_symbol="\u2642",
        symbol_name="Mars male sign glyph",
        primary_marker="Blank shoulder stamp patch, shield boss, or armor plaque (emblem-ready; no painted Mars glyph pixels)",
        secondary_marker="Foam weapon motif plane carrying matching emblem chip",
        signature_prop="Bandana + flame tuft + bitten ear nick from canon (always)",
        placement_rules=[
            "Reserve a centered flat emblem boss on skin patch, shield face, belt plate, or pauldron—keep boss clear for cloth-integrated emblem.",
            "If shield exists, emblem boss occupies center mass - not edge sliver.",
        ],
        must_show_markers=[
            "Blank fight-ready emblem boss on tattoo/shield/armor (no readable Mars glyph pixels in-image)",
            "Bandana knot visible",
            "Tiny flame ear tuft visible",
            "Bitten ear nick visible",
        ],
        optional_label_ideas=["helm crest chip", "gauntlet buckle stamp"],
        visual_read_rule=(
            "Keep Mars identity readable: blank emblem boss plus bandana, flame tuft, and bitten ear nick—integrated canon glyph on that planet's banner when flags appear."
        ),
        avoid_marker_mistakes=[
            "Hiding all Mars cues under helmet without emblem elsewhere",
            "Realistic gore tied to emblem",
        ],
        short_prompt_line=(
            "Mars read: blank shield/armor stamp boss + bandana + flame tuft + ear nick; integrated heraldic glyph on faction banner when visible."
        ),
    ),
    "Jupiter": PlanetIdentityMarkerProfile(
        planet_name="Jupiter",
        planet_symbol="\u2643",
        symbol_name="Jupiter glyph (♃)",
        primary_marker="Jupiter faction banner: large centered **\u2643 (♃)** painted **into the flag cloth** as flat heraldic gold / embroidery—follows folds and rim light (not a floating sticker)",
        secondary_marker="Laurel outline chip near banner hoist (abstract motif only)",
        signature_prop="Open wisdom book + pointer from canon",
        placement_rules=[
            "Banner glyph must read as **canonical ♃**: stylized **number-4** structure with **curved upper stroke** and **cross-like lower stroke**—centered on Jupiter's right/starboard banner in pair shots.",
            "Reject hook-shapes, Latin **J**, lambda **\u039b**, random runes, or lumpy pseudo-symbols masquerading as Jupiter.",
        ],
        must_show_markers=[
            "Open wisdom book + pointer with sage silhouette **and** Jupiter's faction flag shows **one large integrated ♃** in the cloth (heraldic treatment, perspective-correct).",
            "Big-cheek sage silhouette from canon remains.",
        ],
        optional_label_ideas=["lecture baton end cap disk"],
        visual_read_rule=(
            "Keep Jupiter identity readable: **♃ on Jupiter's own banner** as in-scene heraldry plus sage book/pointer—never a pasted sticker over the face."
        ),
        avoid_marker_mistakes=[
            "Readable textbook pages",
            "Tiny lost glyph on busy robe pattern",
            "♃ distorted into hook, J, lambda, or invented sigil",
        ],
        short_prompt_line=(
            "Jupiter read: **♃** integrated on Jupiter's banner cloth—sage book/pointer; canonical 4-like cross structure."
        ),
    ),
    "Saturn": PlanetIdentityMarkerProfile(
        planet_name="Saturn",
        planet_symbol="\u2644",
        symbol_name="Saturn glyph",
        primary_marker="Blank watch dial center disk, cufflink face, hat band plaque, or belt buckle boss (emblem-ready)",
        secondary_marker="Ring-hoop belt echo beside reserved stamp zone",
        signature_prop="Wide-brim hat + blank watch from canon",
        placement_rules=[
            "Keep watch dial center open for integrated cloth emblem OR clean hat band plaque disk—crisp contrast, no painted Saturn glyph pixels.",
            "Keep business-structure silhouette while reserving stamp zone.",
        ],
        must_show_markers=[
            "Structured hat+watch with blank time/structure accessory stamp zone (no readable Saturn glyph pixels in-image).",
        ],
        optional_label_ideas=["briefcase clasp medallion"],
        visual_read_rule=(
            "Keep Saturn identity readable: blank stamp zone on time/structure accessory plus hat/pinstripe boss read—integrated canon glyph on that planet's banner when flags appear."
        ),
        avoid_marker_mistakes=[
            "Readable clock numerals",
            "Stamp zone shrunk inside watch bezel unreadably",
        ],
        short_prompt_line="Saturn read: blank watch/hat/belt stamp boss—structure boss; integrated heraldic glyph on faction banner when visible.",
    ),
    "Uranus": PlanetIdentityMarkerProfile(
        planet_name="Uranus",
        planet_symbol="\u2645",
        symbol_name="Uranus glyph",
        primary_marker="Blank neon patch disk, hoop earring face, jacket back patch, or portal rim medallion (emblem-ready)",
        secondary_marker="Lightning tail tip echo near reserved stamp zone (abstract)",
        signature_prop="Electric portal hoop from canon",
        placement_rules=[
            "Reserve clean glowing patch / earring / portal rim stamp disk—no painted Uranus glyph pixels.",
            "Pair with punk silhouette - avoid washing out under jacket folds.",
        ],
        must_show_markers=[
            "Portal hoop with blank rim/patch stamp zone OR punk electric palette with one emblem-ready disk.",
        ],
        optional_label_ideas=["sneaker strap buckle plate"],
        visual_read_rule=(
            "Keep Uranus identity readable: blank stamp zone on neon/patch/earring/portal plus punk electric palette—integrated canon glyph on that planet's banner when flags appear."
        ),
        avoid_marker_mistakes=[
            "Readable graffiti words",
            "Stamp zone lost in chaotic pattern spam",
        ],
        short_prompt_line="Uranus read: blank neon/portal stamp disk—punk electric badge; integrated heraldic glyph on faction banner when visible.",
    ),
    "Neptune": PlanetIdentityMarkerProfile(
        planet_name="Neptune",
        planet_symbol="\u2646",
        symbol_name="Neptune glyph",
        primary_marker="Blank trident head disk, staff top medallion, wave buckle boss, or fog medallion (emblem-ready)",
        secondary_marker="Twin bubbles + single tiny fish shape framing reserved stamp zone",
        signature_prop="Quiet trident/wave ornament + fog pocket from canon tone",
        placement_rules=[
            "Reserve flat disk on trident plane, staff top, or belt wave plaque—no painted Neptune glyph pixels.",
            "Pair bubbles/fish as framing only - do not crowd schools.",
        ],
        must_show_markers=[
            "Trident/wave ornament with blank stamp disk plus bubble/fish motif (no readable Neptune glyph pixels in-image).",
            "Misty outline read from canon preserved.",
        ],
        optional_label_ideas=["bottle cap seal disk", "surf sash buckle"],
        visual_read_rule=(
            "Keep Neptune identity readable: blank trident/wave stamp zone plus bubbles/fish support cues—integrated canon glyph on that planet's banner when flags appear."
        ),
        avoid_marker_mistakes=[
            "Busy fish swarm hiding stamp zone",
            "Hyperreal water simulation obscuring emblem disk",
        ],
        short_prompt_line="Neptune read: blank trident/wave disk—bubbles/fish frame; integrated heraldic glyph on faction banner when visible.",
    ),
    "Pluto": PlanetIdentityMarkerProfile(
        planet_name="Pluto",
        planet_symbol="\u2647",
        symbol_name="Pluto glyph",
        primary_marker="Blank cauldron face disk, amulet face, glove back plaque, or shadow sigil medallion (emblem-ready)",
        secondary_marker="Spiral pupil echo beside reserved stamp zone (readable cartoon)",
        signature_prop="Mini cauldron + spike cuffs + shadow smoke wisps from canon",
        placement_rules=[
            "Reserve high-contrast flat stamp on cauldron belly, pendant face, or glove back—no painted Pluto glyph pixels.",
            "Shadow wisps frame stamp zone - never obscure it entirely.",
        ],
        must_show_markers=[
            "Cauldron/amulet with blank underworld stamp disk OR glove plaque open for integrated cloth emblem if shown.",
            "Spiral eyes + shadow smoke intensity from canon preserved.",
        ],
        optional_label_ideas=["cloak clasp octagon", "ritual spoon handle disk"],
        visual_read_rule=(
            "Keep Pluto identity readable: blank cauldron/amulet/glove/shadow stamp zone plus spiral-eye cue—integrated canon glyph on that planet's banner when flags appear."
        ),
        avoid_marker_mistakes=[
            "Readable occult words",
            "Gore tied to stamp zone",
        ],
        short_prompt_line="Pluto read: blank cauldron/amulet/glove stamp—underworld disk; integrated heraldic glyph on faction banner when visible.",
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
            "- keep armor/shield/jewelry secondary to **large integrated banner glyphs**; avoid competing fake runes on small props."
        )
    glyph_tail = (
        " [PLANET GLYPH HERALDRY v1 — painted into the scene] When this planet carries a visible **faction flag or parade banner**, "
        f"paint **one large canonical astrological glyph** ({marker.planet_symbol} — {marker.symbol_name}) **into the flag cloth** as part of the illustration: "
        "centered on the cloth field, **flat heraldic gold paint or embroidered-thread emblem**, warped with **fabric folds, perspective, and key light** "
        "(not a floating white sticker, not a detached glow hovering over characters, not pasted across faces/foreheads/muzzles or torsos unless the shot is explicitly medallion-focused). "
        "Reject malformed planetary signs, pseudo-glyphs, fake letters, random occult runes, or sticker-like symbols that ignore cloth physics."
    )
    return (
        f"[IDENTITY MARKERS v1] for {planet}:{skin_clause} "
        f"- Canonical glyph to render **on this planet's own banner cloth** when flags appear: "
        f"{marker.planet_symbol} ({marker.symbol_name}). "
        f"- Primary marker: {marker.primary_marker}. "
        f"- Secondary marker: {marker.secondary_marker}. "
        f"- Signature prop: {marker.signature_prop}. "
        f"- Placement guidance: {placement}. "
        f"- Staging objectives (achieve without painted glyph pixels—props + blank stamp zones): {must_show}. "
        f"- Optional accent ideas: {optional}. "
        f"- Visual read rule: {marker.visual_read_rule}. "
        f"- Avoid marker mistakes: {avoid_m}. "
        f"- Compact cue: {marker.short_prompt_line}"
        f"{glyph_tail}"
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
