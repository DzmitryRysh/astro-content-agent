"""Banner-only glyph reference assist for Catstyle image prompts (v1)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.planet_glyph_registry_v1 import (
    canonical_glyph_char,
    glyph_prompt_label,
)

BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK: str = (
    "[CATSTYLE BANNER-ONLY GLYPH DISCIPLINE v1] **Exactly one** large canonical planetary glyph on the "
    "**left/port faction banner** (planet A) and **exactly one** on the **right/starboard faction banner** (planet B). "
    "Glyphs are **painted or woven into flag cloth only**—heraldic gold / embroidery, perspective-correct, cloth-locked. "
    "**Sun left/port banner:** complete **\u2609 (☉)** = **full circle with clearly visible central dot** (not a hollow ring, not a partial arc). "
    "**Do not** place planetary glyphs on chest, armor, costume jewelry, accessories, portal rims, body patches, crown bands, "
    "floating symbols, foreheads, shields-as-stickers, or background clutter. "
    "Preserve monumental cosmic zodiac coliseum, canonical engraved zodiac floor ring, layered starfield/nebula void, "
    "Earth disk above arena, and high-contrast volumetric cinematic lighting. "
    "**Catplanet bodies dominate** over flags; **no circular chest badges, collar medallion disks, or round torso emblem props.**"
)

BANNER_ONLY_NO_CHEST_BADGE_BLOCK: str = (
    "[BANNER-ONLY NO CHEST BADGE v1] **Forbidden on both characters:** circular chest badges, collar "
    "medallion disks, round torso emblems, badge-shaped brooches, or any disk/plaque that invites off-banner "
    "glyphs. Identity = **planetary body material + aura** and **faction banner cloth** only."
)

# Substrings that must not appear in banner-only identity / composition cue text.
BANNER_ONLY_FORBIDDEN_IDENTITY_PHRASES: tuple[str, ...] = (
    "chest emblem",
    "crown medallion",
    "portal rim medallion",
    "reserved stamp zone",
    "reserved emblem zone",
    "emblem-ready",
    "collar medallion",
    "emblem boss",
    "emblem zone",
    "stamp zone",
    "prop stamp",
    "prop stamps",
    "armor plaque",
    "shield boss",
    "blank patch disk",
    "blank stamp",
    "medallion",
    "medallion plate",
    "solar medallion",
    "stage medallion",
    "flat sun medallion",
    "hat band plaque",
    "belt buckle boss",
    "watch dial center disk",
    "blank chest",
    "blank chest/crown",
    "chest/crown",
    "beside faces/bodies",
    "beside the face",
    "beside faces",
    "flat, ,",
    "nner appears",
)

BANNER_ONLY_ART_DIRECTION_IDENTITY_CUE: str = (
    "Keep each planet's costume/prop identity and **faction banner glyphs** readable at thumbnail scale—"
    "canonical glyphs on left/port and right/starboard banner cloth only, never on bodies or accessories."
)

BANNER_ONLY_GLYPH_NEGATIVE_EXTRAS: tuple[str, ...] = (
    "planetary glyph on chest or armor",
    "glyph on torso or collar",
    "glyph on regal collar or belt",
    "Uranus glyph on body",
    "Sun glyph off left banner",
    "body emblem copied from reference",
    "glyph on costume jewelry or portal rim",
    "extra planetary glyphs outside faction banners",
    "incomplete Sun glyph without central dot",
    "hollow sun ring without central dot",
    "circular chest badge",
    "collar medallion disk",
    "round torso emblem",
    "ordinary furry cat",
    "costume-first mascot",
    "plush fur dominance",
)

# Legacy art-direction lines replaced when banner-only mode is active.
_BANNER_ONLY_ART_DIRECTION_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        "Keep each planet's [IDENTITY MARKERS v1] prop stamps and reserved emblem zones readable at thumbnail scale beside faces/bodies.",
        BANNER_ONLY_ART_DIRECTION_IDENTITY_CUE,
    ),
    (
        "Keep each planet's [IDENTITY MARKERS v1] prop stamps and reserved emblem zones readable beside faces/bodies.",
        BANNER_ONLY_ART_DIRECTION_IDENTITY_CUE,
    ),
)

_DEFAULT_BANNER_GLYPH_REL_DIR = "references/banner_glyphs"

_BROKEN_FRAGMENT_RE = re.compile(
    r",\s*,|"
    r"flat,\s*,|"
    r",\s*or\s*\.|"
    r"\bnner appears\b|"
    r"beside the face\.|"
    r"\|\s*\.|"
    r"—never a tiny",
    re.IGNORECASE,
)

_GENERIC_BANNER_ONLY_FIELD: dict[str, str] = {
    "primary": "Costume, silhouette, and signature props from canon—no glyph pixels on body.",
    "secondary": "Canon secondary silhouette detail (abstract, not a glyph).",
    "signature": "One signature prop focal from canon (prop only, no painted glyph).",
    "placement": "Identity via costume, props, and palette—canonical glyph on this planet's faction banner only.",
    "must_show": "Planet-coded costume and prop read from canon—glyph on faction banner cloth only.",
    "visual_read": "Planet identity via costume and props; banner carries the canonical glyph when visible.",
    "short": "Costume/prop identity—glyph on faction banner only.",
    "avoid": "Readable text on props | Competing fake rune clutter off banners",
}

_BANNER_ONLY_PLANET_FIELD_FALLBACK: dict[str, dict[str, str]] = {
    "Sun": {
        "primary": (
            "Corona rim and solar-core body read, royal warm silhouette, golden armor accents, proud stage posture—"
            "no glyph on body; canonical \u2609 ONLY on left/port Sun faction banner (full circle + central dot)."
        ),
        "secondary": "Warm corona halo integrated at body rim (not a separate badge or disk).",
        "signature": "Regal staff or director-chair fold-line (props only—no circular chest/collar badge).",
        "placement": (
            "Identity via corona, solar-core body, golden armor, and proud stage posture—"
            "glyph \u2609 strictly on left/port Sun faction banner cloth."
        ),
        "must_show": (
            "Corona + warm gold solar palette + proud heroic stage read—"
            "glyph \u2609 on Sun banner cloth only."
        ),
        "visual_read": (
            "Sun reads via corona, solar-core body, and royal warm silhouette; "
            "\u2609 integrated heraldry on Sun banner only."
        ),
        "short": (
            "Sun: corona, solar-core body, golden armor, stage posture—"
            "\u2609 on left banner only (full circle + central dot)."
        ),
        "avoid": "Generic lion only | Readable English on props | Cool monochrome with no warm solar cue",
    },
    "Moon": {
        "primary": "Crescent ear tufts, pillow/blanket nest, cool pearlescent palette—no glyph on pillow or body.",
        "secondary": "Tide-line belly stripe from canon.",
        "signature": "Soft pillow + plush blanket fold (comfort props only).",
        "placement": "Cozy nest staging and lunar palette—glyph \u263d ONLY on Moon faction banner when flags show.",
        "must_show": "Pillow nest + crescent ears OR pearlescent cool palette—no painted crescent on props.",
        "visual_read": "Moon via cozy soft-goods staging; banner cloth carries \u263d when visible.",
        "short": "Moon: pillow/nest cues—\u263d on Moon banner only.",
    },
    "Uranus": {
        "primary": (
            "Electric portal hoop as prop-only set dressing, lightning tail, punk disruptor silhouette, "
            "cyan ice-gas body mass, orbital debris accents—no \u2645 on body or hoop rim."
        ),
        "secondary": "Lightning tail-tip echo (abstract streak, not a glyph).",
        "signature": "Electric portal hoop prop (structure only—no \u2645 painted on the rim).",
        "placement": (
            "Punk electric silhouette, portal hoop prop, and debris accents—"
            "glyph \u2645 ONLY on right/starboard Uranus faction banner cloth."
        ),
        "must_show": (
            "Portal hoop + lightning tail + cyan ice-gas body read—no Uranus glyph on props or body."
        ),
        "visual_read": (
            "Uranus via electric punk silhouette and portal hoop prop; \u2645 on Uranus banner only."
        ),
        "short": "Uranus: portal hoop prop, lightning tail, cyan ice-gas body—\u2645 on right banner only.",
        "avoid": "Readable graffiti words | Chaotic pattern spam hiding banner glyphs",
    },
    "Mercury": {
        "primary": (
            "Mercury faction banner: large centered **\u263f (\u263f)** painted **into the flag cloth** as flat heraldic gold "
            "/ embroidery—follows folds and light (not a floating sticker)."
        ),
        "secondary": "Glasses + satchel + note-card student cluster from canon.",
        "signature": "Messenger bag flap + pencil from canon.",
        "placement": "Student props clustered—glyph \u263f on Mercury left/port faction banner cloth only.",
        "must_show": "Glasses+satchel+note-card trio and one large integrated \u263f on Mercury banner cloth.",
        "visual_read": "Mercury via student props; \u263f on Mercury banner as in-scene heraldry.",
        "short": "Mercury: student props—\u263f on Mercury banner only.",
        "avoid": "Readable checklist text | Distorted pseudo-Mercury marks | Floating sticker glyphs",
    },
    "Jupiter": {
        "primary": (
            "Jupiter faction banner: large centered **\u2643 (\u2643)** painted **into the flag cloth** as flat heraldic gold "
            "/ embroidery—follows folds and light (not a floating sticker)."
        ),
        "secondary": "Laurel wreath + generous mentor silhouette from canon.",
        "signature": "Scroll or atlas tome prop from canon.",
        "placement": "Mentor staging and laurel read—glyph \u2643 on Jupiter faction banner cloth only.",
        "must_show": "Laurel+mentor silhouette and one large integrated \u2643 on Jupiter banner cloth.",
        "visual_read": "Jupiter via mentor props; \u2643 on Jupiter banner as in-scene heraldry.",
        "short": "Jupiter: laurel mentor cues—\u2643 on Jupiter banner only.",
        "avoid": "Readable text on scrolls | Floating sticker glyphs | Competing fake runes",
    },
    "Mars": {
        "primary": "Bandana knot, flame ear tuft, bitten ear nick—fight-ready silhouette without body glyphs.",
        "secondary": "Foam weapon motif plane (no glyph on shield face).",
        "signature": "Bandana + flame tuft + bitten ear nick from canon.",
        "placement": "Fight cues on costume/body—glyph \u2642 ONLY on Mars faction banner.",
        "must_show": "Bandana, flame tuft, ear nick visible—no Mars glyph on shield/armor.",
        "visual_read": "Mars via fighter props; banner carries \u2642.",
        "short": "Mars: bandana/flame/ear cues—\u2642 on Mars banner only.",
    },
    "Venus": {
        "primary": "Rose stem + pearl strand, elegant fashion silhouette—no clasp/mirror glyph pixels.",
        "secondary": "Rose stem + pearl strand (minimal).",
        "signature": "One refined accessory focal (fashion prop only).",
        "placement": "Elegant silhouette + rose/pearl—glyph \u2640 ONLY on Venus faction banner.",
        "must_show": "Rose+pearl + chic silhouette—no Venus glyph on jewelry.",
        "visual_read": "Venus via elegance props; banner carries \u2640.",
        "short": "Venus: rose/pearl fashion—\u2640 on Venus banner only.",
    },
    "Saturn": {
        "primary": "Wide-brim hat, blank watch prop, pinstripe boss silhouette—no glyph on watch dial or hat band.",
        "secondary": "Ring-hoop belt echo (abstract, not a glyph).",
        "signature": "Wide-brim hat + watch prop from canon.",
        "placement": "Structure/time boss cues on costume—glyph \u2644 ONLY on Saturn faction banner.",
        "must_show": "Hat+watch structure read—no Saturn glyph on accessories.",
        "visual_read": "Saturn via restraint props; banner carries \u2644.",
        "short": "Saturn: hat/watch structure—\u2644 on Saturn banner only.",
    },
    "Neptune": {
        "primary": "Fog veil, trident prop silhouette, wave-soft palette—no glyph on trident head or amulet.",
        "secondary": "Fog/mist veil echo.",
        "signature": "Trident or mist prop from canon.",
        "placement": "Dreamy fog staging—glyph \u2646 ONLY on Neptune faction banner.",
        "must_show": "Fog + trident/mist read—no Neptune glyph on props.",
        "visual_read": "Neptune via mist props; banner carries \u2646.",
        "short": "Neptune: fog/trident cues—\u2646 on Neptune banner only.",
    },
    "Pluto": {
        "primary": "Underworld cauldron prop, shadow mass, glove silhouette—no glyph on amulet or glove plaque.",
        "secondary": "Shadow mass echo.",
        "signature": "Cauldron or underworld prop from canon.",
        "placement": "Depth/shadow staging—glyph \u2647 ONLY on Pluto faction banner.",
        "must_show": "Cauldron/shadow read—no Pluto glyph on body props.",
        "visual_read": "Pluto via underworld props; banner carries \u2647.",
        "short": "Pluto: cauldron/shadow—\u2647 on Pluto banner only.",
    },
}


def banner_only_glyph_mode_active() -> bool:
    """Catstyle v1 prompts always apply banner-only glyph discipline in choreography."""
    return True


def _is_banner_cloth_primary_marker(text: str) -> bool:
    low = (text or "").lower()
    return "faction banner" in low or "banner cloth" in low or "into the flag" in low


def _collapse_field_text(text: str) -> str:
    out = re.sub(r"\s{2,}", " ", (text or "").strip())
    out = re.sub(r"\s+([,;|])\s+", r"\1 ", out)
    out = re.sub(r",\s*,+", ", ", out)
    out = re.sub(r"^[,\s|]+|[,\s|]+$", "", out)
    return out.strip(" ,;|")


def _text_looks_broken(text: str) -> bool:
    if not (text or "").strip() or len(text.strip()) < 16:
        return True
    if _BROKEN_FRAGMENT_RE.search(text):
        return True
    return bool(identity_marker_block_forbidden_in_banner_only(text))


def _banner_only_field_fallback(planet: str, field: str) -> str:
    planet_key = normalize_planet_name(planet)
    return (
        _BANNER_ONLY_PLANET_FIELD_FALLBACK.get(planet_key, {}).get(field)
        or _GENERIC_BANNER_ONLY_FIELD.get(field)
        or "Costume and prop identity cues only—glyph on faction banner cloth only."
    )


def sanitize_marker_field_for_banner_only(planet: str, raw: str, *, field: str) -> str:
    """Return clean banner-only identity copy; never partial regex-stripped fragments."""
    fb = _banner_only_field_fallback(planet, field)
    text = (raw or "").strip()
    if field == "primary" and _is_banner_cloth_primary_marker(text):
        result = _collapse_field_text(text)
        if not _text_looks_broken(result):
            return result
    return fb


def rewrite_art_direction_for_banner_only(text: str) -> str:
    """Swap legacy prop-stamp / emblem-zone composition cues for banner-only wording."""
    out = text or ""
    for old, new in _BANNER_ONLY_ART_DIRECTION_REPLACEMENTS:
        out = out.replace(old, new)
    return out


# Full assembled-prompt replacements (canon v1/v2, bible, skins, etc.) — longest phrases first.
_BANNER_ONLY_PROMPT_PHRASE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        "flat sun medallion collar (icon only, no readable text)",
        "neck corona line on silhouette (no circular chest or collar badge, no glyph pixels)",
    ),
    (
        "lens-flare-free sun medallion collar (flat icon)",
        "lens-flare-free neck corona line (costume prop, no badge disk)",
    ),
    ("flat sun medallion collar", "neck corona line (no chest badge)"),
    ("flat sun medallion", "solar-core body surface"),
    ("sun medallion collar", "neck corona line (no badge disk)"),
    ("regal collar shape", "neck corona line (no circular chest or collar badge)"),
    ("regal stage collar shape", "neck silhouette line (no badge disk)"),
    ("circular chest badge", "solar-core body surface"),
    ("collar medallion disk", "corona-integrated body rim"),
    ("round torso emblem", "planetary body surface"),
    (
        "Solar medallion, subtle regal collar motifs, banner-like drape.",
        "solar-core body accent, golden armor accents, proud stage posture, banner-like drape.",
    ),
    ("Solar medallion", "solar-core body accent"),
    ("solar medallion/crown", "solar-core body and crown silhouette"),
    ("solar medallion", "solar-core body accent"),
    ("stage medallion collar", "regal stage collar shape"),
    ("stage medallion", "proud stage posture"),
    ("blank solar medallion", "warm solar staging"),
    ("leader medallion zone", "proud stage posture"),
    ("central medallion/compass center", "central compass hub"),
    ("crown medallion", "crown silhouette shape"),
    ("collar medallion", "neck corona line (no badge disk)"),
    ("portal rim medallion", "portal hoop prop rim"),
    ("handbag medallion", "handbag clasp"),
    ("briefcase clasp medallion", "briefcase clasp accent"),
    ("staff top medallion", "staff top cap"),
    ("fog medallion", "fog veil accent"),
    ("shadow sigil medallion", "shadow sigil accent"),
    ("hairpin medallion", "hairpin accent"),
    ("pin medallion", "pin accent"),
    ("clasp medallion", "clasp accent"),
    ("medallion plate", "costume plate accent"),
    ("medallion-focused", "banner-focused"),
    ("emblem-ready panel on chest emblem, crown band, or collar medallion—never a tiny speck", "corona rim, golden armor, proud stage posture—glyph on banner only"),
    ("emblem-ready", "costume-only"),
    ("reserved emblem zones", "faction banner glyphs"),
    ("reserved emblem zone", "faction banner glyph placement"),
    ("prop stamps and reserved emblem zones readable at thumbnail scale beside faces/bodies", BANNER_ONLY_ART_DIRECTION_IDENTITY_CUE),
    ("prop stamps", "costume props"),
    ("prop stamp", "costume prop"),
    ("reserved stamp zone", "banner cloth field"),
    ("stamp zone", "banner cloth"),
    ("emblem zone", "costume detail"),
    ("emblem boss", "costume accent"),
    ("chest emblem", "chest costume line"),
    ("blank chest/crown", "costume and crown shape"),
    ("chest/crown", "costume and crown shape"),
    ("beside faces/bodies", "at thumbnail scale"),
    ("beside the face", "at thumbnail scale"),
    ("Reserve a large flat", "Proud stage posture with"),
    ("blank stamp zones", "costume props"),
    ("blank stamp zone", "costume prop"),
)


def _scrub_banner_only_prompt_leftovers(text: str) -> str:
    out = text
    out = re.sub(r"\bmedallions?\b", "costume accent", out, flags=re.I)
    out = re.sub(r"\bemblem-ready\b", "costume-only", out, flags=re.I)
    out = re.sub(r"\bstamp\s+zones?\b", "banner cloth", out, flags=re.I)
    out = re.sub(r"\breserved\s+emblem\s+zones?\b", "faction banner glyphs", out, flags=re.I)
    out = re.sub(r"\bprop\s+stamps?\b", "costume props", out, flags=re.I)
    out = re.sub(r",\s*,+", ", ", out)
    out = re.sub(r"\bnner appears\b", "banner appears", out, flags=re.I)
    return out


def sanitize_assembled_prompt_for_banner_only(text: str) -> str:
    """Rewrite full image prompt for banner-only glyph discipline (canon + markers + art direction)."""
    if not (text or "").strip():
        return text or ""
    out = rewrite_art_direction_for_banner_only(text)
    for old, new in _BANNER_ONLY_PROMPT_PHRASE_REPLACEMENTS:
        if old in out:
            out = out.replace(old, new)
    return _scrub_banner_only_prompt_leftovers(out)


def banner_only_prompt_forbidden_phrases(text: str) -> list[str]:
    """Forbidden substrings in a final banner-only assembled prompt (for tests)."""
    return identity_marker_block_forbidden_in_banner_only(text)


def identity_marker_block_forbidden_in_banner_only(text: str) -> list[str]:
    """Return forbidden substrings still present (for tests)."""
    low = (text or "").lower()
    return [p for p in BANNER_ONLY_FORBIDDEN_IDENTITY_PHRASES if p in low]


def _resolve_path(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    p = Path(str(raw).strip()).expanduser()
    if not p.is_absolute():
        candidate = (catstyle_repo_root() / p).resolve()
        p = candidate if candidate.is_file() else (Path.cwd() / p).resolve()
    else:
        p = p.resolve()
    return str(p) if p.is_file() else None


def default_banner_glyph_reference_path(planet: str) -> str | None:
    """Convention: ``references/banner_glyphs/{planet}_banner_glyph.png`` when present."""
    key = normalize_planet_name(planet).lower()
    rel = f"{_DEFAULT_BANNER_GLYPH_REL_DIR}/{key}_banner_glyph.png"
    return _resolve_path(rel)


def resolve_banner_glyph_reference_paths(
    planet_a: str,
    planet_b: str,
    *,
    explicit_planet_a: str | None = None,
    explicit_planet_b: str | None = None,
    use_auto_discovery: bool = True,
) -> tuple[str | None, str | None]:
    """Left/port banner = planet_a; right/starboard = planet_b."""
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    path_a = _resolve_path(explicit_planet_a) if explicit_planet_a else None
    path_b = _resolve_path(explicit_planet_b) if explicit_planet_b else None
    if use_auto_discovery:
        if path_a is None:
            path_a = default_banner_glyph_reference_path(pa)
        if path_b is None:
            path_b = default_banner_glyph_reference_path(pb)
    return path_a, path_b


def format_banner_glyph_reference_roles_block(
    planet_a: str,
    planet_b: str,
    *,
    style_reference_present: bool,
    glyph_ref_planet_a: str | None,
    glyph_ref_planet_b: str | None,
) -> str:
    """
    Describe Image A/B/C roles for providers that accept multiple reference inputs.

    Image A = main style/scene; B = left banner glyph (planet A); C = right (planet B).
    """
    if not glyph_ref_planet_a and not glyph_ref_planet_b:
        return ""

    la = glyph_prompt_label(normalize_planet_name(planet_a)) or planet_a
    lb = glyph_prompt_label(normalize_planet_name(planet_b)) or planet_b
    ga = canonical_glyph_char(planet_a) or ""
    gb = canonical_glyph_char(planet_b) or ""

    lines = [
        "[CATSTYLE REFERENCE IMAGE ROLES v1] Use supplied reference crops with these roles:",
    ]
    if style_reference_present:
        lines.append(
            "**Image A** = main style / scene / character DNA anchor (premium CG catplanet bodies, arena scale, "
            "lighting, cloth texture—NOT for copying misplaced glyphs from the full scene)."
        )
    letter_b = "B" if style_reference_present else "A"
    letter_c = "C" if style_reference_present else "B"
    if glyph_ref_planet_a:
        lines.append(
            f"**Image {letter_b}** = narrow **left/port faction banner glyph** reference for **{la} ({ga})** only—"
            "copy the **canonical heraldic glyph shape painted into fabric** (folds, gold paint, embroidery); "
            "do not paste as a floating sticker; do not copy unrelated scene elements."
        )
    if glyph_ref_planet_b:
        lines.append(
            f"**Image {letter_c}** = narrow **right/starboard faction banner glyph** reference for **{lb} ({gb})** only—"
            "same cloth-integrated heraldic rules as the port banner."
        )
    lines.append(
        f"Render **{ga}** only on the **left/port** banner and **{gb}** only on the **right/starboard** banner. "
        "Ignore glyph marks on characters, props, or rims in Image A—B/C define the correct banner glyphs."
    )
    return " ".join(lines)


def build_banner_glyph_reference_assist(
    planet_a: str,
    planet_b: str,
    *,
    style_reference_image_path: str | None = None,
    explicit_glyph_a: str | None = None,
    explicit_glyph_b: str | None = None,
    use_auto_discovery: bool = True,
) -> dict[str, Any] | None:
    """Metadata + prompt block for pack/jobs when any banner glyph reference is available."""
    glyph_a, glyph_b = resolve_banner_glyph_reference_paths(
        planet_a,
        planet_b,
        explicit_planet_a=explicit_glyph_a,
        explicit_planet_b=explicit_glyph_b,
        use_auto_discovery=use_auto_discovery,
    )
    style_path = _resolve_path(style_reference_image_path) if style_reference_image_path else None
    roles = format_banner_glyph_reference_roles_block(
        planet_a,
        planet_b,
        style_reference_present=bool(style_path),
        glyph_ref_planet_a=glyph_a,
        glyph_ref_planet_b=glyph_b,
    )
    if not roles and not glyph_a and not glyph_b:
        return None
    return {
        "version": "catstyle-banner-glyph-reference-assist-v1",
        "planet_a": normalize_planet_name(planet_a),
        "planet_b": normalize_planet_name(planet_b),
        "style_reference_image_path": style_path,
        "banner_glyph_reference_planet_a_path": glyph_a,
        "banner_glyph_reference_planet_b_path": glyph_b,
        "reference_roles_prompt_block": roles,
        "banner_only_glyph_discipline_block": BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK,
    }


__all__ = [
    "BANNER_ONLY_NO_CHEST_BADGE_BLOCK",
    "BANNER_ONLY_ART_DIRECTION_IDENTITY_CUE",
    "BANNER_ONLY_FORBIDDEN_IDENTITY_PHRASES",
    "BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK",
    "BANNER_ONLY_GLYPH_NEGATIVE_EXTRAS",
    "banner_only_glyph_mode_active",
    "banner_only_prompt_forbidden_phrases",
    "build_banner_glyph_reference_assist",
    "default_banner_glyph_reference_path",
    "format_banner_glyph_reference_roles_block",
    "identity_marker_block_forbidden_in_banner_only",
    "resolve_banner_glyph_reference_paths",
    "rewrite_art_direction_for_banner_only",
    "sanitize_assembled_prompt_for_banner_only",
    "sanitize_marker_field_for_banner_only",
]
