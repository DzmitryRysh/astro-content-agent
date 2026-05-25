"""Catstyle caption opening guard — life-situation hook first."""
from __future__ import annotations

from astro_content_agent.services.content.catstyle_aspect_source_truth_v1 import (
    apply_aspect_source_caption_guard,
    strip_forbidden_current_sky_phrases,
)
from astro_content_agent.services.content.catstyle_caption_context import (
    build_catstyle_caption_context,
    context_to_llm_payload,
)
from astro_content_agent.services.content.catstyle_caption_generator import (
    _DRY_TEXTBOOK_OPENING_MARKERS,
    build_fallback_caption,
)
from astro_content_agent.services.content.catstyle_caption_opening_guard_v1 import (
    apply_caption_opening_guard,
    build_life_situation_opening,
    is_dry_caption_opening,
)
from astro_content_agent.services.content.catstyle_caption_polish import polish_caption_for_package


def _mu_manifest(*, aspect_source: str = "manual_editorial") -> dict:
    return {
        "date": "2026-05-22",
        "aspect_source": aspect_source,
        "manual_aspect_override": {
            "enabled": True,
            "planet_a": "Mercury",
            "planet_b": "Uranus",
            "aspect_type": "opposition",
            "mode": "tension",
            "aspect_source": aspect_source,
        },
        "selected_candidate": {
            "planet_a": "Mercury",
            "planet_b": "Uranus",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
            "aspect_source": aspect_source,
        },
    }


def _sun_uranus_sky_manifest() -> dict:
    return {
        "date": "2026-05-22",
        "sky_scan_mode": "day-window",
        "aspect_source": "sky_current",
        "selected_candidate": {
            "planet_a": "Sun",
            "planet_b": "Uranus",
            "aspect_type": "conjunction",
            "mode_recommendation": "tension",
            "closest_hour_utc": 12,
            "aspect_source": "sky_current",
        },
    }


def test_mercury_uranus_opening_starts_with_life_hook() -> None:
    ctx = build_catstyle_caption_context(_mu_manifest())
    opening = build_life_situation_opening(ctx)
    low = opening.lower()
    assert "если день" in low[:120]
    assert "меркурий" in low and "уран" in low
    assert "сбои" in low or "звонк" in low or "документ" in low
    assert "в оппозиции" not in low[:180]


def test_mercury_uranus_fallback_hook_first_full_caption() -> None:
    ctx = build_catstyle_caption_context(_mu_manifest())
    payload = context_to_llm_payload(ctx)
    assert payload["caption_opening_style"] == "life_situation_hook_first"
    assert "caption_opening_formula" in payload

    result = build_fallback_caption(ctx)
    head = result.caption[:350].lower()
    assert head.startswith("**суета") or "если день" in head[:150]
    assert "стёб" in result.caption.lower() or "стеб" in result.caption.lower()
    opening_only = result.caption.split("\n\n")[0].lower()
    for banned in _DRY_TEXTBOOK_OPENING_MARKERS:
        assert banned not in opening_only


def test_sun_uranus_fallback_uses_life_hook_not_planet_first() -> None:
    ctx = build_catstyle_caption_context(_sun_uranus_sky_manifest())
    result = build_fallback_caption(ctx)
    head = result.caption[:280].lower()
    assert "если день" in head[:120] or "смотри на" in head[:160]
    assert not head.startswith("**солнце")
    assert "сегодня на небе" not in head


def test_apply_opening_guard_replaces_dry_first_paragraph() -> None:
    ctx = build_catstyle_caption_context(_mu_manifest())
    dry = (
        "**Меркурий** — связь и слова.\n\n"
        "**Уран** — внезапность.\n\n"
        "В **оппозиции** (tension) эти две силы встречаются."
    )
    out = apply_caption_opening_guard(dry, ctx)
    assert is_dry_caption_opening(dry.split("\n\n")[0], ctx)
    assert "если день" in out.lower()[:200]
    assert "В **оппозиции**" in out


def test_polish_applies_opening_guard_on_dry_llm_style_text() -> None:
    ctx = build_catstyle_caption_context(_mu_manifest())
    raw = "**Меркурий (Близнецы)** — слова.\n\n**Компенсация:** шаг."
    out = polish_caption_for_package(raw, ctx)
    assert "если день" in out.lower()[:220]


def test_manual_editorial_opening_avoids_current_sky_phrases() -> None:
    ctx = build_catstyle_caption_context(_mu_manifest(aspect_source="manual_editorial"))
    opening = build_life_situation_opening(ctx)
    guarded = apply_aspect_source_caption_guard(opening, ctx.aspect_source)
    low = guarded.lower()
    assert "сегодня на небе" not in low
    assert "текущая небесная погода" not in low
    assert ctx.aspect_source == "manual_editorial"


def test_strip_forbidden_still_applies_to_opening_with_injected_sky_phrase() -> None:
    ctx = build_catstyle_caption_context(_mu_manifest())
    bad = "Сегодня на небе хаос. Если день идёт через сбои — смотри на Меркурий–Уран."
    cleaned = apply_aspect_source_caption_guard(bad, ctx.aspect_source)
    assert "сегодня на небе" not in cleaned.lower()
