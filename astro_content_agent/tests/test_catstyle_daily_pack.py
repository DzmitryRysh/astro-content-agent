"""Tests for Catstyle daily pack (scan + prompt packs)."""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

from astro_content_agent.astro.ephemeris import PlanetPosition, sign_for_longitude
from astro_content_agent.content.catstyle.models import CatstyleCandidate, CatstyleCandidateRankingResult
from astro_content_agent.services.content.catstyle_daily_pack import generate_catstyle_daily_pack
from astro_content_agent.services.content.catstyle_sky_aspect_scan import CATSTYLE_SKY_ORB_CONFIG


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


def test_daily_pack_top_one_has_prompt_pack_and_metadata() -> None:
    pack = generate_catstyle_daily_pack(
        date(2026, 1, 1),
        top=1,
        scan_mode="day-window",
        step_hours=2,
        compute_positions_fn=_mock_positions_three_transits,
    )
    assert pack.ranked_candidates_count >= 1
    assert pack.selected_count == 1
    assert len(pack.prompt_packs) == 1
    assert len(pack.prompt_packs[0]["image_prompts"]) == 4
    cand = pack.selected_candidates[0]
    mode = cand["mode_recommendation"]
    joined = " ".join(pack.prompt_packs[0]["image_prompts"]).lower()
    assert mode in joined or "aspect type" in joined


def test_daily_pack_passes_mode_to_prompt_generator_tension() -> None:
    pack = generate_catstyle_daily_pack(
        date(2026, 1, 1),
        top=1,
        scan_mode="day-window",
        compute_positions_fn=_mock_positions_three_transits,
    )
    cand = pack.selected_candidates[0]
    if cand["mode_recommendation"] == "tension":
        blob = " ".join(pack.prompt_packs[0]["image_prompts"]).lower()
        assert "scene beat" in blob


def test_daily_pack_noon_mode() -> None:
    pack = generate_catstyle_daily_pack(
        date(2026, 1, 1),
        top=1,
        scan_mode="noon",
        compute_positions_fn=_mock_positions_three_transits,
    )
    assert pack.scan_mode == "noon"
    assert pack.step_hours is None
    assert pack.selected_count == 1


def test_daily_pack_empty_when_no_aspects() -> None:
    def _sparse(d: date) -> dict[str, PlanetPosition]:
        names = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        return {n: _P(n, (i * 23.0) % 360.0) for i, n in enumerate(names)}

    zero_orb = {k: (v[0], 0.0) for k, v in CATSTYLE_SKY_ORB_CONFIG.items()}
    pack = generate_catstyle_daily_pack(
        date(2026, 6, 1),
        top=1,
        scan_mode="day-window",
        compute_positions_fn=_sparse,
        orb_config=zero_orb,
    )
    assert pack.selected_count == 0
    assert pack.prompt_packs == []
    assert pack.selected_candidates == []


def test_daily_pack_json_shape() -> None:
    pack = generate_catstyle_daily_pack(
        date(2026, 1, 1),
        top=1,
        scan_mode="day-window",
        step_hours=2,
        compute_positions_fn=_mock_positions_three_transits,
    )
    blob = pack.model_dump(mode="json")
    assert blob["date"] == "2026-01-01"
    assert blob.get("editorial_profile") == "charged"
    assert "ranked_candidates" in blob
    assert "scan_mode" in blob and "selected_candidates" in blob and "prompt_packs" in blob
    meta = blob["prompt_packs"][0].get("art_direction_profile") or {}
    assert meta.get("version") == "catstyle-art-direction-v0"
    assert meta.get("energy") in ("charged", "supportive", "balanced")


