"""Reusable flag-glyph fidelity lock for Catstyle arena banners."""
from __future__ import annotations

from typing import Final

FLAG_GLYPH_FIDELITY_LOCK_BLOCK: Final[str] = (
    "[FLAG GLYPH FIDELITY LOCK v1] Planet glyphs on banners must be **canonical, complete, large, readable**, "
    "and **painted/woven into flag cloth**—not partial glyphs, fake runes, approximations, cropped symbols, "
    "or floating sticker overlays."
)

SUN_URANUS_FLAG_GLYPH_FIDELITY_BLOCK: Final[str] = (
    "[SUN-URANUS FLAG GLYPH FIDELITY v1] **Left Sun banner:** canonical **\u2609 (☉)**—**full circle with central dot**, "
    "large and phone-readable. **Right Uranus banner:** canonical **\u2645 (♅)**—**complete glyph** with "
    "**vertical stem, side arcs, and lower circle**. Reject incomplete glyphs or random rune substitutes."
)

FLAG_GLYPH_FIDELITY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "incomplete flag glyphs",
    "fake Uranus glyph",
    "partial Sun glyph",
    "random rune symbols",
    "cropped banner glyphs",
)

# Re-export banner-only discipline for backward-compatible imports.
from astro_content_agent.content.catstyle.banner_glyph_reference_v1 import (  # noqa: E402
    BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK,
    BANNER_ONLY_GLYPH_NEGATIVE_EXTRAS,
)

__all__ = [
    "BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK",
    "BANNER_ONLY_GLYPH_NEGATIVE_EXTRAS",
    "FLAG_GLYPH_FIDELITY_LOCK_BLOCK",
    "FLAG_GLYPH_FIDELITY_NEGATIVE_EXTRAS",
    "SUN_URANUS_FLAG_GLYPH_FIDELITY_BLOCK",
]
