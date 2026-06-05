"""Tests for money / financial behavior overlay v1."""
from __future__ import annotations

import re

from astro_content_agent.content.money_weather.money_behavior_overlay_v1 import (
    CAPTION_OVERLAY_MONEY_WEATHER,
    CONTENT_ANGLE_MONEY,
    build_aspect_key,
    build_money_weather_caption_ru,
    resolve_money_behavior_overlay,
    validate_money_caption_safety,
)
from astro_content_agent.services.content.catstyle_caption_context import build_catstyle_caption_context
from astro_content_agent.services.content.catstyle_caption_generator import build_fallback_caption


def _venus_pluto_manifest() -> dict:
    return {
        "date": "2026-06-04",
        "aspect_source": "educational",
        "selected_candidate": {
            "planet_a": "Venus",
            "planet_b": "Pluto",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
        },
    }


def test_overlay_exists_venus_opposite_pluto() -> None:
    ov = resolve_money_behavior_overlay("Venus", "Pluto", "opposition")
    assert ov.aspect_key == "venus_opposition_pluto"
    assert ov.is_curated is True
    assert "control" in ov.money_theme.lower()


def test_overlay_exists_venus_square_saturn() -> None:
    ov = resolve_money_behavior_overlay("Venus", "Saturn", "square")
    assert ov.aspect_key == "venus_square_saturn"
    assert ov.compensation_action


def test_overlay_exists_mars_square_uranus() -> None:
    ov = resolve_money_behavior_overlay("Mars", "Uranus", "square")
    assert ov.aspect_key == "mars_square_uranus"


def test_overlay_exists_mercury_square_neptune() -> None:
    ov = resolve_money_behavior_overlay("Mercury", "Neptune", "square")
    assert ov.aspect_key == "mercury_square_neptune"


def test_overlay_returns_compensation_action() -> None:
    ov = resolve_money_behavior_overlay("Jupiter", "Saturn", "square")
    assert ov.compensation_action.strip()
    assert "expansion" in ov.compensation_action.lower() or "growth" in ov.compensation_action.lower()


def test_overlay_returns_money_compass_cta() -> None:
    ov = resolve_money_behavior_overlay("Moon", "Saturn", "square")
    assert "Money Compass" in ov.money_compass_cta


def test_money_caption_avoids_deterministic_claims() -> None:
    ov = resolve_money_behavior_overlay("Venus", "Pluto", "opposition")
    caption = build_money_weather_caption_ru(ov, "Venus", "Pluto", "opposition")
    assert not validate_money_caption_safety(caption)
    low = caption.lower()
    for banned in (
        "you will earn",
        "you will lose",
        "buy now",
        "sell now",
        "invest now",
        "ты заработаешь",
        "покупай сейчас",
        "продавай сейчас",
    ):
        assert banned not in low


def test_russian_caption_venus_pluto_includes_value_control_language() -> None:
    ov = resolve_money_behavior_overlay("Venus", "Pluto", "opposition")
    caption = build_money_weather_caption_ru(ov, "Venus", "Pluto", "opposition")
    low = caption.lower()
    assert "ценност" in low or "ценность" in low or "цене" in low
    assert "контрол" in low or "плутон" in low


def test_russian_caption_includes_money_compass_bridge() -> None:
    ov = resolve_money_behavior_overlay("Venus", "Pluto", "opposition")
    caption = build_money_weather_caption_ru(ov, "Venus", "Pluto", "opposition")
    assert "Money Compass" in caption
    assert "климат" in caption.lower()


def test_unknown_aspect_returns_safe_generic_overlay() -> None:
    ov = resolve_money_behavior_overlay("Sun", "Neptune", "trine")
    assert ov.aspect_key == build_aspect_key("Sun", "Neptune", "trine")
    assert ov.is_curated is False
    assert ov.compensation_action
    assert ov.money_compass_cta
    assert not validate_money_caption_safety(
        build_money_weather_caption_ru(ov, "Sun", "Neptune", "trine")
    )


def test_fallback_caption_uses_money_angle_from_context() -> None:
    ctx = build_catstyle_caption_context(
        _venus_pluto_manifest(),
        content_angle=CONTENT_ANGLE_MONEY,
    )
    result = build_fallback_caption(ctx)
    assert "Money Compass" in result.caption
    assert not validate_money_caption_safety(result.caption)


def test_fallback_caption_accepts_money_weather_overlay_flag() -> None:
    ctx = build_catstyle_caption_context(
        _venus_pluto_manifest(),
        caption_overlay=CAPTION_OVERLAY_MONEY_WEATHER,
    )
    result = build_fallback_caption(ctx)
    assert re.search(r"ценност|контрол|страх|желан", result.caption, re.I)
