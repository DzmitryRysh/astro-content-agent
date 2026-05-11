"""Deterministic approved style-reference registry for Catstyle image jobs (local only, v1)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name


def catstyle_repo_root() -> Path:
    """Repository root (parent of the ``astro_content_agent`` package)."""
    return Path(__file__).resolve().parents[3]


def approved_references_json_path() -> Path:
    """Canonical local registry data source."""
    return catstyle_repo_root() / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"


class ApprovedReferenceEntry(BaseModel):
    """One approved reference image keyed by planet pair + aspect + mode."""

    registry_key: str = Field(..., description="Stable unique key for this row.")
    planet_a: str = Field(..., description="Planet A (English title case after normalize).")
    planet_b: str = Field(..., description="Planet B (English title case after normalize).")
    aspect_type: str = Field(..., description="Major aspect, e.g. square (matched case-insensitive).")
    mode: str = Field(..., description="tension | compensation | mixed | flow (matched case-insensitive).")
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


def read_registry_entries(path: Path | None = None) -> list[ApprovedReferenceEntry]:
    """Load entries from JSON data source; empty list if file missing."""
    p = (path or approved_references_json_path()).expanduser().resolve()
    if not p.is_file():
        return []
    payload = json.loads(p.read_text(encoding="utf-8"))
    raw = payload.get("entries")
    if not isinstance(raw, list):
        raise ValueError(f"Invalid approved references JSON at {p}: missing list 'entries'.")
    return [ApprovedReferenceEntry.model_validate(x) for x in raw]


def write_registry_entries(path: Path | None, entries: list[ApprovedReferenceEntry]) -> Path:
    """Write registry entries to JSON (stable order by priority desc + registry_key)."""
    p = (path or approved_references_json_path()).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(entries, key=lambda e: (-e.priority, e.registry_key))
    payload = {
        "version": "catstyle-approved-references-v1",
        "entries": [e.model_dump(mode="json") for e in ordered],
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def load_approved_reference_registry() -> list[ApprovedReferenceEntry]:
    """Load local JSON-backed registry."""
    return read_registry_entries()


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
    "ApprovedReferenceEntry",
    "ResolvedApprovedReference",
    "approved_references_json_path",
    "catstyle_repo_root",
    "load_approved_reference_registry",
    "list_active_references",
    "normalize_pair_key",
    "read_registry_entries",
    "registry_entries_as_jsonable",
    "resolve_approved_reference",
    "write_registry_entries",
]
