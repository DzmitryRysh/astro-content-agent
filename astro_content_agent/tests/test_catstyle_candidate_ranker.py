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
    # v1 scores include aspect strength; deep pairs stay in the top band.
    candidates = [
        {"planet_a": "Jupiter", "planet_b": "Mercury", "aspect_type": "conjunction"},
        {"planet_a": "Saturn", "planet_b": "Venus", "aspect_type": "conjunction"},
        {"planet_a": "Mars", "planet_b": "Neptune", "aspect_type": "square"},
        {"planet_a": "Uranus", "planet_b": "Moon", "aspect_type": "opposition"},
        {"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "square"},
    ]
    result = rank_catstyle_candidates(candidates)
    totals_by_pair = {_pair_key(c.planet_a, c.planet_b): c.total_score for c in result.ranked}
    assert totals_by_pair[_pair_key("Moon", "Uranus")] >= 45
    assert totals_by_pair[_pair_key("Mars", "Neptune")] >= 45
    # v1: Saturn–Venus (conj) can tie Mars–Neptune (square) and win aspect tiebreak.
    top4 = [_pair_key(c.planet_a, c.planet_b) for c in result.ranked[:4]]
    assert _pair_key("Pluto", "Venus") in top4
    assert _pair_key("Moon", "Uranus") in top4
    assert _pair_key("Mars", "Neptune") in top4


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
    assert "outer" in result.unsupported[0].reason.lower()


def test_mercury_mars_personal_pair_unsupported() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Mercury", "planet_b": "Mars", "aspect_type": "square"}]
    )
    assert result.ranked == []
    assert len(result.unsupported) == 1


def test_all_25_transit_seeds_exist_and_shapes() -> None:
    from astro_content_agent.content.catstyle.transit_pair_seed_v0 import (
        is_seeded_transit_pair,
        list_transit_pair_seeds,
    )

    seeds = list_transit_pair_seeds()
    assert len(seeds) == 25
    for s in seeds:
        assert s.outer_planet and s.personal_planet
        assert s.core_tension.strip()
        assert s.visual_metaphor.strip()
        assert s.constructive_channel.strip()
        assert 3 <= len(s.suggested_scene_angles) <= 5
        assert len(s.avoid) >= 1
    assert is_seeded_transit_pair("Moon", "Pluto")
    assert is_seeded_transit_pair("Pluto", "Moon")


def test_pluto_venus_ranker_uses_deep_not_seed() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "conjunction"}]
    )
    assert result.ranked[0].source == "deep"
    assert "Deep library" in result.ranked[0].reason
    assert "cauldron" in result.ranked[0].recommended_scene_angle.lower()


def test_reason_includes_aspect_charge_phrase() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "conjunction", "orb": 0.5}]
    )
    assert "Aspect charge:" in result.ranked[0].reason
    assert "fusion" in result.ranked[0].reason.lower()


def test_conjunction_ranks_above_square_same_pair_same_orb() -> None:
    result = rank_catstyle_candidates(
        [
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "square", "orb": 1.0},
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "conjunction", "orb": 1.0},
        ]
    )
    assert result.ranked[0].aspect_type == "conjunction"
    assert result.ranked[1].aspect_type == "square"


def test_square_and_opposition_rank_above_trine_same_orb() -> None:
    result = rank_catstyle_candidates(
        [
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "trine", "orb": 1.0},
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "square", "orb": 1.0},
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "opposition", "orb": 1.0},
        ]
    )
    types = [c.aspect_type for c in result.ranked]
    assert types[0] == "opposition"
    assert types[1] == "square"
    assert types[2] == "trine"


def test_trine_ranks_above_sextile_same_orb() -> None:
    result = rank_catstyle_candidates(
        [
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "sextile", "orb": 1.0},
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "trine", "orb": 1.0},
        ]
    )
    assert result.ranked[0].aspect_type == "trine"
    assert result.ranked[1].aspect_type == "sextile"


def test_very_tight_trine_beats_loose_sextile() -> None:
    result = rank_catstyle_candidates(
        [
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "sextile", "orb": 2.8},
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "trine", "orb": 0.25},
        ]
    )
    assert result.ranked[0].aspect_type == "trine"


def test_sextile_does_not_outrank_tighter_square() -> None:
    result = rank_catstyle_candidates(
        [
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "sextile", "orb": 0.15},
            {"planet_a": "Neptune", "planet_b": "Sun", "aspect_type": "square", "orb": 0.4},
        ]
    )
    assert result.ranked[0].aspect_type == "square"


def test_pluto_moon_ranker_uses_seed() -> None:
    result = rank_catstyle_candidates(
        [{"planet_a": "Pluto", "planet_b": "Moon", "aspect_type": "conjunction"}]
    )
    assert len(result.ranked) == 1
    c = result.ranked[0]
    assert c.source == "seed"
    blob = (c.reason + " " + c.recommended_scene_angle).lower()
    assert "pillow" in blob or "blanket" in blob or "shadow" in blob or "cauldron" in blob
    assert "aspect charge" in c.reason.lower()


def test_tighter_orb_ranks_higher_same_pair() -> None:
    result = rank_catstyle_candidates(
        [
            {"planet_a": "Pluto", "planet_b": "Moon", "aspect_type": "conjunction", "orb": 2.5},
            {"planet_a": "Moon", "planet_b": "Pluto", "aspect_type": "conjunction", "orb": 0.4},
        ]
    )
    assert len(result.ranked) == 2
    assert result.ranked[0].orb == 0.4
    assert result.ranked[1].orb == 2.5
    assert result.ranked[0].total_score > result.ranked[1].total_score


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
