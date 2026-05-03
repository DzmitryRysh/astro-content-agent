"""Tests for Catstyle daily pack (scan + prompt packs)."""
from __future__ import annotations

from datetime import date

from astro_content_agent.astro.ephemeris import PlanetPosition, sign_for_longitude
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
    assert "scan_mode" in blob and "selected_candidates" in blob and "prompt_packs" in blob
