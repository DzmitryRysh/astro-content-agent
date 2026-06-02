"""Global square-aspect conflict choreography (Catstyle Square Conflict Law v1)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

SQUARE_CONFLICT_LAW_MARKER: Final[str] = "[SQUARE CONFLICT LAW v1]"

SQUARE_CONFLICT_LAW_BLOCK: Final[str] = (
    "[SQUARE CONFLICT LAW v1] Every square = active struggle, pressure, confrontation—no calm face-off, "
    "polite magical exchange, neutral posing, peaceful ritual, or balanced cooperation. "
    "Visible conflict choreography: attack vs resistance, force vs obstruction, rupture, friction, distortion, "
    "or domination struggle. At least one planet-cat must press, strike, block, trap, rupture, freeze, distort, "
    "burn, shock, bind, drown, or overpower the other's force. Combat language fits the planets; square always combative."
)

SQUARE_CONFLICT_LAW_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "calm face-off",
    "polite magical exchange",
    "neutral posing",
    "peaceful ritual",
    "balanced cooperation",
    "friendly magical exchange",
    "static character posing",
    "no visible conflict",
    "weak square tension",
    "romantic peaceful square",
    "symbolic only aspect scene",
)

_PAIR_SQUARE_CONFLICT_EXAMPLES: Final[dict[frozenset[str], str]] = {
    frozenset({"Mars", "Uranus"}): (
        "Mars square Uranus: explosive impact, shield vs lightning, sudden shock, violent disruption."
    ),
    frozenset({"Mercury", "Neptune"}): (
        "Mercury square Neptune: precise signal/glyph beam distorted, drowned, or dissolved by fog/tide/dream-force."
    ),
    frozenset({"Venus", "Saturn"}): (
        "Venus square Saturn: beauty/desire/rose-light under pressure from cold restriction, chains, stone walls, "
        "time, denial, freezing structure—not a peaceful romantic scene."
    ),
    frozenset({"Sun", "Pluto"}): (
        "Sun square Pluto: royal solar force versus underworld pressure, domination, control, shadow power, volcanic will clash."
    ),
    frozenset({"Moon", "Saturn"}): (
        "Moon square Saturn: vulnerable lunar softness pressured by cold authority, walls, chains, emotional containment."
    ),
}


def is_square_conflict_aspect(aspect_type: str, mode: str | None = None) -> bool:
    if (aspect_type or "").strip().lower() != "square":
        return False
    return (mode or "").strip().lower() != "flow"


def build_square_conflict_law_block(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str | None = None,
) -> str:
    """Square conflict hardlock with optional planet-pair combat example."""
    if not is_square_conflict_aspect(aspect_type, mode):
        return ""
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    example = _PAIR_SQUARE_CONFLICT_EXAMPLES.get(frozenset({pa, pb}), "")
    if example:
        return f"{SQUARE_CONFLICT_LAW_BLOCK} {example}"
    return SQUARE_CONFLICT_LAW_BLOCK


__all__ = [
    "SQUARE_CONFLICT_LAW_BLOCK",
    "SQUARE_CONFLICT_LAW_MARKER",
    "SQUARE_CONFLICT_LAW_NEGATIVE_EXTRAS",
    "build_square_conflict_law_block",
    "is_square_conflict_aspect",
]
