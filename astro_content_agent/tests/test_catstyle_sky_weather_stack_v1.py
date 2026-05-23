"""Daily Sky Weather Stack v1 — selection, manifest, stacked captions."""
from __future__ import annotations

import json
from pathlib import Path

from astro_content_agent.content.catstyle.compensation_registry_v1 import CAPTION_COMPENSATION_MARKER
from astro_content_agent.content.catstyle.models import CatstyleCandidate
from astro_content_agent.services.content.catstyle_caption_context import (
    build_catstyle_caption_context,
    context_to_llm_payload,
)
from astro_content_agent.services.content.catstyle_caption_generator import build_fallback_caption
from astro_content_agent.services.content.catstyle_post_package import build_catstyle_post_package
from astro_content_agent.services.content.catstyle_sky_weather_stack_v1 import (
    build_sky_weather_stack,
    infer_duration_category,
)


def _candidate(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    *,
    mode: str = "tension",
    total_score: int = 30,
    orb: float = 0.4,
    w_first: int = 10,
    w_last: int = 14,
    source: str = "seed",
) -> CatstyleCandidate:
    return CatstyleCandidate(
        planet_a=planet_a,
        planet_b=planet_b,
        aspect_type=aspect_type,
        mode_recommendation=mode,  # type: ignore[arg-type]
        visual_score=7,
        emotional_score=7,
        comedy_score=7,
        clarity_score=7,
        total_score=total_score,
        reason="test candidate",
        recommended_scene_angle="test angle",
        orb=orb,
        orb_bonus=5,
        source=source,  # type: ignore[arg-type]
        window_first_seen_hour_utc=w_first,
        window_last_seen_hour_utc=w_last,
        window_samples_seen=3,
    )


def test_mercury_uranus_opposition_prioritized_as_short_flash_primary() -> None:
    ranked = [
        _candidate("Mars", "Pluto", "square", total_score=42, w_first=0, w_last=22),
        _candidate("Mercury", "Uranus", "opposition", total_score=35, w_first=10, w_last=12),
        _candidate("Venus", "Jupiter", "trine", total_score=50, mode="flow"),
    ]
    stack = build_sky_weather_stack(ranked, editorial_profile="charged")
    assert stack is not None
    assert stack.primary_aspect.planet_a in ("Mercury", "Uranus")
    assert stack.primary_aspect.planet_b in ("Mercury", "Uranus")
    assert stack.primary_aspect.aspect_type == "opposition"
    assert stack.primary_aspect.duration_category == "short_flash"


def test_mars_pluto_square_can_be_pressure_background() -> None:
    mars_pluto = _candidate("Mars", "Pluto", "square", total_score=40, w_first=0, w_last=22)
    assert infer_duration_category(mars_pluto) == "pressure_background"
    ranked = [
        _candidate("Mercury", "Uranus", "opposition", total_score=38, w_first=8, w_last=10),
        mars_pluto,
    ]
    stack = build_sky_weather_stack(ranked, editorial_profile="charged")
    assert stack is not None
    assert stack.background_aspects
    bg = stack.background_aspects[0]
    assert {bg.planet_a, bg.planet_b} == {"Mars", "Pluto"}
    assert bg.duration_category == "pressure_background"


def test_caption_context_includes_primary_and_background() -> None:
    manifest = {
        "date": "2026-05-22",
        "selected_candidate": {
            "planet_a": "Mercury",
            "planet_b": "Uranus",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
        },
        "sky_weather_stack": {
            "version": "catstyle-sky-weather-stack-v1",
            "primary_aspect": {
                "planet_a": "Mercury",
                "planet_b": "Uranus",
                "aspect_type": "opposition",
                "mode_recommendation": "tension",
                "duration_category": "short_flash",
            },
            "background_aspects": [
                {
                    "planet_a": "Mars",
                    "planet_b": "Pluto",
                    "aspect_type": "square",
                    "mode_recommendation": "tension",
                    "duration_category": "pressure_background",
                }
            ],
            "combined_weather_label": "Mercury–Uranus flash + Mars–Pluto pressure",
            "combined_pressure_summary": "test summary",
            "compensation_focus": "перепроверить дважды",
            "selection_reason": "test reason",
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Mercury",
                "planet_b": "Uranus",
                "aspect_type": "opposition",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "out.png",
            }
        ],
    }
    ctx = build_catstyle_caption_context(manifest)
    payload = context_to_llm_payload(ctx)
    assert ctx.background_aspect is not None
    assert ctx.background_aspect.get("planet_a") == "Mars"
    assert payload["stacked_caption_structure"] is not None
    assert payload["background_aspect"]["planet_b"] == "Pluto"


