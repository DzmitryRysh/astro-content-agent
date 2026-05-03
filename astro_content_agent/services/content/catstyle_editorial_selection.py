"""Editorial selection profiles for Catstyle daily pack (on top of intrinsic ranking)."""
from __future__ import annotations

from typing import Literal

from astro_content_agent.content.catstyle.models import CatstyleCandidate
from astro_content_agent.services.content.catstyle_candidate_ranker import _aspect_strength

EditorialProfile = Literal["charged", "balanced", "supportive"]

EDITORIAL_PROFILE_DEFAULT: EditorialProfile = "charged"

_CHARGED_BONUS: dict[str, int] = {
    "conjunction": 8,
    "opposition": 6,
    "square": 5,
    "trine": 1,
    "sextile": -3,
}

_SUPPORTIVE_BONUS: dict[str, int] = {
    "sextile": 6,
    "trine": 5,
    "conjunction": 1,
    "square": -2,
    "opposition": -2,
}


def normalize_editorial_profile(raw: str) -> EditorialProfile:
    key = (raw or "").strip().lower()
    if key not in ("charged", "balanced", "supportive"):
        raise ValueError("editorial_profile must be 'charged', 'balanced', or 'supportive'")
    return key  # type: ignore[return-value]


def editorial_aspect_bonus(aspect_type: str, profile: EditorialProfile) -> int:
    """Per-profile additive bias for selection only (intrinsic ``total_score`` unchanged)."""
    if profile == "balanced":
        return 0
    key = (aspect_type or "").strip().lower()
    if profile == "charged":
        return _CHARGED_BONUS.get(key, 0)
    return _SUPPORTIVE_BONUS.get(key, 0)


def editorial_selection_score(candidate: CatstyleCandidate, profile: EditorialProfile) -> int:
    return int(candidate.total_score) + editorial_aspect_bonus(candidate.aspect_type, profile)


def _charged_geometry_rank(aspect_type: str) -> int:
    """Tiebreak for charged mode: higher = more angularly charged."""
    key = (aspect_type or "").strip().lower()
    return {"conjunction": 5, "opposition": 4, "square": 3, "trine": 2, "sextile": 1}.get(key, 0)


def _supportive_soft_rank(aspect_type: str) -> int:
    """Tiebreak for supportive mode: higher = more compensation-friendly."""
    key = (aspect_type or "").strip().lower()
    return {"sextile": 5, "trine": 4, "conjunction": 2, "square": 1, "opposition": 1}.get(key, 0)


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b), key=str.lower))


def editorial_selection_sort_key(candidate: CatstyleCandidate, profile: EditorialProfile) -> tuple[int, ...]:
    bonus = editorial_aspect_bonus(candidate.aspect_type, profile)
    sel = int(candidate.total_score) + bonus
    ob = int(candidate.orb_bonus)
    ast = _aspect_strength(candidate.aspect_type)
    vis = int(candidate.visual_score)
    emo = int(candidate.emotional_score)
    if profile == "charged":
        return (
            -sel,
            -_charged_geometry_rank(candidate.aspect_type),
            -ob,
            -ast,
            -vis,
            -emo,
            candidate.planet_a.lower(),
            candidate.planet_b.lower(),
        )
    if profile == "supportive":
        return (
            -sel,
            -_supportive_soft_rank(candidate.aspect_type),
            -ob,
            -ast,
            -vis,
            -emo,
            candidate.planet_a.lower(),
            candidate.planet_b.lower(),
        )
    # balanced: match intrinsic ranker ordering
    return (
        -sel,
        -ob,
        -ast,
        -vis,
        -emo,
        candidate.planet_a.lower(),
        candidate.planet_b.lower(),
    )


def sort_candidates_for_editorial_profile(
    candidates: list[CatstyleCandidate],
    profile: EditorialProfile,
) -> list[CatstyleCandidate]:
    return sorted(candidates, key=lambda c: editorial_selection_sort_key(c, profile))


def pick_secondary_supportive_for_charged(
    ranked_intrinsic: list[CatstyleCandidate],
    primary: CatstyleCandidate,
) -> CatstyleCandidate | None:
    """Best trine/sextile on a *different* pair for optional B-roll / softer caption (charged days)."""
    pk = _pair_key(primary.planet_a, primary.planet_b)
    soft = [
        c
        for c in ranked_intrinsic
        if _pair_key(c.planet_a, c.planet_b) != pk
        and c.aspect_type.strip().lower() in ("trine", "sextile")
    ]
    if not soft:
        return None
    ordered = sort_candidates_for_editorial_profile(soft, "supportive")
    return ordered[0]


def candidate_to_editorial_dict(
    c: CatstyleCandidate,
    profile: EditorialProfile,
) -> dict:
    d = c.model_dump(mode="json")
    eb = editorial_aspect_bonus(c.aspect_type, profile)
    d["editorial_profile"] = profile
    d["editorial_bonus"] = eb
    d["editorial_selection_score"] = int(c.total_score) + eb
    return d


__all__ = [
    "EDITORIAL_PROFILE_DEFAULT",
    "EditorialProfile",
    "candidate_to_editorial_dict",
    "editorial_aspect_bonus",
    "editorial_selection_score",
    "editorial_selection_sort_key",
    "normalize_editorial_profile",
    "pick_secondary_supportive_for_charged",
    "sort_candidates_for_editorial_profile",
]
