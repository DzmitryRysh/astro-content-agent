"""Deterministic Catstyle v0 ranking for planet-pair aspects (no AI)."""
from __future__ import annotations

from typing import Any, Literal

from astro_content_agent.content.catstyle.aspect_library_v0 import get_aspect_interaction
from astro_content_agent.content.catstyle.models import (
    CatstyleCandidate,
    CatstyleCandidateRankingResult,
    CatstyleUnsupportedCandidate,
)
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import (
    get_transit_pair_seed,
    orient_outer_personal,
)
from astro_content_agent.services.content.catstyle_prompt_generator import normalize_planet_name

Mode = Literal["tension", "compensation", "mixed"]

_MODE_ORDER: tuple[Mode, ...] = ("tension", "mixed", "compensation")

_HARD_ASPECTS = frozenset({"conjunction", "square", "opposition"})
_SOFT_ASPECTS = frozenset({"trine", "sextile"})

_SEED_SCORES = {"visual": 6, "emotional": 6, "comedy": 6, "clarity": 6}
_FALLBACK_SCORES = {"visual": 5, "emotional": 5, "comedy": 5, "clarity": 5}

_DEEP_PAIR_SPECS: dict[tuple[str, str], dict[str, Any]] = {
    ("Pluto", "Venus"): {
        "visual": 10,
        "emotional": 10,
        "comedy": 8,
        "clarity": 9,
        "base_mode": "tension",
        "angle": "cauldron / hypnosis / shadow control",
        "reason": (
            "Deep library: strongest Catstyle-read—cauldron, spiral eyes, shadow orbit, overwhelmed Venus beat."
        ),
    },
    ("Moon", "Uranus"): {
        "visual": 9,
        "emotional": 9,
        "comedy": 10,
        "clarity": 9,
        "base_mode": "tension",
        "angle": "electric chaos vs Moon comfort (pillow + blanket pled)",
        "reason": (
            "Deep library: very high comic contrast—portal burst vs cozy Moon, readable silhouettes, absurd not cruel."
        ),
    },
    ("Mars", "Neptune"): {
        "visual": 9,
        "emotional": 8,
        "comedy": 9,
        "clarity": 10,
        "base_mode": "tension",
        "angle": "fire vs fog / steam cloud / dissolve gag",
        "reason": "Deep library: heat vs mist reads instantly—steam, fog wall, fish/bubble motif.",
    },
    ("Saturn", "Venus"): {
        "visual": 8,
        "emotional": 8,
        "comedy": 8,
        "clarity": 9,
        "base_mode": "mixed",
        "angle": "love/beauty under control, then design/business/fashion compensation",
        "reason": (
            "Deep library: editorial frame—hat/watch/pinstripe vs Venus value; audit-to-studio arcs."
        ),
    },
    ("Jupiter", "Mercury"): {
        "visual": 7,
        "emotional": 6,
        "comedy": 8,
        "clarity": 8,
        "base_mode": "mixed",
        "angle": "stylish teacher vs student analyst (star map, classroom, travel planning)",
        "reason": (
            "Deep library: constructive chemistry—sage Jupiter vs checklist Mercury carousels."
        ),
    },
}


def _pair_key_canonical(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b), key=str.lower))


def _shift_toward_tension(mode: Mode) -> Mode:
    i = _MODE_ORDER.index(mode)
    return _MODE_ORDER[max(0, i - 1)]


def _shift_toward_compensation(mode: Mode) -> Mode:
    i = _MODE_ORDER.index(mode)
    return _MODE_ORDER[min(len(_MODE_ORDER) - 1, i + 1)]


def _mode_for_aspect(base_mode: Mode, aspect_type: str) -> Mode:
    key = (aspect_type or "").strip().lower()
    if key in _HARD_ASPECTS:
        return _shift_toward_tension(base_mode)
    if key in _SOFT_ASPECTS:
        return _shift_toward_compensation(base_mode)
    return base_mode


def _deep_spec(pa: str, pb: str) -> dict[str, Any] | None:
    return _DEEP_PAIR_SPECS.get(_pair_key_canonical(pa, pb))


def _parse_orb(raw: dict[str, Any]) -> float | None:
    val = raw.get("orb")
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _scan_window_kwargs(raw: dict[str, Any]) -> dict[str, Any]:
    """Optional full-day scan fields passed through from candidate dicts."""
    out: dict[str, Any] = {}
    for key in (
        "closest_hour_utc",
        "window_first_seen_hour_utc",
        "window_last_seen_hour_utc",
        "window_samples_seen",
    ):
        v = raw.get(key)
        if v is not None:
            out[key] = int(v)
    if "is_moon_aspect" in raw:
        out["is_moon_aspect"] = bool(raw["is_moon_aspect"])
    return out


def _orb_bonus(orb: float | None) -> int:
    if orb is None:
        return 0
    if orb <= 0.5:
        return 5
    if orb <= 1.0:
        return 4
    if orb <= 2.0:
        return 3
    if orb <= 3.0:
        return 2
    return 0


