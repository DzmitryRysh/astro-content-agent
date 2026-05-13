"""Merge day-window sky timing into a manual-override primary candidate (same ephemeris path as daily scan)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.content.catstyle.models import CatstyleCandidate
from astro_content_agent.services.content.catstyle_prompt_generator import normalize_planet_name
from astro_content_agent.services.content.catstyle_sky_aspect_scan import scan_catstyle_sky_aspect_windows


def _pair_norm(pa: str, pb: str) -> frozenset[str]:
    a = normalize_planet_name(pa).strip().lower()
    b = normalize_planet_name(pb).strip().lower()
    return frozenset({a, b})


def merge_manual_override_day_window_into_primary(
    primary: dict[str, Any],
    *,
    day: date,
    request_planet_a: str,
    request_planet_b: str,
    request_aspect_type: str,
    step_hours: int,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> bool:
    """
    Populate ``primary`` with orb / UTC window hour fields when the day-window scan
    contains the same outer↔personal pair and aspect type as the manual request.

    Returns True when a row was merged, False when the scan had no matching aspect.
    """
    want_pair = _pair_norm(request_planet_a, request_planet_b)
    want_asp = str(request_aspect_type or "").strip().lower()
    if not want_asp:
        primary["manual_override_sky_timing_match"] = False
        return False

    ranking = scan_catstyle_sky_aspect_windows(
        day,
        step_hours=step_hours,
        compute_positions_fn=compute_positions_fn,
        orb_config=orb_config,
    )
    match: CatstyleCandidate | None = None
    for c in ranking.ranked:
        if _pair_norm(c.planet_a, c.planet_b) != want_pair:
            continue
        if str(c.aspect_type or "").strip().lower() != want_asp:
            continue
        match = c
        break

    if match is None:
        primary["manual_override_sky_timing_match"] = False
        return False

    payload = match.model_dump(mode="json")
    for key in (
        "orb",
        "closest_hour_utc",
        "window_first_seen_hour_utc",
        "window_last_seen_hour_utc",
        "window_samples_seen",
        "is_moon_aspect",
    ):
        if key in payload and payload[key] is not None:
            primary[key] = payload[key]

    wf = primary.get("window_first_seen_hour_utc")
    wl = primary.get("window_last_seen_hour_utc")
    if wf is not None:
        primary["window_start_hour_utc"] = int(wf)
    if wl is not None:
        primary["window_end_hour_utc"] = int(wl)

    primary["manual_override_sky_timing_match"] = True
    return True


__all__ = ["merge_manual_override_day_window_into_primary"]
