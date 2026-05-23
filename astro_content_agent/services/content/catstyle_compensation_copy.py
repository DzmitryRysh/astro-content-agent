"""Apply structured compensation guidance to Catstyle post package copy."""
from __future__ import annotations

from astro_content_agent.content.catstyle.aspect_library_v0 import get_aspect_interaction
from astro_content_agent.content.catstyle.compensation_registry_v1 import (
    CAPTION_COMPENSATION_MARKER,
    CatstyleCompensationEntry,
    resolve_catstyle_compensation,
)
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import (
    get_transit_pair_seed,
    orient_outer_personal,
)


def format_public_compensation_paragraph(entry: CatstyleCompensationEntry) -> str:
    """Natural-language compensation for captions (prefers public adaptation over bullet list)."""
    pub = (entry.public_compensation_adaptation or "").strip()
    if pub:
        return pub
    if entry.relieve_phrasing:
        return entry.relieve_phrasing.strip()
    return f"{CAPTION_COMPENSATION_MARKER} {entry.primary_action}."


def format_compensation_package_block(entry: CatstyleCompensationEntry) -> str:
    """Human-facing compensation section for post_package (not caption-internal jargon)."""
    lines: list[str] = ["Как снять давление аспекта:"]
    if entry.pressure_phrasing:
        lines.append(f"Давление: {entry.pressure_phrasing}")
    if entry.relieve_phrasing:
        lines.append(f"Смысл: {entry.relieve_phrasing}")
    pub = (entry.public_compensation_adaptation or "").strip()
    if pub:
        lines.append(f"Публичная адаптация: {pub}")
    if entry.source_compensation_actions:
        lines.append("Источник (Bioastrologiya):")
        for bullet in entry.source_compensation_actions:
            lines.append(f"• {bullet}")
    for bullet in entry.compensation_actions:
        lines.append(f"• {bullet}")
    return "\n".join(lines)


def format_caption_compensation_lines(entry: CatstyleCompensationEntry) -> str:
    """Short practical block for Instagram caption (one action + one why)."""
    return (
        f"{CAPTION_COMPENSATION_MARKER} {entry.primary_action}.\n"
        f"Зачем это работает: {entry.why_it_helps}."
    )


def _caption_has_structured_compensation(caption: str) -> bool:
    return CAPTION_COMPENSATION_MARKER in (caption or "")


def inject_compensation_into_caption(caption: str, entry: CatstyleCompensationEntry) -> str:
    block = format_caption_compensation_lines(entry)
    base = (caption or "").strip()
    if _caption_has_structured_compensation(base):
        head, _, _tail = base.partition(CAPTION_COMPENSATION_MARKER)
        return f"{head.rstrip()}\n\n{block}".strip()
    if not base:
        return block
    return f"{base}\n\n{block}"


def _fallback_constructive_channel(
    planet_a: str | None,
    planet_b: str | None,
    aspect_type: str | None,
    mode: str | None,
) -> str | None:
    if not planet_a or not planet_b:
        return None
    ix = get_aspect_interaction(planet_a, planet_b)
    if ix is not None and (ix.constructive_channel or "").strip():
        return ix.constructive_channel.strip()
    oriented = orient_outer_personal(planet_a, planet_b)
    if oriented is None:
        return None
    seed = get_transit_pair_seed(oriented[0], oriented[1])
    if seed is None:
        return None
    ch = (seed.constructive_channel or "").strip()
    return ch or None


def format_fallback_compensation_block(constructive_channel: str) -> str:
    return (
        "Как снять давление аспекта:\n"
        f"• {constructive_channel}\n"
        "• переведи напряжение в одно конкретное действие на сегодня;\n"
        "• проверь результат простым критерием «стало легче/яснее?»."
    )


def format_fallback_caption_lines(constructive_channel: str) -> str:
    short = constructive_channel.split("—", 1)[0].strip()
    if len(short) > 120:
        short = short[:117].rstrip() + "…"
    return (
        f"{CAPTION_COMPENSATION_MARKER} возьми одну идею из канала компенсации и сделай её сегодня в маленьком шаге "
        f"({short.lower()}).\n"
        "Зачем это работает: так аспект даёт опору, а не только описание напряжения."
    )


def apply_structured_compensation_to_post_copy(
    planet_a: str | None,
    planet_b: str | None,
    aspect_type: str | None,
    mode: str | None,
    *,
    hook: str,
    caption: str,
    carousel: str,
    compensation: str,
    checklist: str,
) -> tuple[str, str, str, str, str]:
    """
    Prefer registry compensation when available; otherwise light fallback from aspect library / seeds.
    """
    pa = planet_a or ""
    pb = planet_b or ""
    asp = aspect_type or ""
    mo = mode or ""

    entry = resolve_catstyle_compensation(pa, pb, asp, mo)
    if entry is not None:
        return (
            hook,
            inject_compensation_into_caption(caption, entry),
            carousel,
            format_compensation_package_block(entry),
            checklist,
        )

    channel = _fallback_constructive_channel(pa, pb, asp, mo)
    if channel:
        cap = (caption or "").strip()
        if not _caption_has_structured_compensation(cap):
            block = format_fallback_caption_lines(channel)
            cap = f"{cap}\n\n{block}".strip() if cap else block
        comp = compensation.strip()
        if comp.startswith("Компенсация:") and "• одно действие" in comp:
            comp = format_fallback_compensation_block(channel)
        return hook, cap, carousel, comp, checklist

    return hook, caption, carousel, compensation, checklist


__all__ = [
    "apply_structured_compensation_to_post_copy",
    "format_caption_compensation_lines",
    "format_compensation_package_block",
    "format_public_compensation_paragraph",
    "inject_compensation_into_caption",
]
