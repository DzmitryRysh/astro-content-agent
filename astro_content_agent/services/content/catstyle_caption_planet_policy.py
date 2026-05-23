"""Which planets may use zodiac sign context in public Catstyle captions."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

# Transpersonal outers: sign is not used for interpretive copy in captions.
CAPTION_NO_SIGN_INTERPRETATION_PLANETS: Final[frozenset[str]] = frozenset(
    {"Uranus", "Neptune", "Pluto"}
)


def use_sign_in_public_caption(planet: str) -> bool:
    """True for Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn; false for Uranus/Neptune/Pluto."""
    raw = (planet or "").strip()
    if not raw:
        return False
    try:
        name = normalize_planet_name(raw)
    except ValueError:
        return False
    return name not in CAPTION_NO_SIGN_INTERPRETATION_PLANETS


__all__ = [
    "CAPTION_NO_SIGN_INTERPRETATION_PLANETS",
    "use_sign_in_public_caption",
]
