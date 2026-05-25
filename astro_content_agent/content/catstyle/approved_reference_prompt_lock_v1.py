"""Approved-reference prompt fidelity lock (primary visual anchor, not loose inspiration)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.approved_reference_registry import ResolvedApprovedReference
from astro_content_agent.content.catstyle.catplanet_body_identity_lock_v1 import (
    CATPLANET_BODY_NEGATIVE_EXTRAS,
)
from astro_content_agent.content.catstyle.catstyle_global_quality_lock_v1 import (
    CATSTYLE_GLOBAL_QUALITY_NEGATIVE_EXTRAS,
)
from astro_content_agent.content.catstyle.flag_glyph_fidelity_lock_v1 import (
    FLAG_GLYPH_FIDELITY_NEGATIVE_EXTRAS,
)
from astro_content_agent.content.catstyle.zodiac_arena_floor_lock_v1 import (
    ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS,
)
from astro_content_agent.content.catstyle.mars_pluto_square_tension_canon_v1 import (
    MARS_PLUTO_SQUARE_TENSION_NEGATIVE_EXTRAS,
    is_mars_pluto_square_tension,
)
from astro_content_agent.content.catstyle.models import CatstylePromptPack
from astro_content_agent.content.catstyle.banner_glyph_reference_v1 import (
    banner_only_glyph_mode_active,
)
from astro_content_agent.content.catstyle.sun_uranus_conjunction_tension_canon_v1 import (
    SUN_URANUS_APPROVED_REFERENCE_FIDELITY_COMPACT,
    SUN_URANUS_CONJUNCTION_TENSION_NEGATIVE_EXTRAS,
    is_sun_uranus_conjunction_tension,
)
from astro_content_agent.content.catstyle.sun_uranus_visual_refinement_v1 import (
    BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK,
    SUN_URANUS_VISUAL_REFINEMENT_NEGATIVE_EXTRAS,
)

_ASPECT_TYPE_MARKER = "Aspect type:"

APPROVED_REFERENCE_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "reference-lite reinterpretation",
    "simplified mascot redraw",
    "soft cartoon redraw",
    "ordinary fur cats",
    "low-density render",
    "flat arena backdrop",
    "weak planet-body texture",
    "losing approved reference visual DNA",
)

REFERENCE_FIDELITY_GRADING_BLOCK: Final[str] = (
    "[REFERENCE FIDELITY GRADING v1] Target **85–95% visual consistency** with the approved reference—"
    "a **sibling image from the same campaign** with a **new pose/action variation** only; "
    "not reference-lite theme borrowing or a softer cartoon redraw."
)

_NEGATIVE_PROMPT_MAX_LEN = 1200

# Preserve a small set of global anti-storybook negatives when making room for approved-reference extras.
_GLOBAL_NEGATIVE_GUARD_FOR_APPROVED_REF: Final[tuple[str, ...]] = (
    "storybook illustration",
    "children-book style",
    "soft watercolor look",
    "watercolor storybook softness",
    "toy-like cats",
    "static standing confrontation",
)

_BASE_NEGATIVE_GUARD_FOR_APPROVED_REF: Final[tuple[str, ...]] = (
    "malformed planetary glyphs",
    "pseudo-symbols",
    "floating white sticker symbols",
    "disconnected sticker posing",
)

_CATSTYLE_VISUAL_FIDELITY_NEGATIVE_COMPACT: Final[str] = ", ".join(
    (
        *CATPLANET_BODY_NEGATIVE_EXTRAS,
        *ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS,
        *FLAG_GLYPH_FIDELITY_NEGATIVE_EXTRAS,
    )
)


def visual_fidelity_negative_must_keep() -> tuple[str, ...]:
    """One compact comma-chunk reserved under trim (matches base fidelity negative chunk)."""
    return (_CATSTYLE_VISUAL_FIDELITY_NEGATIVE_COMPACT,)


def approved_reference_negative_must_keep(
    planet_a: str, planet_b: str, aspect_type: str, mode: str
) -> tuple[str, ...]:
    out: list[str] = list(
        visual_fidelity_negative_must_keep()
        + APPROVED_REFERENCE_NEGATIVE_EXTRAS
        + _pair_negative_must_keep(planet_a, planet_b, aspect_type, mode)
        + _GLOBAL_NEGATIVE_GUARD_FOR_APPROVED_REF
        + _BASE_NEGATIVE_GUARD_FOR_APPROVED_REF
    )
    if (mode or "").strip().lower() == "flow":
        out.extend(
            [
                "underexposed overall scene",
                "muddy crushed shadows",
                "malformed astrological glyphs painted in-image",
            ]
        )
    return tuple(out)


def build_approved_reference_lock_block(hit: ResolvedApprovedReference) -> str:
    """Concise generic lock when an approved registry row is active."""
    return (
        "[APPROVED CATSTYLE REFERENCE LOCK v1] "
        "Treat the approved reference as **strict visual DNA**—same **exact visual universe**, "
        "**sibling image from the same campaign**, not loose theme inspiration. "
        "Match reference **render density**, **premium comic-poster finish**, **character volume and proportions**, "
        "**catplanet surface texture strength**, **arena depth/scale**, and **lighting contrast**. "
        "Do **not** simplify into soft cartoon redraw, ordinary fur cats with pasted effects, or reference-lite reinterpretation. "
        "New pose/action variation only—preserve the reference look."
    )


def inject_approved_reference_lock_after_style_opener(prompt: str, lock_block: str) -> str:
    """Insert lock immediately after render-style opener, before ``Aspect type:``."""
    marker = _ASPECT_TYPE_MARKER
    idx = prompt.find(marker)
    if idx < 0:
        return f"{prompt.rstrip()} {lock_block}".strip()
    return f"{prompt[:idx].rstrip()} {lock_block} {prompt[idx:].lstrip()}".strip()


def build_approved_reference_prompt_lock_text(
    hit: ResolvedApprovedReference,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
) -> str:
    """Generic lock + grading + optional compact pair-specific approved fidelity."""
    parts = [
        build_approved_reference_lock_block(hit),
        REFERENCE_FIDELITY_GRADING_BLOCK,
    ]
    if banner_only_glyph_mode_active():
        parts.append(BANNER_ONLY_APPROVED_REFERENCE_DECOUPLING_BLOCK)
    if is_sun_uranus_conjunction_tension(planet_a, planet_b, aspect_type, mode):
        parts.append(SUN_URANUS_APPROVED_REFERENCE_FIDELITY_COMPACT)
    return " ".join(p for p in parts if p).strip()


def merge_negative_prompt_with_extras(
    base_negative: str,
    extras: tuple[str, ...],
    *,
    max_len: int = _NEGATIVE_PROMPT_MAX_LEN,
) -> str:
    """Append deduped approved-reference *extras* only when they fit; never mutate existing base chunks."""

    def _norm(s: str) -> str:
        return " ".join(s.lower().split())

    base_parts = [p.strip() for p in (base_negative or "").split(",") if p.strip()]
    seen = {_norm(p) for p in base_parts}
    extra_parts: list[str] = []
    for extra in extras:
        key = _norm(extra)
        if key in seen:
            continue
        trial = ", ".join(base_parts + extra_parts + [extra.strip()])
        if len(trial) <= max_len:
            seen.add(key)
            extra_parts.append(extra.strip())

    return ", ".join(base_parts + extra_parts)


def _negative_parts(negative: str) -> list[str]:
    return [p.strip() for p in (negative or "").split(",") if p.strip()]


def _is_reserved_negative_chunk(chunk: str, must_keep: tuple[str, ...]) -> bool:
    def _norm(s: str) -> str:
        return " ".join(s.lower().split())

    keep_keys = {_norm(m) for m in must_keep if m.strip()}
    c = _norm(chunk)
    return any(k in c or c in k for k in keep_keys)


def trim_negative_prompt_to_max(
    negative: str,
    *,
    max_len: int = _NEGATIVE_PROMPT_MAX_LEN,
    must_keep: tuple[str, ...] = (),
    drop_from: str = "front_first",
) -> str:
    """Drop comma chunks until within *max_len*; preserve order and *must_keep* phrases."""

    parts = _negative_parts(negative)

    def _joined(ps: list[str]) -> str:
        return ", ".join(ps)

    def _drop_one_non_reserved(from_end: bool) -> bool:
        indices = range(len(parts) - 1, -1, -1) if from_end else range(len(parts))
        for i in indices:
            if not _is_reserved_negative_chunk(parts[i], must_keep):
                parts.pop(i)
                return True
        return False

    while len(_joined(parts)) > max_len:
        dropped = False
        if drop_from in ("back_first", "both"):
            dropped = _drop_one_non_reserved(from_end=True)
        if not dropped and drop_from in ("front_first", "both"):
            dropped = _drop_one_non_reserved(from_end=False)
        if not dropped:
            break
    while len(_joined(parts)) > max_len:
        if not _drop_one_non_reserved(from_end=False):
            break
    out = _joined(parts)
    if len(out) > max_len:
        out = out[:max_len].rstrip().rstrip(",")
    return out


def _extras_missing_from_negative(negative: str, extras: tuple[str, ...]) -> list[str]:
    blob = " ".join(negative.lower().split())
    missing: list[str] = []
    for extra in extras:
        key = " ".join(extra.lower().split())
        if key not in blob:
            missing.append(extra)
    return missing


def _pair_negative_must_keep(planet_a: str, planet_b: str, aspect_type: str, mode: str) -> tuple[str, ...]:
    out: list[str] = []
    if is_mars_pluto_square_tension(planet_a, planet_b, aspect_type, mode):
        out.extend(MARS_PLUTO_SQUARE_TENSION_NEGATIVE_EXTRAS)
    if is_sun_uranus_conjunction_tension(planet_a, planet_b, aspect_type, mode):
        out.extend(SUN_URANUS_CONJUNCTION_TENSION_NEGATIVE_EXTRAS)
        out.extend(SUN_URANUS_VISUAL_REFINEMENT_NEGATIVE_EXTRAS)
    return tuple(out)


def _is_global_quality_negative_chunk(chunk: str) -> bool:
    def _norm(s: str) -> str:
        return " ".join(s.lower().split())

    c = _norm(chunk)
    for g in CATSTYLE_GLOBAL_QUALITY_NEGATIVE_EXTRAS:
        gn = _norm(g)
        if gn in c or c in gn:
            return True
    return False


def trim_global_quality_negatives_for_room(negative: str, *, target_max_len: int) -> str:
    """Drop only global anti-storybook tail chunks to make room for approved-reference negatives."""
    parts = _negative_parts(negative)

    def _joined(ps: list[str]) -> str:
        return ", ".join(ps)

    while len(_joined(parts)) > target_max_len:
        dropped = False
        for i in range(len(parts) - 1, -1, -1):
            if _is_global_quality_negative_chunk(parts[i]):
                parts.pop(i)
                dropped = True
                break
        if not dropped:
            break
    return _joined(parts)


def apply_approved_reference_lock_to_prompt_pack(
    pack: CatstylePromptPack,
    hit: ResolvedApprovedReference,
    *,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
) -> CatstylePromptPack:
    """Inject lock after style opener; merge capped negatives. Does not touch art_direction_profile."""
    lock_text = build_approved_reference_prompt_lock_text(hit, planet_a, planet_b, aspect_type, mode)
    new_prompts = [
        inject_approved_reference_lock_after_style_opener(p, lock_text) for p in pack.image_prompts
    ]
    neg = pack.negative_prompt
    must_keep = approved_reference_negative_must_keep(planet_a, planet_b, aspect_type, mode)
    merged_neg = merge_negative_prompt_with_extras(neg, APPROVED_REFERENCE_NEGATIVE_EXTRAS)
    if _extras_missing_from_negative(merged_neg, APPROVED_REFERENCE_NEGATIVE_EXTRAS):
        neg2 = trim_global_quality_negatives_for_room(neg, target_max_len=max(400, len(neg) - 48))
        if neg2 != neg:
            neg = neg2
            merged_neg = merge_negative_prompt_with_extras(neg, APPROVED_REFERENCE_NEGATIVE_EXTRAS)
    merged_neg = merge_negative_prompt_with_extras(merged_neg, _BASE_NEGATIVE_GUARD_FOR_APPROVED_REF)
    merged_neg = trim_negative_prompt_to_max(
        merged_neg,
        must_keep=must_keep,
        drop_from="back_first",
    )
    return pack.model_copy(
        update={
            "image_prompts": new_prompts,
            "negative_prompt": merged_neg,
        }
    )


__all__ = [
    "APPROVED_REFERENCE_NEGATIVE_EXTRAS",
    "REFERENCE_FIDELITY_GRADING_BLOCK",
    "visual_fidelity_negative_must_keep",
    "apply_approved_reference_lock_to_prompt_pack",
    "build_approved_reference_lock_block",
    "build_approved_reference_prompt_lock_text",
    "inject_approved_reference_lock_after_style_opener",
    "merge_negative_prompt_with_extras",
    "trim_negative_prompt_to_max",
]
