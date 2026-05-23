"""Catstyle Daily Sky Weather Stack v1 — primary flash + background pressure selection."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.models import CatstyleCandidate
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import orient_outer_personal
from astro_content_agent.services.content.catstyle_editorial_selection import (
    EditorialProfile,
    candidate_to_editorial_dict,
)

DurationCategory = Literal["short_flash", "active_wave", "pressure_background"]

_HARD_ASPECTS = frozenset({"conjunction", "square", "opposition"})

# Pairs that read as short high-impact flashes (outer → fast personal emphasis).
_SHORT_FLASH_PAIR_KEYS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"Mercury", "Uranus"}),
        frozenset({"Mercury", "Neptune"}),
        frozenset({"Moon", "Uranus"}),
        frozenset({"Moon", "Neptune"}),
        frozenset({"Sun", "Uranus"}),
        frozenset({"Venus", "Uranus"}),
    }
)

# Slower collective / pressure-background pairs.
_PRESSURE_BACKGROUND_PAIR_KEYS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"Mars", "Pluto"}),
        frozenset({"Mars", "Uranus"}),
        frozenset({"Mars", "Saturn"}),
        frozenset({"Venus", "Pluto"}),
        frozenset({"Venus", "Uranus"}),
        frozenset({"Moon", "Saturn"}),
        frozenset({"Moon", "Neptune"}),
        frozenset({"Jupiter", "Saturn"}),
        frozenset({"Sun", "Pluto"}),
        frozenset({"Sun", "Saturn"}),
    }
)

_TRANS_PERSONAL_OUTERS = frozenset({"Uranus", "Neptune", "Pluto"})


class SkyWeatherAspectSlot(BaseModel):
    planet_a: str
    planet_b: str
    aspect_type: str
    mode_recommendation: str
    duration_category: DurationCategory
    source: str = "sky_scan"
    orb: float | None = None
    total_score: int | None = None
    stack_role: Literal["primary", "background"] = "primary"
    selection_score: int | None = None


class CatstyleSkyWeatherStack(BaseModel):
    """Stacked daily weather: one primary flash + optional background pressure aspect(s)."""

    version: str = "catstyle-sky-weather-stack-v1"
    primary_aspect: SkyWeatherAspectSlot
    background_aspects: list[SkyWeatherAspectSlot] = Field(default_factory=list)
    combined_weather_label: str
    combined_pressure_summary: str
    compensation_focus: str
    selection_reason: str


def _pair_key(planet_a: str, planet_b: str) -> frozenset[str] | None:
    try:
        a = normalize_planet_name(planet_a)
        b = normalize_planet_name(planet_b)
    except ValueError:
        return None
    return frozenset({a, b})


def is_outer_to_personal(planet_a: str, planet_b: str) -> bool:
    return orient_outer_personal(planet_a, planet_b) is not None


def is_transpersonal_to_personal(planet_a: str, planet_b: str) -> bool:
    oriented = orient_outer_personal(planet_a, planet_b)
    if oriented is None:
        return False
    return oriented[0] in _TRANS_PERSONAL_OUTERS


def _window_span_days(c: CatstyleCandidate) -> float | None:
    first = c.window_first_seen_hour_utc
    last = c.window_last_seen_hour_utc
    if first is None or last is None:
        return None
    hours = max(0, int(last) - int(first))
    return hours / 24.0


def infer_duration_category(candidate: CatstyleCandidate) -> DurationCategory:
    """Classify aspect window length for stack roles (heuristic v1)."""
    pk = _pair_key(candidate.planet_a, candidate.planet_b)
    asp = (candidate.aspect_type or "").strip().lower()
    span = _window_span_days(candidate)

    if pk in _SHORT_FLASH_PAIR_KEYS and asp in _HARD_ASPECTS:
        return "short_flash"
    if pk in _PRESSURE_BACKGROUND_PAIR_KEYS and asp in _HARD_ASPECTS:
        return "pressure_background"
    if span is not None:
        if span <= 2.25:
            return "short_flash"
        if span >= 7.0:
            return "pressure_background"
        if span <= 5.5:
            return "active_wave"
    oriented = orient_outer_personal(candidate.planet_a, candidate.planet_b)
    if oriented and oriented[0] in _TRANS_PERSONAL_OUTERS:
        personal = oriented[1]
        if personal in ("Mercury", "Moon") and asp in _HARD_ASPECTS:
            return "short_flash"
        if personal in ("Mars", "Venus", "Sun") and asp in _HARD_ASPECTS:
            return "active_wave"
    if pk in _PRESSURE_BACKGROUND_PAIR_KEYS:
        return "pressure_background"
    return "active_wave"


def _slot_from_candidate(
    c: CatstyleCandidate,
    *,
    role: Literal["primary", "background"],
    duration: DurationCategory,
    selection_score: int,
) -> SkyWeatherAspectSlot:
    return SkyWeatherAspectSlot(
        planet_a=c.planet_a,
        planet_b=c.planet_b,
        aspect_type=c.aspect_type,
        mode_recommendation=c.mode_recommendation,
        duration_category=duration,
        source=c.source,
        orb=c.orb,
        total_score=c.total_score,
        stack_role=role,
        selection_score=selection_score,
    )


def _primary_selection_score(c: CatstyleCandidate) -> int:
    score = int(c.total_score)
    dur = infer_duration_category(c)
    if dur == "short_flash":
        score += 45
    elif dur == "active_wave":
        score += 15
    if is_transpersonal_to_personal(c.planet_a, c.planet_b):
        score += 40
    elif is_outer_to_personal(c.planet_a, c.planet_b):
        score += 25
    asp = (c.aspect_type or "").strip().lower()
    if asp in _HARD_ASPECTS:
        score += 12
    if c.orb is not None and c.orb <= 1.0:
        score += 8
    oriented = orient_outer_personal(c.planet_a, c.planet_b)
    if oriented and oriented[1] in ("Mercury", "Moon"):
        score += 10
    return score


def _background_selection_score(c: CatstyleCandidate, primary_pk: frozenset[str] | None) -> int:
    pk = _pair_key(c.planet_a, c.planet_b)
    if pk is None or pk == primary_pk:
        return -1
    score = int(c.total_score)
    dur = infer_duration_category(c)
    if dur == "pressure_background":
        score += 50
    elif dur == "active_wave":
        score += 20
    if pk in _PRESSURE_BACKGROUND_PAIR_KEYS:
        score += 35
    asp = (c.aspect_type or "").strip().lower()
    if asp in _HARD_ASPECTS and (c.mode_recommendation or "").lower() == "tension":
        score += 15
    span = _window_span_days(c)
    if span is not None and span >= 6.0:
        score += 12
    return score


def _combined_label(primary: SkyWeatherAspectSlot, backgrounds: list[SkyWeatherAspectSlot]) -> str:
    if backgrounds:
        return f"{primary.planet_a}–{primary.planet_b} flash + {backgrounds[0].planet_a}–{backgrounds[0].planet_b} pressure"
    return f"{primary.planet_a}–{primary.planet_b} daily weather"


def _combined_pressure_summary(primary: SkyWeatherAspectSlot, backgrounds: list[SkyWeatherAspectSlot]) -> str:
    parts = [
        f"Главный удар: {primary.planet_a} {primary.aspect_type} {primary.planet_b} "
        f"({primary.duration_category.replace('_', ' ')}).",
    ]
    for bg in backgrounds:
        parts.append(
            f"Фон: {bg.planet_a} {bg.aspect_type} {bg.planet_b} "
            f"({bg.duration_category.replace('_', ' ')})."
        )
    return " ".join(parts)


def _compensation_focus_text(primary: SkyWeatherAspectSlot, backgrounds: list[SkyWeatherAspectSlot]) -> str:
    from astro_content_agent.content.catstyle.compensation_registry_v1 import resolve_catstyle_compensation

    lines: list[str] = []
    pcomp = resolve_catstyle_compensation(
        primary.planet_a, primary.planet_b, primary.aspect_type, primary.mode_recommendation
    )
    if pcomp:
        pub = (pcomp.public_compensation_adaptation or "").strip()
        lines.append(pub if pub else pcomp.primary_action)
    for bg in backgrounds:
        bcomp = resolve_catstyle_compensation(bg.planet_a, bg.planet_b, bg.aspect_type, bg.mode_recommendation)
        if bcomp and bcomp.primary_action not in lines:
            lines.append(bcomp.primary_action)
    if not lines:
        return "один ясный шаг сегодня + пауза перед ответом на пике раздражения"
    return "; ".join(lines[:2])


def _selection_reason(
    primary: SkyWeatherAspectSlot,
    backgrounds: list[SkyWeatherAspectSlot],
    *,
    editorial_profile: EditorialProfile,
) -> str:
    bits = [
        f"Primary: {primary.planet_a} {primary.aspect_type} {primary.planet_b} "
        f"as {primary.duration_category} (outer-to-personal / flash priority, profile={editorial_profile}).",
    ]
    if backgrounds:
        bg = backgrounds[0]
        bits.append(
            f"Background: {bg.planet_a} {bg.aspect_type} {bg.planet_b} "
            f"as {bg.duration_category} (longer pressure layer, different pair)."
        )
    else:
        bits.append("No distinct background pressure pair in today's scan.")
    return " ".join(bits)


def build_sky_weather_stack(
    ranked: list[CatstyleCandidate],
    *,
    editorial_profile: EditorialProfile = "charged",
) -> CatstyleSkyWeatherStack | None:
    """
    Pick primary short-window aspect + optional background pressure from ranked scan rows.

    Returns ``None`` when *ranked* is empty.
    """
    if not ranked:
        return None

    primary_pk: frozenset[str] | None = None
    best_primary: CatstyleCandidate | None = None
    best_primary_score = -1
    for c in ranked:
        ps = _primary_selection_score(c)
        if ps > best_primary_score:
            best_primary_score = ps
            best_primary = c
            primary_pk = _pair_key(c.planet_a, c.planet_b)

    if best_primary is None:
        best_primary = ranked[0]
        primary_pk = _pair_key(best_primary.planet_a, best_primary.planet_b)

    primary_dur = infer_duration_category(best_primary)
    primary_slot = _slot_from_candidate(
        best_primary, role="primary", duration=primary_dur, selection_score=best_primary_score
    )

    backgrounds: list[SkyWeatherAspectSlot] = []
    best_bg: CatstyleCandidate | None = None
    best_bg_score = -1
    for c in ranked:
        bs = _background_selection_score(c, primary_pk)
        if bs > best_bg_score:
            best_bg_score = bs
            best_bg = c

    if best_bg is not None and best_bg_score > 0:
        bg_dur = infer_duration_category(best_bg)
        if bg_dur in ("pressure_background", "active_wave") or _pair_key(best_bg.planet_a, best_bg.planet_b) in _PRESSURE_BACKGROUND_PAIR_KEYS:
            backgrounds.append(
                _slot_from_candidate(best_bg, role="background", duration=bg_dur, selection_score=best_bg_score)
            )

    return CatstyleSkyWeatherStack(
        primary_aspect=primary_slot,
        background_aspects=backgrounds,
        combined_weather_label=_combined_label(primary_slot, backgrounds),
        combined_pressure_summary=_combined_pressure_summary(primary_slot, backgrounds),
        compensation_focus=_compensation_focus_text(primary_slot, backgrounds),
        selection_reason=_selection_reason(primary_slot, backgrounds, editorial_profile=editorial_profile),
    )


def resolve_stack_primary_candidate(
    ranked: list[CatstyleCandidate],
    stack: CatstyleSkyWeatherStack,
) -> CatstyleCandidate | None:
    """Match stack primary slot back to a ranked ``CatstyleCandidate``."""
    p = stack.primary_aspect
    pk = _pair_key(p.planet_a, p.planet_b)
    asp = (p.aspect_type or "").strip().lower()
    for c in ranked:
        if _pair_key(c.planet_a, c.planet_b) == pk and (c.aspect_type or "").strip().lower() == asp:
            return c
    for c in ranked:
        if _pair_key(c.planet_a, c.planet_b) == pk:
            return c
    return ranked[0] if ranked else None


def stack_to_manifest_dict(stack: CatstyleSkyWeatherStack) -> dict[str, Any]:
    return stack.model_dump(mode="json")


def apply_stack_to_selected_dict(
    selected_dict: dict[str, Any],
    stack: CatstyleSkyWeatherStack,
) -> dict[str, Any]:
    """Annotate editorial selected candidate with stack metadata."""
    out = dict(selected_dict)
    out["sky_weather_stack_role"] = "primary"
    out["duration_category"] = stack.primary_aspect.duration_category
    out["sky_weather_stack"] = stack_to_manifest_dict(stack)
    return out


__all__ = [
    "CatstyleSkyWeatherStack",
    "DurationCategory",
    "SkyWeatherAspectSlot",
    "apply_stack_to_selected_dict",
    "build_sky_weather_stack",
    "infer_duration_category",
    "is_outer_to_personal",
    "is_transpersonal_to_personal",
    "resolve_stack_primary_candidate",
    "stack_to_manifest_dict",
]
