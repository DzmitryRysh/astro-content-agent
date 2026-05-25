"""Life-situation-first opening guard for Catstyle captions."""
from __future__ import annotations

import re
from typing import Any

from astro_content_agent.content.catstyle.compensation_registry_v1 import (
    CAPTION_COMPENSATION_MARKER,
    resolve_catstyle_compensation,
)
from astro_content_agent.content.catstyle.planet_meaning_registry_v1 import planet_display_ru
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import orient_outer_personal
from astro_content_agent.services.content.catstyle_caption_context import CatstyleCaptionContext
from astro_content_agent.services.content.catstyle_caption_planet_policy import use_sign_in_public_caption
from astro_content_agent.content.catstyle.sign_meaning_registry_v1 import sign_display_ru

# Dry / textbook openings — aspect name or planet label leads without life hook.
_DRY_OPENING_MARKERS: tuple[str, ...] = (
    "в оппозиции к",
    "в соединении с",
    "в квадрате к",
    "сегодня их соединение",
    "сегодня их оппозиция",
    "этот аспект",
    "данный аспект",
    "аспект — это",
)

_LIFE_HOOK_LEADS: tuple[str, ...] = (
    "если день",
    "когда день",
    "если утро",
    "если вечер",
    "смотри на",
    "день идёт",
    "день идет",
)

_OUTER_SITUATION_RU: dict[str, str] = {
    "Uranus": "сбои, звонки, документы и разговоры на повышенных оборотах",
    "Neptune": "догадки, намёки и размытые формулировки",
    "Pluto": "борьбу за контроль, напряжённые разговоры и ощущение давления",
    "Saturn": "дедлайны, ограничения и разговоры «надо потерпеть»",
    "Jupiter": "расширение планов, обещания и желание «взять больше»",
    "Mars": "спешку, раздражение и желание давить на газ",
}


def dry_opening_markers() -> tuple[str, ...]:
    return _DRY_OPENING_MARKERS


def _pair_label(ctx: CatstyleCaptionContext) -> str:
    return f"{planet_display_ru(ctx.planet_a)}–{planet_display_ru(ctx.planet_b)}"


def _resolve_weather_label(ctx: CatstyleCaptionContext) -> str | None:
    label = (ctx.combined_weather_label or "").strip()
    if label and label not in ("x", "y"):
        return label
    comp = resolve_catstyle_compensation(ctx.planet_a, ctx.planet_b, ctx.aspect_type, ctx.mode)
    if comp and comp.caption_weather_label:
        return comp.caption_weather_label.strip()
    return None


def _generic_life_hook_line(ctx: CatstyleCaptionContext) -> str:
    """Concrete life situation, then pair name — safe for all aspect_source values."""
    comp = resolve_catstyle_compensation(ctx.planet_a, ctx.planet_b, ctx.aspect_type, ctx.mode)
    if comp and (comp.pressure_phrasing or "").strip():
        lead = comp.pressure_phrasing.strip().rstrip(".")
        if len(lead) > 120:
            lead = lead[:117].rsplit(" ", 1)[0] + "…"
        return f"{lead} — смотри на {_pair_label(ctx)}."

    oriented = orient_outer_personal(ctx.planet_a, ctx.planet_b)
    if oriented:
        outer, personal = oriented
        situation = _OUTER_SITUATION_RU.get(
            outer,
            "рывки, сбои и темы, которые не держатся в привычном ритме",
        )
        return (
            f"Если день идёт через {situation} — "
            f"смотри на {planet_display_ru(personal)}–{planet_display_ru(outer)}."
        )

    return (
        f"Если день идёт рывками и срывами — смотри на {_pair_label(ctx)}."
    )


def _planet_meanings_paragraph(ctx: CatstyleCaptionContext) -> str:
    """Short planet meanings without outer-planet sign interpretation."""
    pa = planet_display_ru(ctx.planet_a)
    pb = planet_display_ru(ctx.planet_b)
    sign_a = (
        f" ({sign_display_ru(ctx.planet_a_sign)})"
        if ctx.planet_a_sign and use_sign_in_public_caption(ctx.planet_a)
        else ""
    )
    sign_b = (
        f" ({sign_display_ru(ctx.planet_b_sign)})"
        if ctx.planet_b_sign and use_sign_in_public_caption(ctx.planet_b)
        else ""
    )
    p1 = ctx.planet_a_sign_context or ctx.planet_a_meaning
    p2 = ctx.planet_b_sign_context or ctx.planet_b_meaning
    return f"**{pa}{sign_a}** — {p1}\n\n**{pb}{sign_b}** — {p2}"


