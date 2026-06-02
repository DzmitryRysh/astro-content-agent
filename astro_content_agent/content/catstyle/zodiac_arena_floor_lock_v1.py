"""Reusable zodiac arena floor lock for Catstyle cosmic coliseum scenes."""
from __future__ import annotations

from typing import Final

ZODIAC_ARENA_FLOOR_LOCK_BLOCK: Final[str] = (
    "[ZODIAC ARENA FLOOR LOCK v1] The arena floor must show **only real zodiac glyphs** "
    "(Aries through Pisces) in **correct astrological order**—twelve clear sectors, **no fake runes** "
    "or invented occult symbols. Wheel **engraved or inlaid into colosseum stone brick paving**, "
    "not a painted magic circle. **Visible central compass hub**; floor is **physically part of the arena stone**."
)

ZODIAC_FLOOR_SCALE_FRAMING_BLOCK: Final[str] = (
    "[ZODIAC FLOOR SCALE / FRAMING v1] The zodiac floor is **monumental**—much larger than the fighters. "
    "It must **not** fit fully inside the frame; **prefer** the wheel **extending beyond image boundaries** "
    "(roughly **35–65%** of the circle visible). **Do not** show the **entire circle neatly centered** as a "
    "small complete disc under their feet. Fighters stand on a **huge engraved stone coliseum surface** "
    "integrated with depth, torch lines, arches, and tiers—the floor must not shrink perceived arena scale."
)

ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "random magic circle",
    "fake runes instead of zodiac glyphs",
    "wrong zodiac sign order",
    "fake zodiac symbols",
    "invented pseudo-zodiac floor signs",
    "tiny decorative floor emblem",
    "vague occult floor markings",
)

ZODIAC_FLOOR_SCALE_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "tiny complete zodiac disc under the characters",
    "entire zodiac wheel fitted neatly in frame",
    "neatly centered small magic-circle floor",
    "miniature zodiac platform",
    "small medallion-like floor circle",
    "decorative magic circle under characters feet",
)

__all__ = [
    "ZODIAC_ARENA_FLOOR_LOCK_BLOCK",
    "ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS",
    "ZODIAC_FLOOR_SCALE_FRAMING_BLOCK",
    "ZODIAC_FLOOR_SCALE_NEGATIVE_EXTRAS",
]
