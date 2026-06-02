"""Catstyle arena reference pool registry (environment-only plates v1)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root

DEFAULT_ARENA_POOL_KEY = "premium_cosmic_zodiac_arena_v2"


def arena_pools_json_path() -> Path:
    return catstyle_repo_root() / "astro_content_agent" / "content" / "catstyle" / "arena_pools.json"


class ArenaPoolCandidateEntry(BaseModel):
    pool_key: str = Field(..., description="Pool namespace, e.g. premium_cosmic_zodiac_arena_v2.")
    candidate_key: str = Field(..., description="Stable unique key within the pool.")
    image_path: str = Field(..., description="Path relative to repo root (POSIX slashes).")
    label: str = Field(default="", description="Short human label.")
    notes: str = Field(default="", description="Optional operator notes/tags.")
    active: bool = Field(default=True, description="Inactive rows are ignored.")


class ResolvedArenaPoolCandidate(BaseModel):
    pool_key: str
    candidate_key: str
    image_path: Path
    label: str
    notes: str


def _absolute_image_path(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    if p.is_absolute():
        return p.resolve()
    return (catstyle_repo_root() / p).resolve()


def read_arena_pool_entries(path: Path | None = None) -> list[ArenaPoolCandidateEntry]:
    p = (path or arena_pools_json_path()).expanduser().resolve()
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = data.get("entries") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        return []
    return [ArenaPoolCandidateEntry.model_validate(item) for item in raw]


def list_active_arena_pool_candidates(
    pool_key: str,
    *,
    registry: list[ArenaPoolCandidateEntry] | None = None,
) -> list[ArenaPoolCandidateEntry]:
    key = pool_key.strip()
    rows = registry if registry is not None else read_arena_pool_entries()
    matches = [e for e in rows if e.active and e.pool_key == key]
    matches.sort(key=lambda e: e.candidate_key)
    return matches


def entry_to_resolved(entry: ArenaPoolCandidateEntry) -> ResolvedArenaPoolCandidate:
    return ResolvedArenaPoolCandidate(
        pool_key=entry.pool_key,
        candidate_key=entry.candidate_key,
        image_path=_absolute_image_path(entry.image_path),
        label=entry.label,
        notes=entry.notes,
    )


def resolve_arena_pool_candidate_entry(
    pool_key: str,
    candidate_key: str,
    *,
    registry: list[ArenaPoolCandidateEntry] | None = None,
) -> ResolvedArenaPoolCandidate | None:
    rows = registry if registry is not None else read_arena_pool_entries()
    for entry in rows:
        if entry.pool_key == pool_key and entry.candidate_key == candidate_key and entry.active:
            return entry_to_resolved(entry)
    return None


__all__ = [
    "DEFAULT_ARENA_POOL_KEY",
    "ArenaPoolCandidateEntry",
    "ResolvedArenaPoolCandidate",
    "arena_pools_json_path",
    "list_active_arena_pool_candidates",
    "read_arena_pool_entries",
    "resolve_arena_pool_candidate_entry",
]
