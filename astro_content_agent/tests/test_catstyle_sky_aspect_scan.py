"""Tests for Catstyle sky aspect scan v0 (mocked ephemeris)."""
from __future__ import annotations

from datetime import date

from astro_content_agent.astro.ephemeris import PlanetPosition, sign_for_longitude
from astro_content_agent.content.catstyle.models import CatstyleCandidate
from astro_content_agent.services.content.catstyle_sky_aspect_scan import (
    CATSTYLE_SKY_ORB_CONFIG,
    detect_catstyle_transit_aspects,
    scan_catstyle_sky_aspects,
)


def _P(name: str, lon: float) -> PlanetPosition:
    sign, sd = sign_for_longitude(lon)
    return PlanetPosition(
        name=name,
        longitude=lon,
        sign=sign,
        sign_degree=sd,
        retrograde=False,
        speed=0.0,
    )


def _mock_positions_three_transits(_day: date) -> dict[str, PlanetPosition]:
    """Deterministic chart: Pluto+Moon conj, Saturn+Mars sq, Neptune+Mercury sq; no Jupiter-personal hits."""
    return {
        "Sun": _P("Sun", 1.0),
        "Moon": _P("Moon", 120.0),
        "Mercury": _P("Mercury", 110.0),
        "Venus": _P("Venus", 71.0),
        "Mars": _P("Mars", 90.0),
        "Jupiter": _P("Jupiter", 15.0),
        "Saturn": _P("Saturn", 0.0),
        "Uranus": _P("Uranus", 205.0),
        "Neptune": _P("Neptune", 200.0),
        "Pluto": _P("Pluto", 120.4),
    }


def test_detect_aspects_pluto_moon_saturn_mars_neptune_mercury() -> None:
    pos = _mock_positions_three_transits(date(2026, 1, 1))
    cands = detect_catstyle_transit_aspects(pos)
    keys = {(c["planet_a"], c["planet_b"], c["aspect_type"]) for c in cands}
    keys |= {(c["planet_b"], c["planet_a"], c["aspect_type"]) for c in cands}
    assert ("Pluto", "Moon", "conjunction") in keys or ("Moon", "Pluto", "conjunction") in keys
    assert ("Saturn", "Mars", "square") in keys or ("Mars", "Saturn", "square") in keys
    assert ("Neptune", "Mercury", "square") in keys or ("Mercury", "Neptune", "square") in keys
    pm = next(c for c in cands if "Pluto" in (c["planet_a"], c["planet_b"]) and "Moon" in (c["planet_a"], c["planet_b"]))
    assert pm["aspect_type"] == "conjunction"
    assert 0.0 <= float(pm["orb"]) < 1.0


def test_detect_excludes_outer_outer_and_personal_personal() -> None:
    from astro_content_agent.content.catstyle.transit_pair_seed_v0 import OUTER_PLANETS, PERSONAL_PLANETS

    pos = _mock_positions_three_transits(date(2026, 1, 1))
    cands = detect_catstyle_transit_aspects(pos)
    for c in cands:
        a, b = c["planet_a"], c["planet_b"]
        assert not (a in OUTER_PLANETS and b in OUTER_PLANETS)
        assert not (a in PERSONAL_PLANETS and b in PERSONAL_PLANETS)


def test_scan_passes_orb_to_ranker() -> None:
    result = scan_catstyle_sky_aspects(date(2026, 1, 1), compute_positions_fn=_mock_positions_three_transits)
    assert result.unsupported == []
    assert len(result.ranked) >= 3
    orbs = {tuple(sorted((c.planet_a, c.planet_b), key=str.lower)): c.orb for c in result.ranked}
    assert orbs[tuple(sorted(("Pluto", "Moon"), key=str.lower))] is not None
    assert all(c.orb is not None for c in result.ranked)


def test_scan_empty_when_no_aspects_in_band() -> None:
    def _sparse(_d: date) -> dict[str, PlanetPosition]:
        names = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        return {n: _P(n, (i * 23.0) % 360.0) for i, n in enumerate(names)}

    # Zero-width orbs: only mathematically exact aspects count (none on this synthetic wheel).
    zero_orb = {k: (v[0], 0.0) for k, v in CATSTYLE_SKY_ORB_CONFIG.items()}
    result = scan_catstyle_sky_aspects(
        date(2026, 6, 1), compute_positions_fn=_sparse, orb_config=zero_orb
    )
    assert result.ranked == []


def test_orb_config_matches_spec() -> None:
    assert CATSTYLE_SKY_ORB_CONFIG["conjunction"] == (0.0, 3.0)
    assert CATSTYLE_SKY_ORB_CONFIG["sextile"] == (60.0, 2.0)
    assert CATSTYLE_SKY_ORB_CONFIG["square"] == (90.0, 3.0)
