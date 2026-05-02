"""Tests for Catstyle candidate ranker v0 (deterministic)."""
from __future__ import annotations

import pytest

from astro_content_agent.services.content.catstyle_candidate_ranker import rank_catstyle_candidates


def test_pluto_venus_conjunction_ranks_above_jupiter_mercury_trine() -> None:
    candidates = [
        {"planet_a": "Jupiter", "planet_b": "Mercury", "aspect_type": "trine"},
        {"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "conjunction"},
    ]
    result = rank_catstyle_candidates(candidates)
    assert len(result.ranked) == 2
    assert result.ranked[0].planet_a in ("Pluto", "Venus")
    assert result.ranked[0].total_score >= result.ranked[1].total_score
    assert result.ranked[0].planet_a == "Pluto" and result.ranked[0].planet_b == "Venus"


def _pair_key(c_planet_a: str, c_planet_b: str) -> tuple[str, str]:
    return tuple(sorted((c_planet_a, c_planet_b), key=str.lower))


def test_uranus_moon_and_mars_neptune_rank_high_among_five() -> None:
    candidates = [
        {"planet_a": "Jupiter", "planet_b": "Mercury", "aspect_type": "conjunction"},
        {"planet_a": "Saturn", "planet_b": "Venus", "aspect_type": "conjunction"},
        {"planet_a": "Mars", "planet_b": "Neptune", "aspect_type": "square"},
        {"planet_a": "Uranus", "planet_b": "Moon", "aspect_type": "opposition"},
        {"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "square"},
    ]
    result = rank_catstyle_candidates(candidates)
    totals_by_pair = {_pair_key(c.planet_a, c.planet_b): c.total_score for c in result.ranked}
    assert totals_by_pair[_pair_key("Moon", "Uranus")] >= 35
    assert totals_by_pair[_pair_key("Mars", "Neptune")] >= 35
    tops = [_pair_key(c.planet_a, c.planet_b) for c in result.ranked[:3]]
    assert _pair_key("Pluto", "Venus") in tops
    assert _pair_key("Moon", "Uranus") in tops
    assert _pair_key("Mars", "Neptune") in tops


def test_jupiter_mercury_trine_recommends_compensation_or_mixed() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Jupiter", "planet_b": "Mercury", "aspect_type": "trine"}]
    )
    assert len(result.ranked) == 1
    assert result.ranked[0].mode_recommendation in ("compensation", "mixed")


def test_hard_aspect_nudges_saturn_venus_from_mixed_to_tension() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Saturn", "planet_b": "Venus", "aspect_type": "conjunction"}]
    )
    assert result.ranked[0].mode_recommendation == "tension"


def test_square_nudges_jupiter_mercury_toward_tension() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Jupiter", "planet_b": "Mercury", "aspect_type": "square"}]
    )
    assert result.ranked[0].mode_recommendation == "tension"


def test_pluto_venus_conjunction_recommends_tension() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "conjunction"}]
    )
    assert result.ranked[0].mode_recommendation == "tension"


def test_unsupported_pair_not_ranked_lists_unsupported() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Sun", "planet_b": "Mars", "aspect_type": "conjunction"}]
    )
    assert result.ranked == []
    assert len(result.unsupported) == 1
    assert "library" in result.unsupported[0].reason.lower()


def test_unknown_planet_goes_unsupported() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "NotAPlanet", "planet_b": "Venus", "aspect_type": "trine"}]
    )
    assert result.ranked == []
    assert len(result.unsupported) == 1


def test_missing_field_goes_unsupported() -> None:
    result = rank_catstyle_candidates([{"planet_a": "Pluto"}])
    assert result.ranked == []
    assert len(result.unsupported) == 1


def test_scores_and_angle_populated() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Mars", "planet_b": "Neptune", "aspect_type": "opposition"}]
    )
    c = result.ranked[0]
    assert c.visual_score == 9 and c.clarity_score == 10
    assert "fog" in c.recommended_scene_angle.lower() or "steam" in c.recommended_scene_angle.lower()
