"""Deterministic arena pool candidate selection for Catstyle image jobs."""
from __future__ import annotations

import hashlib
from typing import Final, Literal

from astro_content_agent.content.catstyle.arena_pool_registry_v1 import (
    ArenaPoolCandidateEntry,
    ResolvedArenaPoolCandidate,
    entry_to_resolved,
    list_active_arena_pool_candidates,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

ArenaPoolSelectionMode = Literal["stable_by_pair"]
DEFAULT_ARENA_POOL_SELECTION: Final[ArenaPoolSelectionMode] = "stable_by_pair"


def stable_pair_pool_index(
    *,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    pool_key: str,
    candidate_count: int,
) -> int:
    """Deterministic index in ``[0, candidate_count)`` from aspect pair + pool key."""
    if candidate_count < 1:
        raise ValueError("candidate_count must be >= 1")
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    asp = (aspect_type or "").strip().lower()
    m = (mode or "").strip().lower()
    blob = f"{pa}|{pb}|{asp}|{m}|{pool_key.strip()}"
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return int(digest, 16) % candidate_count


def select_arena_pool_candidate(
    pool_key: str,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    *,
    selection_mode: ArenaPoolSelectionMode = DEFAULT_ARENA_POOL_SELECTION,
    registry: list[ArenaPoolCandidateEntry] | None = None,
) -> ResolvedArenaPoolCandidate:
    """Pick one active candidate from ``pool_key`` (reproducible for stable_by_pair)."""
    if selection_mode != "stable_by_pair":
        raise ValueError(f"Unsupported arena_pool_selection: {selection_mode!r}")
    rows = list_active_arena_pool_candidates(pool_key, registry=registry)
    if not rows:
        raise ValueError(f"Arena pool {pool_key!r} has no active candidates")
    idx = stable_pair_pool_index(
        planet_a=planet_a,
        planet_b=planet_b,
        aspect_type=aspect_type,
        mode=mode,
        pool_key=pool_key,
        candidate_count=len(rows),
    )
    return entry_to_resolved(rows[idx])


__all__ = [
    "DEFAULT_ARENA_POOL_SELECTION",
    "ArenaPoolSelectionMode",
    "select_arena_pool_candidate",
    "stable_pair_pool_index",
]