def test_stacked_fallback_caption_names_planets_early_no_outer_signs() -> None:
    manifest = {
        "date": "2026-05-22",
        "selected_candidate": {
            "planet_a": "Mercury",
            "planet_b": "Uranus",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
            "mercury_sign": "Gemini",
            "uranus_sign": "Gemini",
        },
        "sky_weather_stack": {
            "primary_aspect": {
                "planet_a": "Mercury",
                "planet_b": "Uranus",
                "aspect_type": "opposition",
                "mode_recommendation": "tension",
                "duration_category": "short_flash",
            },
            "background_aspects": [
                {
                    "planet_a": "Mars",
                    "planet_b": "Pluto",
                    "aspect_type": "square",
                    "mode_recommendation": "tension",
                    "duration_category": "pressure_background",
                }
            ],
            "combined_weather_label": "x",
            "combined_pressure_summary": "y",
            "compensation_focus": "перепроверить",
            "selection_reason": "z",
        },
    }
    ctx = build_catstyle_caption_context(manifest)
    result = build_fallback_caption(ctx)
    head = result.caption[:400].lower()
    assert "меркурий" in head
    assert "уран" in head
    assert "марс" in result.caption.lower() or "плутон" in result.caption.lower()
    assert "уран в" not in head
    assert "нептун в" not in head
    assert "плутон в" not in head


def test_stacked_fallback_mercury_uranus_bioastrologiya_compensation_not_generic() -> None:
    manifest = {
        "date": "2026-05-22",
        "selected_candidate": {
            "planet_a": "Mercury",
            "planet_b": "Uranus",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
            "uranus_sign": "Gemini",
            "mercury_sign": "Gemini",
        },
        "sky_weather_stack": {
            "primary_aspect": {
                "planet_a": "Mercury",
                "planet_b": "Uranus",
                "aspect_type": "opposition",
                "mode_recommendation": "tension",
                "duration_category": "short_flash",
            },
            "background_aspects": [
                {
                    "planet_a": "Mars",
                    "planet_b": "Pluto",
                    "aspect_type": "square",
                    "mode_recommendation": "tension",
                    "duration_category": "pressure_background",
                }
            ],
            "combined_weather_label": "x",
            "combined_pressure_summary": "y",
            "compensation_focus": "умная искра",
            "selection_reason": "z",
        },
    }
    ctx = build_catstyle_caption_context(manifest)
    result = build_fallback_caption(ctx)
    low = result.caption.lower()
    assert "стёб" in low or "стеб" in low
    assert "друз" in low or "обсужден" in low
    assert any(x in low for x in ("фантаст", "формула", "прогноз", "математ", "скорочт"))
    assert "прогул" not in low
    assert "уран в" not in low
    assert "измеримое действие" in low or "контрол" in low or "докажу" in low


def test_stacked_caption_includes_compensation(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-05-22",
        "selected_candidate": {
            "planet_a": "Mercury",
            "planet_b": "Uranus",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
        },
        "sky_weather_stack": {
            "primary_aspect": {
                "planet_a": "Mercury",
                "planet_b": "Uranus",
                "aspect_type": "opposition",
                "mode_recommendation": "tension",
                "duration_category": "short_flash",
            },
            "background_aspects": [
                {
                    "planet_a": "Mars",
                    "planet_b": "Pluto",
                    "aspect_type": "square",
                    "mode_recommendation": "tension",
                    "duration_category": "pressure_background",
                }
            ],
            "combined_weather_label": "x",
            "combined_pressure_summary": "y",
            "compensation_focus": "перепроверить",
            "selection_reason": "z",
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Mercury",
                "planet_b": "Uranus",
                "aspect_type": "opposition",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "out.png",
            }
        ],
    }
    mp = tmp_path / "jobs.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    pkg = build_catstyle_post_package(mp, use_llm_caption=False)
    low = pkg.caption.lower()
    assert CAPTION_COMPENSATION_MARKER.lower() in low
    assert "стёб" in low or "стеб" in low or "формула" in low
    assert "практический шаг" in low
