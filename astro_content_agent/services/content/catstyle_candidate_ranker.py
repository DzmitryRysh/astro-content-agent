"""Deterministic Catstyle v0 ranking for planet-pair aspects (no AI)."""
from __future__ import annotations

from typing import Any, Literal

from astro_content_agent.content.catstyle.aspect_library_v0 import get_aspect_interaction
from astro_content_agent.content.catstyle.models import (
    CatstyleCandidate,
    CatstyleCandidateRankingResult,
    CatstyleUnsupportedCandidate,
)
from astro_content_agent.services.content.catstyle_prompt_generator import normalize_planet_name

Mode = Literal["tension", "compensation", "mixed"]

_MODE_ORDER: tuple[Mode, ...] = ("tension", "mixed", "compensation")

_HARD_ASPECTS = frozenset({"conjunction", "square", "opposition"})
_SOFT_ASPECTS = frozenset({"trine", "sextile"})


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


_PAIR_SPECS: dict[tuple[str, str], dict[str, Any]] = {
    ("Pluto", "Venus"): {
        "visual": 10,
        "emotional": 10,
        "comedy": 8,
        "clarity": 9,
        "base_mode": "tension",
        "angle": "cauldron / hypnosis / shadow control",
        "reason": (
            "Strongest Catstyle-read: magnetism vs overwhelm reads instantly—cauldron, spiral eyes, shadow orbit."
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
            "Very high comic contrast: portal burst vs cozy Moon—readable silhouettes and absurd not cruel."
        ),
    },
    ("Mars", "Neptune"): {
        "visual": 9,
        "emotional": 8,
        "comedy": 9,
        "clarity": 10,
        "base_mode": "tension",
        "angle": "fire vs fog / steam cloud / dissolve gag",
        "reason": "Heat vs mist is instantly visual—steam, fog wall, fish/bubble motif sells the joke.",
    },
    ("Saturn", "Venus"): {
        "visual": 8,
        "emotional": 8,
        "comedy": 8,
        "clarity": 9,
        "base_mode": "mixed",
        "angle": "love/beauty under control, then design/business/fashion compensation",
        "reason": (
            "Strong editorial frame: hat/watch/pinstripe vs Venus value—mixed beats suit audit-to-studio arcs."
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
            "Constructive chemistry: sage Jupiter vs checklist Mercury—great for compensation/mixed carousels."
        ),
    },
}


def _spec_for_pair(pa: str, pb: str) -> dict[str, Any] | None:
    return _PAIR_SPECS.get(_pair_key_canonical(pa, pb))


def rank_catstyle_candidates(candidates: list[dict[str, Any]]) -> CatstyleCandidateRankingResult:
    """
    Rank Catstyle-supported planet pairs by deterministic visual/emotional/comedy/clarity scores.

    Unsupported rows (unknown planets or pair not in aspect library v0) are returned in ``unsupported``.
    """
    ranked: list[CatstyleCandidate] = []
    unsupported: list[CatstyleUnsupportedCandidate] = []

    for raw in candidates:
        pa_raw = str(raw.get("planet_a", "")).strip()
        pb_raw = str(raw.get("planet_b", "")).strip()
        aspect_type = str(raw.get("aspect_type", "")).strip()
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

        if get_aspect_interaction(pa, pb) is None:
            unsupported.append(
                CatstyleUnsupportedCandidate(
                    planet_a=pa,
                    planet_b=pb,
                    aspect_type=aspect_type,
                    reason="Pair not in Catstyle aspect library v0.",
                )
            )
            continue

        spec = _spec_for_pair(pa, pb)
        if spec is None:
            unsupported.append(
                CatstyleUnsupportedCandidate(
                    planet_a=pa,
                    planet_b=pb,
                    aspect_type=aspect_type,
                    reason="Pair supported in library but missing ranking spec v0.",
                )
            )
            continue

        base_mode: Mode = spec["base_mode"]
        mode = _mode_for_aspect(base_mode, aspect_type)
        vis = int(spec["visual"])
        emo = int(spec["emotional"])
        com = int(spec["comedy"])
        clar = int(spec["clarity"])
        total = vis + emo + com + clar
        aspect_lower = aspect_type.strip().lower()
        aspect_note = ""
        if aspect_lower in _HARD_ASPECTS:
            aspect_note = " Hard aspect nudges toward tension-forward prompts."
        elif aspect_lower in _SOFT_ASPECTS:
            aspect_note = " Soft aspect nudges toward compensation-forward prompts."

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
                total_score=total,
                reason=str(spec["reason"]) + aspect_note,
                recommended_scene_angle=str(spec["angle"]),
            )
        )

    ranked.sort(
        key=lambda c: (-c.total_score, -c.visual_score, -c.emotional_score, c.planet_a.lower(), c.planet_b.lower()),
    )

    return CatstyleCandidateRankingResult(ranked=ranked, unsupported=unsupported)


__all__ = ["rank_catstyle_candidates"]
