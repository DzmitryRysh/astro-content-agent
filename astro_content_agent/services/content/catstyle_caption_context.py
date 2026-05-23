"""Deterministic context blocks for Catstyle LLM caption generation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from astro_content_agent.astro.ephemeris import compute_positions
from astro_content_agent.content.catstyle.aspect_interaction_registry_v1 import build_aspect_interaction_block
from astro_content_agent.content.catstyle.compensation_registry_v1 import (
    resolve_catstyle_compensation,
)
from astro_content_agent.content.catstyle.models import CatstyleAspectTimingMetadata
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.planet_meaning_registry_v1 import planet_meaning_ru
from astro_content_agent.content.catstyle.sign_meaning_registry_v1 import (
    normalize_sign_name,
    sign_context_line_ru,
)
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import orient_outer_personal
from astro_content_agent.services.content.catstyle_aspect_timing import (
    build_aspect_timing_from_manifest,
    format_ru_timing_caption_append,
)
from astro_content_agent.services.content.catstyle_caption_planet_policy import use_sign_in_public_caption
from astro_content_agent.services.content.catstyle_compensation_copy import (
    format_compensation_package_block,
)

_CAPTION_BANNED_PHRASES: tuple[str, ...] = (
    "лови пару и тип аспекта",
    "метафора ритма",
    "без морализаторства",
    "пакет catstyle для ручной сборки",
    "пакет для ручной",
    "placeholder",
)


@dataclass(frozen=True)
class CatstyleCaptionContext:
    planet_a: str
    planet_b: str
    aspect_type: str
    mode: str
    date_iso: str
    planet_a_meaning: str
    planet_b_meaning: str
    planet_a_sign: str | None
    planet_b_sign: str | None
    planet_a_sign_context: str | None
    planet_b_sign_context: str | None
    aspect_interaction: str
    orb: float | None
    timing_note: str | None
    compensation_guidance: str | None
    compensation_primary_action: str | None
    compensation_why: str | None
    pressure_phrasing: str | None
    aspect_timing: CatstyleAspectTimingMetadata | None
    sky_weather_stack: dict[str, Any] | None = None
    background_aspect: dict[str, Any] | None = None
    combined_weather_label: str | None = None
    combined_pressure_summary: str | None = None
    stack_compensation_focus: str | None = None


def caption_banned_phrases() -> tuple[str, ...]:
    return _CAPTION_BANNED_PHRASES


def _row_from_manifest(manifest: dict[str, Any]) -> dict[str, Any] | None:
    sel = manifest.get("selected_candidate")
    if isinstance(sel, dict):
        return sel
    jobs = manifest.get("jobs")
    if isinstance(jobs, list) and jobs and isinstance(jobs[0], dict):
        return jobs[0]
    return None


def _sign_from_row_keys(row: dict[str, Any], planet: str) -> str | None:
    raw = (planet or "").strip()
    if not raw:
        return None
    try:
        p = normalize_planet_name(raw)
    except ValueError:
        return None
    for key in (
        f"{p.lower()}_sign",
        f"planet_{p.lower()}_sign",
        f"{raw.lower()}_sign",
    ):
        raw = row.get(key)
        if raw:
            return normalize_sign_name(str(raw))
    return None


def resolve_planet_signs(
    manifest: dict[str, Any],
    planet_a: str,
    planet_b: str,
    *,
    post_date: date | None = None,
) -> tuple[str | None, str | None]:
    row = _row_from_manifest(manifest)
    sa = _sign_from_row_keys(row, planet_a) if row else None
    sb = _sign_from_row_keys(row, planet_b) if row else None
    if sa and sb:
        return sa, sb
    d = post_date
    if d is None:
        raw = str(manifest.get("date") or "").strip()
        if raw:
            try:
                d = date.fromisoformat(raw)
            except ValueError:
                d = None
    if d is None:
        return sa, sb
    hour = 12.0
    if row:
        ch = row.get("closest_hour_utc")
        if ch is not None:
            try:
                hour = float(ch)
            except (TypeError, ValueError):
                hour = 12.0
    try:
        positions = compute_positions(d, hour_utc=hour)
    except Exception:
        return sa, sb
    def _pos_sign(planet: str) -> str | None:
        try:
            name = normalize_planet_name(planet)
        except ValueError:
            return None
        pos = positions.get(name)
        return normalize_sign_name(pos.sign) if pos else None

    if not sa:
        sa = _pos_sign(planet_a)
    if not sb:
        sb = _pos_sign(planet_b)
    return sa, sb


def _orb_from_manifest(manifest: dict[str, Any], row: dict[str, Any] | None) -> float | None:
    if row:
        o = row.get("orb")
        if o is not None:
            try:
                return float(o)
            except (TypeError, ValueError):
                pass
    jobs = manifest.get("jobs")
    if isinstance(jobs, list):
        for j in jobs:
            if isinstance(j, dict) and j.get("orb") is not None:
                try:
                    return float(j.get("orb"))
                except (TypeError, ValueError):
                    continue
    return None


def build_catstyle_caption_context(
    manifest: dict[str, Any],
    *,
    planet_a: str | None = None,
    planet_b: str | None = None,
    aspect_type: str | None = None,
    mode: str | None = None,
) -> CatstyleCaptionContext:
    row = _row_from_manifest(manifest)
    def _safe_planet(raw: str) -> str:
        s = (raw or "").strip()
        if not s:
            return ""
        try:
            return normalize_planet_name(s)
        except ValueError:
            return s

    pa = _safe_planet(planet_a or (str(row.get("planet_a")) if row else "") or "")
    pb = _safe_planet(planet_b or (str(row.get("planet_b")) if row else "") or "")
    asp = aspect_type or (str(row.get("aspect_type")) if row else "") or ""
    mo = mode or (str(row.get("mode_recommendation") or row.get("mode")) if row else "") or ""

    post_d: date | None = None
    date_iso = str(manifest.get("date") or "").strip()
    if date_iso:
        try:
            post_d = date.fromisoformat(date_iso)
        except ValueError:
            post_d = None

    sa, sb = resolve_planet_signs(manifest, pa, pb, post_date=post_d)
    timing = build_aspect_timing_from_manifest(manifest)
    oriented = orient_outer_personal(pa, pb)
    personal = oriented[1] if oriented else pb
    timing_note = format_ru_timing_caption_append(timing, post_date=post_d or date.today(), personal_planet=personal)
    if timing_note and not timing_note.strip():
        timing_note = None

    comp = resolve_catstyle_compensation(pa, pb, asp, mo)
    comp_guidance = format_compensation_package_block(comp) if comp else None

    ma = planet_meaning_ru(pa) or f"{pa} — планетарная тема дня (общий архетип)."
    mb = planet_meaning_ru(pb) or f"{pb} — планетарная тема дня (общий архетип)."

    sa_ctx = sign_context_line_ru(pa, sa) if use_sign_in_public_caption(pa) else None
    sb_ctx = sign_context_line_ru(pb, sb) if use_sign_in_public_caption(pb) else None

    stack_raw = manifest.get("sky_weather_stack")
    if not isinstance(stack_raw, dict) and row:
        nested = row.get("sky_weather_stack")
        stack_raw = nested if isinstance(nested, dict) else stack_raw
    stack: dict[str, Any] | None = stack_raw if isinstance(stack_raw, dict) else None
    bg_aspect: dict[str, Any] | None = None
    if stack:
        bgs = stack.get("background_aspects")
        if isinstance(bgs, list) and bgs and isinstance(bgs[0], dict):
            bg_aspect = bgs[0]

    return CatstyleCaptionContext(
        planet_a=pa,
        planet_b=pb,
        aspect_type=asp,
        mode=mo,
        date_iso=date_iso,
        planet_a_meaning=ma,
        planet_b_meaning=mb,
        planet_a_sign=sa if use_sign_in_public_caption(pa) else None,
        planet_b_sign=sb if use_sign_in_public_caption(pb) else None,
        planet_a_sign_context=sa_ctx,
        planet_b_sign_context=sb_ctx,
        aspect_interaction=build_aspect_interaction_block(pa, pb, asp, mo),
        orb=_orb_from_manifest(manifest, row),
        timing_note=timing_note,
        compensation_guidance=comp_guidance,
        compensation_primary_action=comp.primary_action if comp else None,
        compensation_why=comp.why_it_helps if comp else None,
        pressure_phrasing=comp.pressure_phrasing if comp else None,
        aspect_timing=timing,
        sky_weather_stack=stack,
        background_aspect=bg_aspect,
        combined_weather_label=str(stack.get("combined_weather_label") or "") if stack else None,
        combined_pressure_summary=str(stack.get("combined_pressure_summary") or "") if stack else None,
        stack_compensation_focus=str(stack.get("compensation_focus") or "") if stack else None,
    )


def context_to_llm_payload(ctx: CatstyleCaptionContext) -> dict[str, Any]:
    comp_entry = resolve_catstyle_compensation(ctx.planet_a, ctx.planet_b, ctx.aspect_type, ctx.mode)
    return {
        "planet_a": ctx.planet_a,
        "planet_b": ctx.planet_b,
        "aspect_type": ctx.aspect_type,
        "mode": ctx.mode,
        "date": ctx.date_iso,
        "planet_a_meaning": ctx.planet_a_meaning,
        "planet_b_meaning": ctx.planet_b_meaning,
        "planet_a_sign": ctx.planet_a_sign,
        "planet_b_sign": ctx.planet_b_sign,
        "planet_a_sign_context": ctx.planet_a_sign_context,
        "planet_b_sign_context": ctx.planet_b_sign_context,
        "aspect_interaction": ctx.aspect_interaction,
        "orb": ctx.orb,
        "package_appends_timing_block": True,
        "sign_interpretation_rules": (
            "Знак зодиака можно вплетать только для Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn. "
            "Для Uranus, Neptune, Pluto знак в данных может быть, но НЕ используй его в тексте — "
            "описывай только планетарный принцип (внезапность, туман, глубина/контроль)."
        ),
        "compensation_guidance": ctx.compensation_guidance,
        "compensation_primary_action": ctx.compensation_primary_action,
        "compensation_why": ctx.compensation_why,
        "public_compensation_adaptation": (
            comp_entry.public_compensation_adaptation if comp_entry else None
        ),
        "source_compensation_actions": (
            list(comp_entry.source_compensation_actions) if comp_entry else []
        ),
        "pressure_phrasing": ctx.pressure_phrasing,
        "caption_structure": [
            "planet_a_meaning",
            "planet_b_meaning",
            "interaction",
            "how_it_may_feel_today",
            "risk_pressure",
            "compensation",
            "one_concrete_action_today",
        ],
        "banned_phrases": list(_CAPTION_BANNED_PHRASES),
        "length_chars": "900-1500",
        "sky_weather_stack": ctx.sky_weather_stack,
        "background_aspect": ctx.background_aspect,
        "combined_weather_label": ctx.combined_weather_label,
        "combined_pressure_summary": ctx.combined_pressure_summary,
        "stack_compensation_focus": ctx.stack_compensation_focus,
        "stacked_caption_structure": (
            [
                "primary_aspect_plain_language",
                "background_pressure_brief",
                "how_they_combine_in_real_life",
                "compensation",
                "one_concrete_action_today",
            ]
            if ctx.background_aspect
            else None
        ),
    }


__all__ = [
    "CatstyleCaptionContext",
    "build_catstyle_caption_context",
    "caption_banned_phrases",
    "context_to_llm_payload",
    "resolve_planet_signs",
]