def _ranking_saturn_jupiter_moon_jupiter_mars() -> CatstyleCandidateRankingResult:
    """Intrinsic order: Saturn sextile edges Jupiter aspects (mirrors 2026-05-02-style scores)."""
    saturn_venus = CatstyleCandidate(
        planet_a="Saturn",
        planet_b="Venus",
        aspect_type="sextile",
        mode_recommendation="compensation",
        visual_score=8,
        emotional_score=8,
        comedy_score=8,
        clarity_score=9,
        total_score=46,
        reason="Deep library beat.",
        recommended_scene_angle="Saturn+Venus editorial frame",
        orb=0.24,
        orb_bonus=8,
        source="deep",
    )
    jupiter_moon = CatstyleCandidate(
        planet_a="Jupiter",
        planet_b="Moon",
        aspect_type="trine",
        mode_recommendation="compensation",
        visual_score=6,
        emotional_score=6,
        comedy_score=6,
        clarity_score=6,
        total_score=39,
        reason="Transit seed.",
        recommended_scene_angle="Jupiter scroll + Moon fort",
        orb=0.39,
        orb_bonus=7,
        source="seed",
        is_moon_aspect=True,
    )
    jupiter_mars = CatstyleCandidate(
        planet_a="Jupiter",
        planet_b="Mars",
        aspect_type="square",
        mode_recommendation="tension",
        visual_score=6,
        emotional_score=6,
        comedy_score=6,
        clarity_score=6,
        total_score=38,
        reason="Transit seed.",
        recommended_scene_angle="Mars charges Jupiter",
        orb=1.34,
        orb_bonus=3,
        source="seed",
    )
    return CatstyleCandidateRankingResult(ranked=[saturn_venus, jupiter_moon, jupiter_mars])


def test_charged_profile_prefers_jupiter_square_mars_over_saturn_sextile_venus() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_pack.scan_catstyle_sky_aspect_windows",
        return_value=_ranking_saturn_jupiter_moon_jupiter_mars(),
    ):
        pack = generate_catstyle_daily_pack(
            date(2026, 5, 2),
            top=1,
            scan_mode="day-window",
            editorial_profile="charged",
        )
    assert pack.editorial_profile == "charged"
    top = pack.selected_candidates[0]
    assert top["planet_a"] == "Jupiter" and top["planet_b"] == "Mars"
    assert top["aspect_type"] == "square"
    assert pack.ranked_candidates[0]["planet_a"] == "Saturn"


def test_supportive_profile_prefers_saturn_sextile_venus() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_pack.scan_catstyle_sky_aspect_windows",
        return_value=_ranking_saturn_jupiter_moon_jupiter_mars(),
    ):
        pack = generate_catstyle_daily_pack(
            date(2026, 5, 2),
            top=1,
            scan_mode="day-window",
            editorial_profile="supportive",
        )
    top = pack.selected_candidates[0]
    assert top["planet_a"] == "Saturn" and top["planet_b"] == "Venus"
    assert top["aspect_type"] == "sextile"


def test_balanced_profile_keeps_intrinsic_order() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_pack.scan_catstyle_sky_aspect_windows",
        return_value=_ranking_saturn_jupiter_moon_jupiter_mars(),
    ):
        pack = generate_catstyle_daily_pack(
            date(2026, 5, 2),
            top=1,
            scan_mode="day-window",
            editorial_profile="balanced",
        )
    top = pack.selected_candidates[0]
    assert top["planet_a"] == "Saturn" and top["aspect_type"] == "sextile"


def test_charged_secondary_supportive_is_soft_on_different_pair() -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_pack.scan_catstyle_sky_aspect_windows",
        return_value=_ranking_saturn_jupiter_moon_jupiter_mars(),
    ):
        pack = generate_catstyle_daily_pack(
            date(2026, 5, 2),
            top=1,
            scan_mode="day-window",
            editorial_profile="charged",
        )
    sec = pack.secondary_supportive_candidate
    assert sec is not None
    assert sec["aspect_type"] in ("trine", "sextile")
    assert not (
        sec["planet_a"] == pack.selected_candidates[0]["planet_a"]
        and sec["planet_b"] == pack.selected_candidates[0]["planet_b"]
    )
