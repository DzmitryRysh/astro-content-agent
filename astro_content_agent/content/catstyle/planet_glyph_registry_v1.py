"""Canonical planetary glyphs + Catstyle pair-flag prompt fragments (v1).

Single source of truth for Unicode astrological symbols used in image prompts
and optional tooling. ``planet_a`` maps to **left/port** banner; ``planet_b``
to **right/starboard** banner.
"""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

# Unicode astrological symbols (canonical for Catstyle). Moon = ☽ (U+263D).
CANONICAL_PLANET_GLYPHS: Final[dict[str, str]] = {
    "sun": "\u2609",  # ☉
    "moon": "\u263d",  # ☽
    "mercury": "\u263f",  # ☿
    "venus": "\u2640",  # ♀
    "mars": "\u2642",  # ♂
    "jupiter": "\u2643",  # ♃
    "saturn": "\u2644",  # ♄
    "uranus": "\u2645",  # ♅
    "neptune": "\u2646",  # ♆
    "pluto": "\u2647",  # ♇
}

SUPPORTED_PLANET_GLYPH_KEYS: Final[frozenset[str]] = frozenset(CANONICAL_PLANET_GLYPHS.keys())


GLYPH_HARDENING: Final[dict[str, str]] = {
    "sun": (
        "[Sun ☉ hardening] Paint canonical **\u2609 (☉)** on the Sun banner: **circle with central dot**, "
        "large, complete, clean, cloth-integrated—not partial, cropped, approximate, or a generic coin / letter O."
    ),
    "moon": (
        "[Moon ☽ hardening] Paint **\u263d (☽)** as a clear crescent-with-disc lunar mark on the Moon banner—"
        "not a backward C smudge, not a random sickle rune, not a second unrelated moon icon elsewhere."
    ),
    "mercury": (
        "[Mercury ☿ hardening] Canonical **\u263f**: circle with small **crescent/horns above** and **cross below**—"
        "painted into **Mercury's** own faction banner cloth per the port/starboard assignment above; "
        "not a random knot, not a pseudo-alphabet letter."
    ),
    "venus": (
        "[Venus ♀ hardening] Canonical **\u2640**: circle with small cross below—mirror-clean female-sign geometry on Venus's banner; "
        "not a distorted mirror of Mars, not a jewelry charm that replaces the glyph."
    ),
    "mars": (
        "[Mars ♂ hardening] Canonical **\u2642**: circle with spear/arrow emerging at ~45° on Mars's **left/port** banner when Mars is planet A "
        "(or **right/starboard** when Mars is planet B)—clear ring + arrow read; not omega \u03a9, not a plain plus, not a lumpy blob."
    ),
    "jupiter": (
        "[Jupiter ♃ hardening] Canonical **\u2643 (♃)** must read as the stylized **number-4** silhouette with **curved upper stroke** "
        "and **cross-like lower structure** on Jupiter's banner—**must not** read as Latin **J**, digit **1**, a fish-hook, "
        "**lambda (\u039b)**, a random rune, or a melted pseudo-symbol."
    ),
    "saturn": (
        "[Saturn ♄ hardening] Canonical **\u2644 (♄)** must keep the **hook/crossbar** Saturn silhouette on Saturn's banner—"
        "clearly **Saturn**, not a bare **h** letterform, not a random hooked stroke, not a collapsed smear."
    ),
    "uranus": (
        "[Uranus ♅ hardening] Paint canonical **\u2645 (♅)** on Uranus's banner: **full glyph** with **vertical stem, "
        "side arcs, lower circle**, large, complete, readable on cloth—not partial, cropped, fake rune, "
        "H-with-orbit doodle, or swapped Neptune mark."
    ),
    "neptune": (
        "[Neptune ♆ hardening] Use canonical **\u2646 (♆)** on Neptune's banner—standard trident-derived Neptune glyph; "
        "not a fork with extra random bars, not Uranus/Pluto confusion."
    ),
    "pluto": (
        "[Pluto ♇ hardening] Use canonical **\u2647 (♇)** on Pluto's banner—P+L combined Pluto form; "
        "not a generic skull rune, not a made-up sigil."
    ),
}


def planet_glyph_key(planet_name: str) -> str:
    return normalize_planet_name(planet_name).strip().lower()


def canonical_glyph_char(planet_name: str) -> str | None:
    """Return the single Unicode glyph for *planet_name*, or ``None`` if unknown."""
    return CANONICAL_PLANET_GLYPHS.get(planet_glyph_key(planet_name))


def glyph_prompt_label(planet_name: str) -> str | None:
    """``Name (CHAR)`` for prompt lines, e.g. ``Mercury (\u263f)``."""
    ch = canonical_glyph_char(planet_name)
    if not ch:
        return None
    return f"{normalize_planet_name(planet_name)} ({ch})"


def format_pair_flag_glyph_system_block(planet_a: str, planet_b: str) -> str:
    """Deterministic [CATSTYLE PAIR FLAG GLYPH SYSTEM v1] block for any supported pair."""
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    ga = canonical_glyph_char(pa)
    gb = canonical_glyph_char(pb)
    if not ga or not gb:
        return ""

    la = glyph_prompt_label(pa)
    lb = glyph_prompt_label(pb)
    assert la is not None and lb is not None

    base = (
        f"[CATSTYLE PAIR FLAG GLYPH SYSTEM v1] **Left/port faction banner = {la}**; **right/starboard faction banner = {lb}**. "
        "Each side carries **one large canonical planetary glyph painted into the flag cloth** as part of the illustration—"
        "**flat heraldic gold paint or embroidered-thread emblem**, **centered** on its banner field, **warped with fabric folds, perspective, occlusion, and key/rim light**, "
        "**readable at Instagram / mobile thumbnail scale**. "
        "**Negatives (all planets):** no malformed planetary signs, no fake letters, no pseudo-glyphs, no random occult runes replacing planet symbols, "
        "no floating post-process overlay stickers, no pasted symbols over faces/foreheads/muzzles/torsos, no detached glow not locked to the cloth surface."
    )

    extras: list[str] = []
    seen: set[str] = set()
    for pname in (pa, pb):
        k = planet_glyph_key(pname)
        if k in seen:
            continue
        seen.add(k)
        h = GLYPH_HARDENING.get(k)
        if h:
            extras.append(h)
    if not extras:
        return base
    return f"{base} " + " ".join(extras)


__all__ = [
    "CANONICAL_PLANET_GLYPHS",
    "GLYPH_HARDENING",
    "SUPPORTED_PLANET_GLYPH_KEYS",
    "canonical_glyph_char",
    "format_pair_flag_glyph_system_block",
    "glyph_prompt_label",
    "planet_glyph_key",
]
