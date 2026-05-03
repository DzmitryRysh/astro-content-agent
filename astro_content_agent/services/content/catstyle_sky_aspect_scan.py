"""Catstyle v0: scan real-sky major aspects (outer→personal) for a date, then rank."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from astro_content_agent.astro.aspects import find_aspects
from astro_content_agent.astro.ephemeris import PlanetPosition, compute_positions
from astro_content_agent.content.catstyle.models import CatstyleCandidateRankingResult
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import orient_outer_personal
from astro_content_agent.services.content.catstyle_candidate_ranker import rank_catstyle_candidates

# (exact_angle_deg, max_orb_deg) — Catstyle sky scan v0 policy (tighter than engine default for content).
CATSTYLE_SKY_ORB_CONFIG: dict[str, tuple[float, float]] = {
    "conjunction": (0.0, 3.0),
    "sextile": (60.0, 2.0),
    "square": (90.0, 3.0),
    "trine": (120.0, 3.0),
    "opposition": (180.0, 3.0),
}


def _is_outer_to_personal_transit(p1: str, p2: str) -> bool:
    return orient_outer_personal(p1, p2) is not None


def detect_catstyle_transit_aspects(
    positions: dict[str, PlanetPosition],
    *,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> list[dict[str, Any]]:
    """
    Run major-aspect detection on *positions*, keep only social/outer-to-personal pairs.

    Each item is suitable for ``rank_catstyle_candidates`` (planet_a, planet_b, aspect_type, orb).
    """
    cfg = orb_config if orb_config is not None else CATSTYLE_SKY_ORB_CONFIG
    raw = find_aspects(positions, orb_config=cfg)
    candidates: list[dict[str, Any]] = []
    for r in raw:
        if not _is_outer_to_personal_transit(r.planet1, r.planet2):
            continue
        candidates.append(
            {
                "planet_a": r.planet1,
                "planet_b": r.planet2,
                "aspect_type": r.aspect,
                "orb": float(r.orb),
            }
        )
    return candidates


def scan_catstyle_sky_aspects(
    day: date,
    *,
    compute_positions_fn: Callable[[date], dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleCandidateRankingResult:
    """
    Compute positions for *day* (noon UTC, same convention as ``compute_positions``),
    detect outer→personal major aspects within Catstyle v0 orbs, rank via ``rank_catstyle_candidates``.

    Pass *compute_positions_fn* in tests to inject deterministic positions.
    """
    fn = compute_positions_fn or compute_positions
    positions = fn(day)
    candidates = detect_catstyle_transit_aspects(positions, orb_config=orb_config)
    if not candidates:
        return CatstyleCandidateRankingResult(ranked=[], unsupported=[])
    return rank_catstyle_candidates(candidates)


__all__ = [
    "CATSTYLE_SKY_ORB_CONFIG",
    "detect_catstyle_transit_aspects",
    "scan_catstyle_sky_aspects",
]
