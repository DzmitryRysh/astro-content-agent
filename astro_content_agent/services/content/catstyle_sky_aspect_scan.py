"""Catstyle v0/v1: real-sky outer→personal aspects for a date, then rank."""
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


def _call_compute_positions(
    fn: Callable[..., dict[str, PlanetPosition]],
    day: date,
    hour_utc: float,
) -> dict[str, PlanetPosition]:
    """Call ephemeris; support legacy 1-arg test fns that ignore hour."""
    try:
        return fn(day, hour_utc=hour_utc)
    except TypeError:
        return fn(day)


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


def _merge_window_key(aspect_type: str, planet_a: str, planet_b: str) -> tuple[str, str, str] | None:
    oriented = orient_outer_personal(planet_a, planet_b)
    if oriented is None:
        return None
    outer, personal = oriented
    return (aspect_type.strip().lower(), outer, personal)


def scan_catstyle_sky_aspect_windows(
    day: date,
    step_hours: int = 2,
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleCandidateRankingResult:
    """
    Sample the UTC calendar *day* every *step_hours* (0, 2, …, 22 by default).

    Merges repeated detections of the same (outer, personal, aspect_type), keeping
    ``orb`` = minimum orb seen, ``closest_hour_utc`` = hour where that minimum occurred,
    first/last seen hours, sample count, and ``is_moon_aspect`` when the personal planet is Moon.
    """
    fn = compute_positions_fn or compute_positions
    step = max(1, int(step_hours))
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}

    for hour in range(0, 24, step):
        positions = _call_compute_positions(fn, day, float(hour))
        for item in detect_catstyle_transit_aspects(positions, orb_config=orb_config):
            key = _merge_window_key(item["aspect_type"], item["planet_a"], item["planet_b"])
            if key is None:
                continue
            _, outer, personal = key
            orb = float(item["orb"])
            if key not in merged:
                merged[key] = {
                    "planet_a": outer,
                    "planet_b": personal,
                    "aspect_type": item["aspect_type"],
                    "min_orb": orb,
                    "closest_hour_utc": hour,
                    "first_seen_hour_utc": hour,
                    "last_seen_hour_utc": hour,
                    "samples_seen": 1,
                }
            else:
                m = merged[key]
                if orb < m["min_orb"]:
                    m["min_orb"] = orb
                    m["closest_hour_utc"] = hour
                m["first_seen_hour_utc"] = min(m["first_seen_hour_utc"], hour)
                m["last_seen_hour_utc"] = max(m["last_seen_hour_utc"], hour)
                m["samples_seen"] += 1

    if not merged:
        return CatstyleCandidateRankingResult(ranked=[], unsupported=[])

    candidates: list[dict[str, Any]] = []
    for m in merged.values():
        candidates.append(
            {
                "planet_a": m["planet_a"],
                "planet_b": m["planet_b"],
                "aspect_type": m["aspect_type"],
                "orb": m["min_orb"],
                "closest_hour_utc": m["closest_hour_utc"],
                "window_first_seen_hour_utc": m["first_seen_hour_utc"],
                "window_last_seen_hour_utc": m["last_seen_hour_utc"],
                "window_samples_seen": m["samples_seen"],
                "is_moon_aspect": m["planet_b"] == "Moon",
            }
        )

    return rank_catstyle_candidates(candidates)


def scan_catstyle_sky_aspects(
    day: date,
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleCandidateRankingResult:
    """
    Noon UTC snapshot only (legacy v0): one ``compute_positions`` call at 12:00 UTC.

    For Moon-sensitive days use ``scan_catstyle_sky_aspect_windows``.
    """
    fn = compute_positions_fn or compute_positions
    positions = _call_compute_positions(fn, day, 12.0)
    candidates = detect_catstyle_transit_aspects(positions, orb_config=orb_config)
    if not candidates:
        return CatstyleCandidateRankingResult(ranked=[], unsupported=[])
    return rank_catstyle_candidates(candidates)


__all__ = [
    "CATSTYLE_SKY_ORB_CONFIG",
    "detect_catstyle_transit_aspects",
    "scan_catstyle_sky_aspects",
    "scan_catstyle_sky_aspect_windows",
]
