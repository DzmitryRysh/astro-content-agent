"""Money / financial behavior weather overlays for Astro Content Agent."""

from astro_content_agent.content.money_weather.money_behavior_overlay_v1 import (
    CAPTION_OVERLAY_MONEY_WEATHER,
    CONTENT_ANGLE_MONEY,
    MoneyBehaviorOverlay,
    build_aspect_key,
    build_money_weather_caption_ru,
    inject_money_overlay_into_caption,
    is_money_content_angle,
    resolve_money_behavior_overlay,
    validate_money_caption_safety,
)

__all__ = [
    "CAPTION_OVERLAY_MONEY_WEATHER",
    "CONTENT_ANGLE_MONEY",
    "MoneyBehaviorOverlay",
    "build_aspect_key",
    "build_money_weather_caption_ru",
    "inject_money_overlay_into_caption",
    "is_money_content_angle",
    "resolve_money_behavior_overlay",
    "validate_money_caption_safety",
]