def build_life_situation_opening(ctx: CatstyleCaptionContext) -> str:
    """
    Opening block: life hook → pair (in hook) → planet meanings when not already embedded.
    """
    comp = resolve_catstyle_compensation(ctx.planet_a, ctx.planet_b, ctx.aspect_type, ctx.mode)
    if comp and (comp.caption_life_hook_opening or "").strip():
        body = comp.caption_life_hook_opening.strip()
        has_meanings = "\n\n" in body
    else:
        body = _generic_life_hook_line(ctx)
        has_meanings = False

    label = _resolve_weather_label(ctx)
    if label:
        body = f"**{label}**\n\n{body}"

    if has_meanings:
        return body
    return f"{body}\n\n{_planet_meanings_paragraph(ctx)}"


def is_dry_caption_opening(text: str, ctx: CatstyleCaptionContext | None = None) -> bool:
    """True when the opening reads like textbook aspect/planet-first copy."""
    head = (text or "").strip()
    if not head:
        return True
    sample = head[:320].lower()
    if any(lead in sample for lead in _LIFE_HOOK_LEADS):
        return False
    if "смотри на" in sample[:200]:
        return False
    first_line = head.split("\n", 1)[0].strip()
    low_line = first_line.lower()
    if re.match(r"^\*\*[^*]+\*\*\s*—", first_line):
        return True
    if any(m in sample for m in _DRY_OPENING_MARKERS):
        return True
    if ctx is not None:
        pa = planet_display_ru(ctx.planet_a).lower()
        pb = planet_display_ru(ctx.planet_b).lower()
        if low_line.startswith(pa) or low_line.startswith(f"**{pa}"):
            return True
        if low_line.startswith(pb) or low_line.startswith(f"**{pb}"):
            return True
    return False


def _feel_paragraph(ctx: CatstyleCaptionContext) -> str:
    if ctx.aspect_source == "sky_current":
        if ctx.mode.lower() == "flow":
            return (
                "Сегодня есть ощущение короткого окна — если поймать его, день может дать облегчение; "
                "если проморгать, останется только «ну, было красиво в голове»."
            )
        return (
            "Сегодня обе темы звучат громче обычного — тело и нервы могут реагировать быстрее, "
            "чем успеваешь всё назвать словами."
        )
    if ctx.mode.lower() == "flow":
        return (
            "Есть ощущение короткого окна — если поймать его, можно получить облегчение; "
            "если проморгать, останется только «ну, было красиво в голове»."
        )
    return (
        "Обе темы могут звучать громче обычного — тело и нервы реагируют быстрее, "
        "чем успеваешь всё назвать словами."
    )


def build_standard_fallback_body_paragraphs(
    ctx: CatstyleCaptionContext,
    *,
    comp_summary: str,
    action: str,
    why: str,
) -> list[str]:
    """Life hook → meanings (if needed) → interaction → feel → risk → compensation → step."""
    comp_entry = resolve_catstyle_compensation(ctx.planet_a, ctx.planet_b, ctx.aspect_type, ctx.mode)
    paragraphs: list[str] = [build_life_situation_opening(ctx)]
    asp_ru = {
        "conjunction": "соединение",
        "sextile": "секстиль",
        "square": "квадрат",
        "opposition": "оппозиция",
        "trine": "трин",
    }.get(ctx.aspect_type.lower(), ctx.aspect_type)

    paragraphs.extend(
        [
            f"В **{asp_ru}** ({ctx.mode}) эти две силы встречаются так: {ctx.aspect_interaction}",
            _feel_paragraph(ctx),
        ]
    )
    if comp_entry and (comp_entry.caption_risk_line or "").strip():
        paragraphs.append(comp_entry.caption_risk_line.strip())
    else:
        risk = ctx.pressure_phrasing or (
            "Риск — разогнать тему в тревогу или в спор «кто прав», вместо одного ясного шага."
        )
        paragraphs.append(f"**Точка давления:** {risk}")

    paragraphs.append(f"**Компенсация:** {comp_summary}")
    paragraphs.append(f"{CAPTION_COMPENSATION_MARKER} {action}.\nЗачем это работает: {why}")
    return paragraphs


def apply_caption_opening_guard(caption: str, ctx: CatstyleCaptionContext) -> str:
    """Replace a dry first paragraph with a life-situation hook opening when needed."""
    text = (caption or "").strip()
    if not text:
        return text
    parts = text.split("\n\n", 1)
    first = parts[0]
    rest = parts[1].strip() if len(parts) > 1 else ""
    if not is_dry_caption_opening(first, ctx):
        return text
    opening = build_life_situation_opening(ctx)
    if rest:
        return f"{opening}\n\n{rest}".strip()
    return opening


__all__ = [
    "apply_caption_opening_guard",
    "CAPTION_COMPENSATION_MARKER",
    "build_life_situation_opening",
    "build_standard_fallback_body_paragraphs",
    "dry_opening_markers",
    "is_dry_caption_opening",
]
