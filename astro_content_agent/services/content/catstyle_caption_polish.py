"""Post-process Catstyle captions: no outer-sign copy, single timing block."""
from __future__ import annotations

import re
from datetime import date

from astro_content_agent.content.catstyle.models import CatstyleAspectTimingMetadata
from astro_content_agent.content.catstyle.planet_meaning_registry_v1 import planet_display_ru
from astro_content_agent.services.content.catstyle_aspect_timing import append_ru_timing_to_caption
from astro_content_agent.services.content.catstyle_caption_planet_policy import (
    CAPTION_NO_SIGN_INTERPRETATION_PLANETS,
    use_sign_in_public_caption,
)
from astro_content_agent.services.content.catstyle_caption_context import CatstyleCaptionContext

_OUTER_DISPLAY_RU: tuple[str, ...] = tuple(
    planet_display_ru(p) for p in sorted(CAPTION_NO_SIGN_INTERPRETATION_PLANETS)
)

_TIMING_PARAGRAPH_MARKERS: tuple[str, ...] = (
    "окно аспекта",
    "1–2 дня",
    "1-2 дня",
    "на весь месяц",
    "ближайшие сутки",
    "не растягивай шанс",
    "не упусти",
    "день публикации",
    "окно короткое",
    "вокруг пика",
)


def strip_caption_timing_blocks(text: str) -> str:
    """Remove package-style and inline timing paragraphs so one block can be appended."""
    if not text:
        return ""
    out = re.sub(
        r"\n?\*\*Про сроки:\*\*[\s\S]*?(?=\n\n\*\*|\Z)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    parts = [p.strip() for p in out.split("\n\n") if p.strip()]
    kept: list[str] = []
    for part in parts:
        low = part.lower()
        if "**про сроки:**" in low:
            continue
        if "практический шаг" in low or "точка давления" in low or "компенсация" in low:
            kept.append(part)
            continue
        hits = sum(1 for m in _TIMING_PARAGRAPH_MARKERS if m in low)
        if hits >= 2 and len(part) < 420:
            continue
        kept.append(part)
    return "\n\n".join(kept).strip()


def strip_transpersonal_outer_sign_copy(text: str) -> str:
    """Drop lines that interpret Uranus/Neptune/Pluto by zodiac sign."""
    if not text:
        return ""
    sign_in_line = re.compile(
        r"(?:"
        r"\sв\s+[А-ЯЁ][а-яё]+"
        r"|в\s+знаке"
        r"|сейчас\s+в"
        r"|,\s*тоже\s+в"
        r")",
        re.IGNORECASE,
    )
    lines = text.split("\n")
    kept: list[str] = []
    for line in lines:
        if not line.strip():
            kept.append(line)
            continue
        if any(label in line for label in _OUTER_DISPLAY_RU) and sign_in_line.search(line):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def polish_caption_for_package(caption: str, ctx: CatstyleCaptionContext | None = None) -> str:
    """Sanitize caption before timing append (outer-sign + duplicate timing)."""
    out = strip_transpersonal_outer_sign_copy(caption)
    out = strip_caption_timing_blocks(out)
    if ctx is not None:
        for planet, sign in ((ctx.planet_a, ctx.planet_a_sign), (ctx.planet_b, ctx.planet_b_sign)):
            if sign and not use_sign_in_public_caption(planet):
                label = planet_display_ru(planet)
                z = sign  # canonical English sign name in data
                for pat in (
                    rf"{re.escape(label)}\s+в\s+{re.escape(z)}",
                    rf"{re.escape(label)},\s*тоже\s+в\s+{re.escape(z)}",
                ):
                    out = re.sub(pat, label, out, flags=re.IGNORECASE)
    return out.strip()


def append_timing_once(
    caption: str,
    meta: CatstyleAspectTimingMetadata,
    post_date: date,
    personal_planet: str | None,
) -> str:
    """Exactly one **Про сроки:** block at the end."""
    base = strip_caption_timing_blocks(caption.rstrip())
    return append_ru_timing_to_caption(base, meta, post_date, personal_planet)


__all__ = [
    "append_timing_once",
    "polish_caption_for_package",
    "strip_caption_timing_blocks",
    "strip_transpersonal_outer_sign_copy",
]
