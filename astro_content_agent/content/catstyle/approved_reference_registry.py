"""Deterministic approved style-reference registry for Catstyle image jobs (local only, v1)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name


def catstyle_repo_root() -> Path:
    """Repository root (parent of the ``astro_content_agent`` package)."""
    return Path(__file__).resolve().parents[3]


class ApprovedReferenceEntry(BaseModel):
    """One approved reference image keyed by planet pair + aspect + mode."""

    registry_key: str = Field(..., description="Stable unique key for this row.")
    planet_a: str = Field(..., description="Planet A (English title case after normalize).")
    planet_b: str = Field(..., description="Planet B (English title case after normalize).")
    aspect_type: str = Field(..., description="Major aspect, e.g. square (matched case-insensitive).")
    mode: str = Field(..., description="tension | compensation | mixed (matched case-insensitive).")
    image_path: str = Field(
        ...,
        description="Path relative to repo root, POSIX slashes (e.g. references/catstyle_moon_saturn_approved.png).",
    )
    label: str = Field(default="", description="Short human label for listings.")
    notes: str = Field(default="", description="Optional operator notes.")
    priority: int = Field(default=0, description="Higher wins when multiple rows match.")
    active: bool = Field(default=True, description="Inactive entries are ignored by resolve.")


class ResolvedApprovedReference(BaseModel):
    """Result of a successful registry lookup."""

    registry_key: str
    image_path: str = Field(description="Absolute resolved filesystem path.")
    label: str
    notes: str
    priority: int


# v1 seed data — extend by appending rows (deterministic order for equal priority: registry_key).
APPROVED_REFERENCE_REGISTRY_V1: tuple[ApprovedReferenceEntry, ...] = (
    ApprovedReferenceEntry(
        registry_key="moon_saturn_square_tension_v1",
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        image_path="references/catstyle_moon_saturn_approved.png",
        label="Moon square Saturn (tension)",
        notes="Approved softness-vs-structure reference.",
        priority=100,
        active=True,
    ),
    ApprovedReferenceEntry(
        registry_key="pluto_mars_square_tension_v1",
        planet_a="Pluto",
        planet_b="Mars",
        aspect_type="square",
        mode="tension",
        image_path="references/catstyle_pluto_mars_approved.png",
        label="Pluto square Mars (tension)",
        notes="Approved pressure/control vs strike reference.",
        priority=100,
        active=True,
    ),
    ApprovedReferenceEntry(
        registry_key="jupiter_mars_square_tension_v1",
        planet_a="Jupiter",
        planet_b="Mars",
        aspect_type="square",
        mode="tension",
        image_path="references/catstyle_jupiter_mars_approved.png",
        label="Jupiter square Mars (tension)",
        notes="Approved expansion vs kinetic reference.",
        priority=100,
        active=True,
    ),
)


def load_approved_reference_registry() -> list[ApprovedReferenceEntry]:
    """Return a copy of the built-in registry (deterministic, immutable source)."""
    return list(APPROVED_REFERENCE_REGISTRY_V1)


def normalize_pair_key(planet_a: str, planet_b: str, aspect_type: str, mode: str) -> str:
    """
    Canonical comparison key: sorted normalized planet names, lowercase aspect and mode.

    Order-insensitive for planets: Moon+Saturn and Saturn+Moon yield the same key.
    """
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    a, b = sorted((pa.lower(), pb.lower()))
    asp = (aspect_type or "").strip().lower()
    mo = (mode or "").strip().lower()
    return f"{a}|{b}|{asp}|{mo}"


def _entry_match_key(entry: ApprovedReferenceEntry) -> str:
    return normalize_pair_key(entry.planet_a, entry.planet_b, entry.aspect_type, entry.mode)


def _absolute_image_path(rel: str) -> str:
    rel_clean = rel.strip().replace("\\", "/")
    return str((catstyle_repo_root() / Path(rel_clean)).resolve())


def resolve_approved_reference(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    *,
    registry: list[ApprovedReferenceEntry] | None = None,
) -> ResolvedApprovedReference | None:
    """
    Return the winning approved reference for this aspect context, or ``None``.

    Tie-break: highest ``priority``, then lexicographically smallest ``registry_key``.
    """
    want = normalize_pair_key(planet_a, planet_b, aspect_type, mode)
    rows = registry if registry is not None else load_approved_reference_registry()
    matches = [e for e in rows if e.active and _entry_match_key(e) == want]
    if not matches:
        return None
    matches.sort(key=lambda e: (-e.priority, e.registry_key))
    winner = matches[0]
    return ResolvedApprovedReference(
        registry_key=winner.registry_key,
        image_path=_absolute_image_path(winner.image_path),
        label=winner.label,
        notes=winner.notes,
        priority=winner.priority,
    )


def list_active_references() -> list[ApprovedReferenceEntry]:
    """All active registry rows, sorted by priority desc then registry_key."""
    rows = [e for e in load_approved_reference_registry() if e.active]
    rows.sort(key=lambda e: (-e.priority, e.registry_key))
    return rows


def registry_entries_as_jsonable() -> list[dict[str, Any]]:
    """For ``--json`` CLI: serialized active entries with resolved absolute paths."""
    out: list[dict[str, Any]] = []
    root = catstyle_repo_root()
    for e in list_active_references():
        d = e.model_dump(mode="json")
        d["image_path_absolute"] = str((root / Path(e.image_path.replace("\\", "/"))).resolve())
        d["pair_aspect_mode"] = f"{e.planet_a} {e.aspect_type} {e.planet_b} / {e.mode}"
        out.append(d)
    return out


__all__ = [
    "APPROVED_REFERENCE_REGISTRY_V1",
    "ApprovedReferenceEntry",
    "ResolvedApprovedReference",
    "catstyle_repo_root",
    "load_approved_reference_registry",
    "list_active_references",
    "normalize_pair_key",
    "registry_entries_as_jsonable",
    "resolve_approved_reference",
]