def rank_catstyle_candidates(candidates: list[dict[str, Any]]) -> CatstyleCandidateRankingResult:
    """
    Rank Catstyle candidates: deep aspect_library pairs first, then 25 transit seeds, then generic outer-to-personal fallback.

    ``orb`` optional on each candidate dict (degrees). Tighter orbs add a deterministic bonus to ``total_score``.
    """
    ranked: list[CatstyleCandidate] = []
    unsupported: list[CatstyleUnsupportedCandidate] = []

    for raw in candidates:
        pa_raw = str(raw.get("planet_a", "")).strip()
        pb_raw = str(raw.get("planet_b", "")).strip()
        aspect_type = str(raw.get("aspect_type", "")).strip()
        orb = _parse_orb(raw)
        ob = _orb_bonus(orb)

        if not pa_raw or not pb_raw or not aspect_type:
            unsupported.append(
                CatstyleUnsupportedCandidate(
                    planet_a=pa_raw or "?",
                    planet_b=pb_raw or "?",
                    aspect_type=aspect_type or "?",
                    reason="Missing planet_a, planet_b, or aspect_type.",
                )
            )
            continue

        try:
            pa = normalize_planet_name(pa_raw)
            pb = normalize_planet_name(pb_raw)
        except ValueError as e:
            unsupported.append(
                CatstyleUnsupportedCandidate(
                    planet_a=pa_raw,
                    planet_b=pb_raw,
                    aspect_type=aspect_type,
                    reason=str(e),
                )
            )
            continue

        aspect_lower = aspect_type.strip().lower()
        aspect_note = ""
        if aspect_lower in _HARD_ASPECTS:
            aspect_note = " Hard aspect nudges toward tension-forward prompts."
        elif aspect_lower in _SOFT_ASPECTS:
            aspect_note = " Soft aspect nudges toward compensation-forward prompts."

        if get_aspect_interaction(pa, pb) is not None:
            spec = _deep_spec(pa, pb)
            if spec is None:
                unsupported.append(
                    CatstyleUnsupportedCandidate(
                        planet_a=pa,
                        planet_b=pb,
                        aspect_type=aspect_type,
                        reason="Pair in aspect library but missing deep ranking spec.",
                    )
                )
                continue
            base_mode: Mode = spec["base_mode"]
            mode = _mode_for_aspect(base_mode, aspect_type)
            vis = int(spec["visual"])
            emo = int(spec["emotional"])
            com = int(spec["comedy"])
            clar = int(spec["clarity"])
            base_total = vis + emo + com + clar
            ranked.append(
                CatstyleCandidate(
                    planet_a=pa,
                    planet_b=pb,
                    aspect_type=aspect_type,
                    mode_recommendation=mode,
                    visual_score=vis,
                    emotional_score=emo,
                    comedy_score=com,
                    clarity_score=clar,
                    total_score=base_total + ob,
                    reason=str(spec["reason"]) + aspect_note,
                    recommended_scene_angle=str(spec["angle"]),
                    orb=orb,
                    orb_bonus=ob,
                    source="deep",
                    **_scan_window_kwargs(raw),
                )
            )
            continue

        oriented = orient_outer_personal(pa, pb)
        if oriented is None:
            unsupported.append(
                CatstyleUnsupportedCandidate(
                    planet_a=pa,
                    planet_b=pb,
                    aspect_type=aspect_type,
                    reason="Not a Catstyle social/outer-to-personal transit pair.",
                )
            )
            continue

        outer, personal = oriented
        seed = get_transit_pair_seed(outer, personal)
        if seed is not None:
            base_mode = seed.base_mode
            mode = _mode_for_aspect(base_mode, aspect_type)
            vis = _SEED_SCORES["visual"]
            emo = _SEED_SCORES["emotional"]
            com = _SEED_SCORES["comedy"]
            clar = _SEED_SCORES["clarity"]
            base_total = vis + emo + com + clar
            angle = f"{seed.visual_metaphor} | {seed.suggested_scene_angles[0]}"
            reason = (
                f"Transit seed v0 ({seed.outer_planet}->{seed.personal_planet}): {seed.core_tension}"
                + aspect_note
            )
            ranked.append(
                CatstyleCandidate(
                    planet_a=pa,
                    planet_b=pb,
                    aspect_type=aspect_type,
                    mode_recommendation=mode,
                    visual_score=vis,
                    emotional_score=emo,
                    comedy_score=com,
                    clarity_score=clar,
                    total_score=base_total + ob,
                    reason=reason,
                    recommended_scene_angle=angle,
                    orb=orb,
                    orb_bonus=ob,
                    source="seed",
                    **_scan_window_kwargs(raw),
                )
            )
            continue

        fb_mode: Mode = "mixed"
        mode = _mode_for_aspect(fb_mode, aspect_type)
        vis = _FALLBACK_SCORES["visual"]
        emo = _FALLBACK_SCORES["emotional"]
        com = _FALLBACK_SCORES["comedy"]
        clar = _FALLBACK_SCORES["clarity"]
        base_total = vis + emo + com + clar
        ranked.append(
            CatstyleCandidate(
                planet_a=pa,
                planet_b=pb,
                aspect_type=aspect_type,
                mode_recommendation=mode,
                visual_score=vis,
                emotional_score=emo,
                comedy_score=com,
                clarity_score=clar,
                total_score=base_total + ob,
                reason="Generic Catstyle transit fallback (seed missing for this outer-to-personal pair)." + aspect_note,
                recommended_scene_angle=(
                    f"{outer} social rhythm vs {personal} everyday stakes—clear gesture, minimal props, thick outlines."
                ),
                orb=orb,
                orb_bonus=ob,
                source="fallback",
                **_scan_window_kwargs(raw),
            )
        )

    ranked.sort(
        key=lambda c: (
            -c.total_score,
            -c.orb_bonus,
            -c.visual_score,
            -c.emotional_score,
            c.planet_a.lower(),
            c.planet_b.lower(),
        ),
    )

    return CatstyleCandidateRankingResult(ranked=ranked, unsupported=unsupported)


__all__ = ["rank_catstyle_candidates"]
