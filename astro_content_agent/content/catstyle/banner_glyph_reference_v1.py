"""Banner-only glyph reference assist for Catstyle image prompts (v1)."""
from __future__ import annotations

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
    "**Do not** place planetary glyphs on chest, armor, medallions, accessories, portal rims, floating symbols, "
    "foreheads, shields-as-stickers, or background clutter."
)

BANNER_ONLY_GLYPH_NEGATIVE_EXTRAS: tuple[str, ...] = (
    "planetary glyph on chest or armor",
    "glyph on medallion accessory or portal rim",
    "extra planetary glyphs outside faction banners",
)

_DEFAULT_BANNER_GLYPH_REL_DIR = "references/banner_glyphs"


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
    "BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK",
    "BANNER_ONLY_GLYPH_NEGATIVE_EXTRAS",
    "build_banner_glyph_reference_assist",
    "default_banner_glyph_reference_path",
    "format_banner_glyph_reference_roles_block",
    "resolve_banner_glyph_reference_paths",
]
