"""Global Catstyle premium quality lock (all generations)."""
from __future__ import annotations

from typing import Final

CATSTYLE_GLOBAL_QUALITY_LOCK_BLOCK: Final[str] = (
    "[CATSTYLE GLOBAL QUALITY LOCK v2] Mandatory finish for every generation: **premium cinematic comic-poster** "
    "with **comic-cover polish**—**sharper linework**, **stronger contrast**, **dramatic poster lighting** "
    "(rim + impact keys), never storybook or children-book illustration. "
    "**World shell:** monumental **cosmic zodiac coliseum arena** at tournament scale—clear **foreground / midground / background** depth. "
    "**Earth disk visible above** the arena vault as a readable distant anchor. "
    "**Arena floor:** **zodiac circle engraved into stone floor / stone brick paving**—bold constellation band in masonry. "
    "**Composition:** high-drama heroic staging, **strong silhouettes**, **action or symbolic tension** with kinetic read—"
    "**not** static standing confrontation or idle mascot posing. "
    "**Identity:** each planet-cat keeps clear planetary identity; **integrated flag glyphs** woven into banner cloth "
    "(canonical heraldic gold, cloth-locked—never floating sticker overlays). "
    "**Anti-drift:** reject watercolor/storybook softness, cozy cute low-drama tableau, flat toy-like mascots."
)

CATSTYLE_GLOBAL_QUALITY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "storybook illustration",
    "children-book style",
    "picture-book watercolor softness",
    "soft watercolor look",
    "watercolor storybook softness",
    "cozy cute low-drama scene",
    "flat mascot look",
    "toy-like cats",
    "weak simple confrontation",
    "static standing confrontation",
    "two cats merely pointing at each other",
    "idle mascot posing with no kinetic tension",
    "generic cute cartoon",
    "painterly softness that loses comic-poster edge",
    "nursery-book diffusion dominance",
    "low-stakes playground duel energy",
    "soft pastel storybook palette dominance",
    "blurred mushy linework without poster edge",
)

__all__ = [
    "CATSTYLE_GLOBAL_QUALITY_LOCK_BLOCK",
    "CATSTYLE_GLOBAL_QUALITY_NEGATIVE_EXTRAS",
]
