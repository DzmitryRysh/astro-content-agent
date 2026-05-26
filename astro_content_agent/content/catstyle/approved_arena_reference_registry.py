"""Catstyle approved arena/environment reference registry (aspect-agnostic v1)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root

DEFAULT_ARENA_REGISTRY_KEY = "cosmic_zodiac_arena_premium_v1"
DEFAULT_ARENA_REFERENCE_FILENAME = "catstyle_cosmic_zodiac_arena_premium_v1_approved.png"


def approved_arena_references_json_path() -> Path:
    """JSON registry beside pair-specific ``approved_references.json``."""
    return catstyle_repo_root() / "astro_content_agent" / "content" / "catstyle" / "approved_arena_references.json"


class ApprovedArenaReferenceEntry(BaseModel):
    """One approved arena/environment reference image (reusable across all aspects)."""

    registry_key: str = Field(..., description="Stable unique key for this row.")
    image_path: str = Field(
        ...,
        description="Path relative to repo root, POSIX slashes (e.g. references/catstyle_arena_....png).",
    )
    label: str = Field(default="", description="Short human label for listings.")
    notes: str = Field(default="", description="Optional operator notes.")
    priority: int = Field(default=0, description="Higher wins when multiple rows are active.")
    active: bool = Field(default=True, description="Inactive entries are ignored by resolve.")


class ResolvedArenaReference(BaseModel):
    """Result of a successful arena registry lookup."""

    registry_key: str
    image_path: Path
    label: str
    notes: str
    priority: int


def _absolute_image_path(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    if p.is_absolute():
        return p.resolve()
    return (catstyle_repo_root() / p).resolve()


def read_arena_registry_entries(path: Path | None = None) -> list[ApprovedArenaReferenceEntry]:
    p = (path or approved_arena_references_json_path()).expanduser().resolve()
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = data.get("entries") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        return []
    return [ApprovedArenaReferenceEntry.model_validate(item) for item in raw]


def write_arena_registry_entries(
    path: Path,
    entries: list[ApprovedArenaReferenceEntry],
    *,
    version: str = "catstyle-approved-arena-reference-v1",
) -> None:
    p = path.expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "version": version,
        "entries": [e.model_dump(mode="json") for e in entries],
    }
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_approved_arena_reference_registry() -> list[ApprovedArenaReferenceEntry]:
    return read_arena_registry_entries()


def resolve_approved_arena_reference(
    *,
    registry: list[ApprovedArenaReferenceEntry] | None = None,
) -> ResolvedArenaReference | None:
    """Return the winning active arena reference, or ``None``."""
    rows = registry if registry is not None else load_approved_arena_reference_registry()
    matches = [e for e in rows if e.active]
    if not matches:
        return None
    matches.sort(key=lambda e: (-e.priority, e.registry_key))
    winner = matches[0]
    return ResolvedArenaReference(
        registry_key=winner.registry_key,
        image_path=_absolute_image_path(winner.image_path),
        label=winner.label,
        notes=winner.notes,
        priority=winner.priority,
    )


def list_active_arena_references() -> list[ApprovedArenaReferenceEntry]:
    rows = [e for e in load_approved_arena_reference_registry() if e.active]
    rows.sort(key=lambda e: (-e.priority, e.registry_key))
    return rows


__all__ = [
    "DEFAULT_ARENA_REFERENCE_FILENAME",
    "DEFAULT_ARENA_REGISTRY_KEY",
    "ApprovedArenaReferenceEntry",
    "ResolvedArenaReference",
    "approved_arena_references_json_path",
    "list_active_arena_references",
    "load_approved_arena_reference_registry",
    "read_arena_registry_entries",
    "resolve_approved_arena_reference",
    "write_arena_registry_entries",
]
