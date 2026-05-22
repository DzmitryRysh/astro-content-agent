"""Reusable zodiac arena floor lock for Catstyle cosmic coliseum scenes."""
from __future__ import annotations

from typing import Final

ZODIAC_ARENA_FLOOR_LOCK_BLOCK: Final[str] = (
    "[ZODIAC ARENA FLOOR LOCK v1] The arena floor must contain a **large readable zodiac wheel** "
    "**engraved or inlaid into stone brick paving**—a major Catstyle universe anchor, **not a random magic circle**. "
    "**Canonical zodiac glyphs** around the wheel, **clear sector divisions**, **visible central medallion/compass center**; "
    "floor feels **physically part of the arena**—readable but not stealing focus from fighters."
)

ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "random magic circle",
    "fake zodiac symbols",
    "tiny decorative floor emblem",
    "incomplete zodiac wheel",
    "vague occult floor markings",
)

__all__ = [
    "ZODIAC_ARENA_FLOOR_LOCK_BLOCK",
    "ZODIAC_ARENA_FLOOR_NEGATIVE_EXTRAS",
]
