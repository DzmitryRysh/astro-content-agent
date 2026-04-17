"""Tests for AstroEngineV1 and its supporting modules.

Covers:
- sign_for_longitude helper
- compute_positions (real ephemeris, determinism, known astronomical facts)
- _angular_distance and find_aspects (aspect detection, polarity, intensity)
- AstroEngineV1 (output contract, determinism, brand-independence, orb ordering,
  correct polarity, known transit on specific date)
"""
from __future__ import annotations

from datetime import date

import pytest

from astro_content_agent.astro.aspects import (
    ASPECT_CONFIG,
    AspectResult,
    _angular_distance,
    find_aspects,
)
from astro_content_agent.astro.engine import AstroEngineV1, EngineInput, MAX_SIGNALS
from astro_content_agent.astro.ephemeris import (
    PlanetPosition,
    ZODIAC_SIGNS,
    compute_positions,
    sign_for_longitude,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_pos(name: str, lon: float, retrograde: bool = False) -> PlanetPosition:
    sign, deg = sign_for_longitude(lon)
    return PlanetPosition(
        name=name,
        longitude=lon,
        sign=sign,
        sign_degree=deg,
        retrograde=retrograde,
        speed=-0.5 if retrograde else 1.0,
    )


def _engine_result(day: date = date(2026, 4, 7), brand: str = "test-brand"):
    return AstroEngineV1().generate_day(EngineInput(brand_profile_id=brand, day=day))


# ---------------------------------------------------------------------------
# sign_for_longitude
# ---------------------------------------------------------------------------

class TestSignForLongitude:
    def test_aries_at_zero(self):
        sign, deg = sign_for_longitude(0.0)
        assert sign == "Aries"
        assert abs(deg) < 0.001

    def test_taurus_at_30(self):
        assert sign_for_longitude(30.0)[0] == "Taurus"

    def test_gemini_at_60(self):
        assert sign_for_longitude(60.0)[0] == "Gemini"

    def test_pisces_near_360(self):
        assert sign_for_longitude(359.9)[0] == "Pisces"

    def test_wraps_at_360(self):
        s1, d1 = sign_for_longitude(0.0)
        s2, d2 = sign_for_longitude(360.0)
        assert s1 == s2

    def test_all_12_signs_reachable(self):
        signs = {sign_for_longitude(i * 30 + 0.5)[0] for i in range(12)}
        assert signs == set(ZODIAC_SIGNS)

    def test_mid_sign_degree(self):
        # 15° into Aries = Aries at 15°
        _, deg = sign_for_longitude(15.0)
        assert abs(deg - 15.0) < 0.001


# ---------------------------------------------------------------------------
# compute_positions (real ephemeris)
# ---------------------------------------------------------------------------

class TestComputePositions:
    def test_all_10_planets_present(self):
        expected = {"Sun", "Moon", "Mercury", "Venus", "Mars",
                    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
        assert set(compute_positions(date(2026, 4, 7)).keys()) == expected

    def test_longitudes_in_0_360(self):
        for name, pos in compute_positions(date(2026, 4, 7)).items():
            assert 0.0 <= pos.longitude < 360.0, f"{name}: {pos.longitude}"

    def test_signs_are_valid(self):
        for name, pos in compute_positions(date(2026, 4, 7)).items():
            assert pos.sign in ZODIAC_SIGNS, f"{name}: {pos.sign}"

    def test_deterministic_same_day(self):
        d = date(2026, 4, 7)
        p1 = compute_positions(d)
        p2 = compute_positions(d)
        for name in p1:
            assert p1[name].longitude == p2[name].longitude

    def test_moon_moves_between_weeks(self):
        # Moon travels ~13 deg/day; one week should differ by ~90 deg
        p1 = compute_positions(date(2026, 4, 7))
        p2 = compute_positions(date(2026, 4, 14))
        delta = abs(p1["Moon"].longitude - p2["Moon"].longitude) % 360.0
        if delta > 180.0:
            delta = 360.0 - delta
        assert delta > 5.0, f"Moon barely moved in a week: {delta:.2f}"

    def test_vernal_equinox_2026_sun_near_aries_zero(self):
        # 2026 equinox: Sun at ~359.89 deg (just before 0 Aries) at noon UTC
        lon = compute_positions(date(2026, 3, 20))["Sun"].longitude
        near_zero = lon > 357.0 or lon < 3.0
        assert near_zero, f"Expected Sun near 0 Aries on equinox, got {lon:.4f}"

    def test_sun_in_aries_early_april(self):
        assert compute_positions(date(2026, 4, 7))["Sun"].sign == "Aries"

    def test_retrograde_flag_is_bool(self):
        for pos in compute_positions(date(2026, 4, 7)).values():
            assert isinstance(pos.retrograde, bool)

    def test_sign_degree_in_0_30(self):
        for pos in compute_positions(date(2026, 4, 7)).values():
            assert 0.0 <= pos.sign_degree < 30.0, f"{pos.name}: {pos.sign_degree}"


# ---------------------------------------------------------------------------
# _angular_distance
# ---------------------------------------------------------------------------

class TestAngularDistance:
    def test_simple_30(self):
        assert abs(_angular_distance(30.0, 60.0) - 30.0) < 0.001

    def test_exact_opposition(self):
        assert abs(_angular_distance(0.0, 180.0) - 180.0) < 0.001

    def test_wrap_across_zero(self):
        # 350 to 10 = 20, not 340
        assert abs(_angular_distance(350.0, 10.0) - 20.0) < 0.001

    def test_symmetric(self):
        assert _angular_distance(30.0, 330.0) == _angular_distance(330.0, 30.0)

    def test_identical_is_zero(self):
        assert _angular_distance(45.0, 45.0) < 0.001

    def test_never_exceeds_180(self):
        import random
        rng = random.Random(42)
        for _ in range(200):
            a, b = rng.uniform(0, 360), rng.uniform(0, 360)
            assert _angular_distance(a, b) <= 180.0 + 1e-9


# ---------------------------------------------------------------------------
# find_aspects
# ---------------------------------------------------------------------------

class TestFindAspects:
    def test_exact_trine_detected(self):
        pos = {"Venus": _fake_pos("Venus", 0.0), "Saturn": _fake_pos("Saturn", 120.0)}
        aspects = find_aspects(pos)
        trines = [a for a in aspects if a.aspect == "trine"]
        assert len(trines) == 1
        assert trines[0].orb < 0.001
        assert trines[0].polarity == "harmonious"
        assert abs(trines[0].intensity - 1.0) < 0.001

    def test_exact_square_is_tense(self):
        pos = {"Mars": _fake_pos("Mars", 0.0), "Pluto": _fake_pos("Pluto", 90.0)}
        aspects = find_aspects(pos)
        squares = [a for a in aspects if a.aspect == "square"]
        assert len(squares) == 1
        assert squares[0].polarity == "tense"

    def test_exact_conjunction_is_neutral(self):
        pos = {"Sun": _fake_pos("Sun", 15.0), "Mercury": _fake_pos("Mercury", 15.0)}
        aspects = find_aspects(pos)
        conj = [a for a in aspects if a.aspect == "conjunction"]
        assert len(conj) == 1
        assert conj[0].polarity == "neutral"

    def test_exact_sextile_is_harmonious(self):
        pos = {"Venus": _fake_pos("Venus", 0.0), "Jupiter": _fake_pos("Jupiter", 60.0)}
        aspects = find_aspects(pos)
        sextiles = [a for a in aspects if a.aspect == "sextile"]
        assert sextiles[0].polarity == "harmonious"

    def test_exact_opposition_is_tense(self):
        pos = {"Moon": _fake_pos("Moon", 0.0), "Saturn": _fake_pos("Saturn", 180.0)}
        aspects = find_aspects(pos)
        opp = [a for a in aspects if a.aspect == "opposition"]
        assert opp[0].polarity == "tense"

    def test_trine_with_wide_orb_excluded(self):
        # trine max orb = 6 deg; 130 deg -> orb 10 -> excluded
        pos = {"Venus": _fake_pos("Venus", 0.0), "Saturn": _fake_pos("Saturn", 130.0)}
        trines = [a for a in find_aspects(pos) if a.aspect == "trine"]
        assert len(trines) == 0

    def test_trine_at_max_orb_included(self):
        # exactly at the trine max orb boundary (6 deg): 120 + 6 = 126 deg
        pos = {"Venus": _fake_pos("Venus", 0.0), "Saturn": _fake_pos("Saturn", 126.0)}
        trines = [a for a in find_aspects(pos) if a.aspect == "trine"]
        assert len(trines) == 1
        assert trines[0].intensity < 0.01

    def test_trine_just_outside_max_orb_excluded(self):
        # 120 + 6.1 = 126.1 deg -> orb 6.1 > 6.0 -> excluded
        pos = {"Venus": _fake_pos("Venus", 0.0), "Saturn": _fake_pos("Saturn", 126.1)}
        trines = [a for a in find_aspects(pos) if a.aspect == "trine"]
        assert len(trines) == 0

    def test_sorted_by_orb_ascending(self):
        pos = {
            "Sun":     _fake_pos("Sun", 0.0),
            "Moon":    _fake_pos("Moon", 119.0),    # trine orb ~1
            "Mercury": _fake_pos("Mercury", 180.0), # opposition exact
        }
        aspects = find_aspects(pos)
        orbs = [a.orb for a in aspects]
        assert orbs == sorted(orbs)

    def test_all_polarities(self):
        cases = [
            ("sextile", 60.0, "harmonious"),
            ("trine", 120.0, "harmonious"),
            ("square", 90.0, "tense"),
            ("opposition", 180.0, "tense"),
            ("conjunction", 0.0, "neutral"),
        ]
        for asp_name, angle, expected in cases:
            pos = {"A": _fake_pos("A", 0.0), "B": _fake_pos("B", angle)}
            matching = [a for a in find_aspects(pos) if a.aspect == asp_name]
            assert matching, f"{asp_name} at {angle} was not detected"
            assert matching[0].polarity == expected, f"{asp_name}: expected {expected}"


# ---------------------------------------------------------------------------
# AstroEngineV1
# ---------------------------------------------------------------------------

class TestAstroEngineV1:
    def test_version_string(self):
        assert AstroEngineV1().version == "v1.real"

    def test_deterministic_same_brand_and_day(self):
        r1 = _engine_result()
        r2 = _engine_result()
        assert [s.key for s in r1.signals] == [s.key for s in r2.signals]
        assert [s.orb for s in r1.signals] == [s.orb for s in r2.signals]

    def test_brand_independent(self):
        # Different brand_profile_id on same day must yield identical signals
        r1 = _engine_result(brand="brand-a")
        r2 = _engine_result(brand="brand-b")
        assert [s.key for s in r1.signals] == [s.key for s in r2.signals]

    def test_signal_count_within_max(self):
        result = _engine_result()
        assert 1 <= len(result.signals) <= MAX_SIGNALS

    def test_required_fields_present(self):
        for s in _engine_result().signals:
            assert s.key
            assert s.headline
            assert s.summary
            assert 0.0 <= s.intensity <= 1.0
            assert s.aspect_polarity in ("harmonious", "tense", "neutral")

    def test_v1_enrichment_fields_populated(self):
        for s in _engine_result().signals:
            assert s.planet1_sign in ZODIAC_SIGNS, f"bad sign: {s.planet1_sign}"
            assert s.planet2_sign in ZODIAC_SIGNS, f"bad sign: {s.planet2_sign}"
            assert s.orb is not None and s.orb >= 0.0
            assert isinstance(s.planet1_retrograde, bool)
            assert isinstance(s.planet2_retrograde, bool)

    def test_sorted_by_orb_ascending(self):
        orbs = [s.orb for s in _engine_result().signals if s.orb is not None]
        assert orbs == sorted(orbs), "Signals must be tightest-orb first"

    def test_no_duplicate_keys(self):
        keys = [s.key for s in _engine_result().signals]
        assert len(keys) == len(set(keys))

    def test_polarity_matches_aspect_in_key(self):
        for s in _engine_result().signals:
            if "trine" in s.key or "sextile" in s.key:
                assert s.aspect_polarity == "harmonious", s.key
            elif "square" in s.key or "opposition" in s.key:
                assert s.aspect_polarity == "tense", s.key
            elif "conjunction" in s.key:
                assert s.aspect_polarity == "neutral", s.key

    def test_engine_version_in_payload(self):
        assert _engine_result().engine_version == "v1.real"

    def test_known_tightest_transit_april_7_2026(self):
        # Sun trine Moon has orb ~0.42 deg on 2026-04-07 -- must be signal #1
        result = _engine_result(date(2026, 4, 7))
        top = result.signals[0]
        assert "sun" in top.key, f"Expected Sun as first planet: {top.key}"
        assert "trine" in top.key, f"Expected trine: {top.key}"
        assert "moon" in top.key, f"Expected Moon as second planet: {top.key}"
        assert top.orb is not None and top.orb < 1.0, f"Expected tight orb: {top.orb}"

    def test_different_dates_produce_different_signals(self):
        # 3 months apart should yield different top transits
        r1 = _engine_result(date(2026, 4, 7))
        r2 = _engine_result(date(2026, 7, 7))
        assert {s.key for s in r1.signals} != {s.key for s in r2.signals}

    def test_intensity_inversely_proportional_to_orb(self):
        # For any pair of signals, tighter orb must have >= intensity
        signals = _engine_result().signals
        if len(signals) < 2:
            pytest.skip("need at least 2 signals")
        for i in range(len(signals) - 1):
            s_tight = signals[i]
            s_wide = signals[i + 1]
            if s_tight.orb is not None and s_wide.orb is not None:
                assert s_tight.intensity >= s_wide.intensity, (
                    f"orb order vs intensity mismatch: "
                    f"{s_tight.key} orb={s_tight.orb} intensity={s_tight.intensity} vs "
                    f"{s_wide.key} orb={s_wide.orb} intensity={s_wide.intensity}"
                )

    def test_headline_format(self):
        for s in _engine_result().signals:
            parts = s.headline.split(" ")
            assert len(parts) == 3, f"Expected 'Planet aspect Planet': {s.headline}"
