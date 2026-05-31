"""Catstyle approved per-planet character reference registry and prompt helpers (v1)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name


def approved_planet_references_json_path() -> Path:
    return catstyle_repo_root() / "astro_content_agent" / "content" / "catstyle" / "approved_planet_references.json"


def planet_reference_target_relpath(planet: str, registry_key: str) -> str:
    """Deterministic repo-relative path under ``references/``."""
    planet_slug = normalize_planet_name(planet).lower()
    key_slug = (registry_key or "default").strip().replace("-", "_").lower()
    return f"references/catstyle_planet_{planet_slug}_{key_slug}_approved.png"


class ApprovedPlanetReferenceEntry(BaseModel):
    registry_key: str
    planet: str
    image_path: str
    label: str = ""
    notes: str = ""
    priority: int = 0
    active: bool = True


class ResolvedPlanetReference(BaseModel):
    registry_key: str
    planet: str
    image_path: Path
    label: str
    notes: str
    priority: int


class PlanetReferenceResolveResult(BaseModel):
    """Graceful resolve outcome for one planet (may be missing)."""

    planet: str
    used: bool
    registry_key: str | None = None
    image_path: str | None = None
    label: str | None = None
    notes: str | None = None
    priority: int | None = None
    source: str = "none"
    missing_reason: str | None = None

    def to_manifest_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def _absolute_image_path(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    if p.is_absolute():
        return p.resolve()
    return (catstyle_repo_root() / p).resolve()


def read_planet_registry_entries(path: Path | None = None) -> list[ApprovedPlanetReferenceEntry]:
    p = (path or approved_planet_references_json_path()).expanduser().resolve()
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = data.get("entries") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        return []
    return [ApprovedPlanetReferenceEntry.model_validate(item) for item in raw]


def write_planet_registry_entries(
    path: Path,
    entries: list[ApprovedPlanetReferenceEntry],
    *,
    version: str = "catstyle-approved-planet-reference-v1",
) -> None:
    p = path.expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(entries, key=lambda e: (-e.priority, e.registry_key))
    payload: dict[str, Any] = {
        "version": version,
        "entries": [e.model_dump(mode="json") for e in ordered],
    }
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_approved_planet_reference_registry() -> list[ApprovedPlanetReferenceEntry]:
    return read_planet_registry_entries()


def resolve_approved_planet_reference(
    planet: str,
    *,
    registry: list[ApprovedPlanetReferenceEntry] | None = None,
) -> ResolvedPlanetReference | None:
    """Return highest-priority active reference for ``planet``, or ``None``."""
    planet_norm = normalize_planet_name(planet)
    rows = registry if registry is not None else load_approved_planet_reference_registry()
    matches = [
        e for e in rows if e.active and normalize_planet_name(e.planet) == planet_norm
    ]
    if not matches:
        return None
    matches.sort(key=lambda e: (-e.priority, e.registry_key))
    winner = matches[0]
    return ResolvedPlanetReference(
        registry_key=winner.registry_key,
        planet=planet_norm,
        image_path=_absolute_image_path(winner.image_path),
        label=winner.label,
        notes=winner.notes,
        priority=winner.priority,
    )


def resolve_planet_reference(planet: str) -> PlanetReferenceResolveResult:
    """Resolve one planet reference; never raises when missing."""
    planet_norm = normalize_planet_name(planet)
    hit = resolve_approved_planet_reference(planet_norm)
    if hit is None:
        return PlanetReferenceResolveResult(
            planet=planet_norm,
            used=False,
            source="none",
            missing_reason="no_active_registry_entry",
        )
    if not hit.image_path.is_file():
        return PlanetReferenceResolveResult(
            planet=planet_norm,
            used=False,
            registry_key=hit.registry_key,
            image_path=str(hit.image_path),
            label=hit.label,
            notes=hit.notes,
            priority=hit.priority,
            source="registry_missing_file",
            missing_reason="registry_file_not_found",
        )
    return PlanetReferenceResolveResult(
        planet=planet_norm,
        used=True,
        registry_key=hit.registry_key,
        image_path=str(hit.image_path),
        label=hit.label,
        notes=hit.notes,
        priority=hit.priority,
        source="planet_registry",
    )


def resolve_planet_references_for_pair(planet_a: str, planet_b: str) -> dict[str, Any]:
    """Resolve both planets for manifests and image jobs."""
    pa = resolve_planet_reference(planet_a)
    pb = resolve_planet_reference(planet_b)
    return {
        "planet_a": pa.to_manifest_dict(),
        "planet_b": pb.to_manifest_dict(),
        "any_used": pa.used or pb.used,
    }


def list_active_planet_references_grouped() -> dict[str, list[ApprovedPlanetReferenceEntry]]:
    grouped: dict[str, list[ApprovedPlanetReferenceEntry]] = {}
    for e in load_approved_planet_reference_registry():
        if not e.active:
            continue
        key = normalize_planet_name(e.planet)
        grouped.setdefault(key, []).append(e)
    for planet in grouped:
        grouped[planet].sort(key=lambda x: (-x.priority, x.registry_key))
    return grouped


def list_resolved_winners_by_planet() -> dict[str, ResolvedPlanetReference | None]:
    grouped = list_active_planet_references_grouped()
    return {
        planet: resolve_approved_planet_reference(planet, registry=entries)
        for planet, entries in grouped.items()
    }


def format_catstyle_modular_reference_roles_prefix(
    *,
    arena_reference_present: bool,
    planet_a_reference_present: bool,
    planet_b_reference_present: bool,
    pair_style_reference_present: bool,
    planet_a_name: str = "planet A",
    planet_b_name: str = "planet B",
    banner_glyph_a: bool = False,
    banner_glyph_b: bool = False,
) -> str:
    """
    Modular reference roles: A=arena, B=planet_a, C=planet_b, D=optional pair, then banner glyphs.
    """
    if not any(
        (
            arena_reference_present,
            planet_a_reference_present,
            planet_b_reference_present,
            pair_style_reference_present,
            banner_glyph_a,
            banner_glyph_b,
        )
    ):
        return ""
    lines = [
        "[CATSTYLE REFERENCE IMAGE ROLES v3] When the image API accepts multiple reference images:",
    ]
    letter = ord("A")
    if arena_reference_present:
        lines.append(
            "**Image A** = **approved arena/environment reference ONLY**—controls **coliseum brightness**, "
            "**illuminated arches**, **tier depth**, **rich Milky Way sky**, **Earth disk**, **zodiac floor**—"
            "**do NOT** copy characters, poses, planet colors, or glyphs from Image A."
        )
        letter += 1
    if planet_a_reference_present:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = **approved {planet_a_name} character reference ONLY**—controls **{planet_a_name}** "
            "cat-planet body material, silhouette, palette, costume, and identity—**not** environment, "
            "**not** the other planet, **not** aspect pair mood override."
        )
        letter += 1
    if planet_b_reference_present:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = **approved {planet_b_name} character reference ONLY**—controls **{planet_b_name}** "
            "cat-planet body material, silhouette, palette, costume, and identity—**not** environment, "
            "**not** the other planet, **not** aspect pair mood override."
        )
        letter += 1
    if pair_style_reference_present:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = **optional pair/aspect approved reference**—**lower priority**; may inform "
            "**pair mood**, **choreography energy**, and campaign finish only—**must NOT** override Image A "
            "environment, **must NOT** override per-planet character identity on Images B/C, **must NOT** "
            "pull watercolor/cute ordinary cats or weak planet-cat identity over modular planet plates. "
            "**Aspect choreography comes from prompt text**, not from overriding planet identity."
        )
        letter += 1
    if banner_glyph_a:
        ch = chr(letter)
        lines.append(f"**Image {ch}** = narrow **left/port banner glyph** crop—heraldic cloth glyph only.")
        letter += 1
    if banner_glyph_b:
        ch = chr(letter)
        lines.append(f"**Image {ch}** = narrow **right/starboard banner glyph** crop—heraldic cloth glyph only.")
    lines.append(
        "**Modular priority lock:** arena (A) wins environment; planet references win their planet identity; "
        "optional pair reference is lowest-priority mood/choreography assist only."
    )
    return " ".join(lines)


def format_modular_reference_provider_priority_preamble(
    *,
    arena_present: bool,
    planet_a_present: bool,
    planet_b_present: bool,
    pair_style_present: bool,
    planet_a_name: str = "planet A",
    planet_b_name: str = "planet B",
) -> str:
    parts: list[str] = []
    if arena_present:
        parts.append(
            "**Image A (arena)** is authoritative for brighter coliseum, rich sky, Earth disk, and zodiac floor—"
            "never inherit a darker arena shell from other references."
        )
    if planet_a_present:
        parts.append(
            f"**Per-planet reference for {planet_a_name}** controls that cat-planet's identity only—"
            "not the arena shell or the other planet's body."
        )
    if planet_b_present:
        parts.append(
            f"**Per-planet reference for {planet_b_name}** controls that cat-planet's identity only—"
            "not the arena shell or the other planet's body."
        )
    if pair_style_present:
        parts.append(
            "**Optional pair/aspect reference** is lowest priority—pair mood/choreography assist only; "
            "do not let it override arena environment or per-planet character identity; "
            "aspect staging follows prompt text."
        )
    return " ".join(parts)


__all__ = [
    "ApprovedPlanetReferenceEntry",
    "PlanetReferenceResolveResult",
    "ResolvedPlanetReference",
    "approved_planet_references_json_path",
    "format_catstyle_modular_reference_roles_prefix",
    "format_modular_reference_provider_priority_preamble",
    "list_active_planet_references_grouped",
    "list_resolved_winners_by_planet",
    "load_approved_planet_reference_registry",
    "planet_reference_target_relpath",
    "read_planet_registry_entries",
    "resolve_approved_planet_reference",
    "resolve_planet_reference",
    "resolve_planet_references_for_pair",
    "write_planet_registry_entries",
]
