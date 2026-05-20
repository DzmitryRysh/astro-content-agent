"""Pair-specific premium visual canon: Mars square Pluto (tension).

Locks the strong legacy Mars/Pluto read (frontal heat vs underworld control) into the
cosmic zodiac coliseum arena stack—correct left/right staging, canonical flag glyphs,
and anti-drift negatives. Order of ``planet_a`` / ``planet_b`` in requests does not
change composition or banner assignment for this aspect/mode.
"""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.planet_glyph_registry_v1 import format_pair_flag_glyph_system_block


# Marked stable for daily-agent auto-publish (pair-specific canon without approved PNG required).
MARS_PLUTO_SQUARE_TENSION_CREATIVE_PUBLISH_STABLE: Final[bool] = True


def is_mars_pluto_square_tension(planet_a: str, planet_b: str, aspect_type: str, mode: str) -> bool:
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    if {pa, pb} != {"Mars", "Pluto"}:
        return False
    if (aspect_type or "").strip().lower() != "square":
        return False
    return (mode or "").strip().lower() == "tension"


def is_mars_pluto_square_tension_creative_publish_stable(
    planet_a: str, planet_b: str, aspect_type: str, mode: str
) -> bool:
    """True when Mars/Pluto square tension canon is active and marked stable for auto-publish."""
    return MARS_PLUTO_SQUARE_TENSION_CREATIVE_PUBLISH_STABLE and is_mars_pluto_square_tension(
        planet_a, planet_b, aspect_type, mode
    )


def resolved_pair_flag_glyph_system_block(
    planet_a: str, planet_b: str, aspect_type: str, mode: str
) -> str:
    """Left/port = Pluto ♇, right/starboard = Mars ♂ for Mars–Pluto square + tension."""
    if is_mars_pluto_square_tension(planet_a, planet_b, aspect_type, mode):
        return format_pair_flag_glyph_system_block("Pluto", "Mars").strip()
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    return format_pair_flag_glyph_system_block(pa, pb).strip()


MARS_PLUTO_SQUARE_TENSION_VISUAL_CANON: Final[str] = (
    "[MARS-PLUTO SQUARE TENSION VISUAL CANON v1] "
    "Lock the **strong legacy concept** into the **premium cosmic zodiac coliseum arena** (monumental tiered "
    "coliseum architecture, massive zodiac-ring scale, strong layered foreground/midground/background depth). "
    "**Earth disk visible above** the arena vault as a readable distant scale anchor—never replace that cue with "
    "another planet body. "
    "**Character force split:** **Mars** reads as **fiery frontal direct-force fighter**—impulse, attack vector, "
    "combat heat, savage pressure, immediate kinetic threat. **Pluto** reads as **dark underworld manipulator**—"
    "reactor-core menace, shadow tendrils, psychological domination, deep control, cauldron/smoke weight. "
    "**Square tension:** collision of **brute will vs buried power**—apocalyptic volcanic stakes, domination versus "
    "eruption; **not** a cute duel or toy spar. "
    "**Mandatory placement (screen geometry):** **Pluto planet-cat + Pluto faction occupy the LEFT half** of the composition; "
    "**Mars planet-cat + Mars faction occupy the RIGHT half**—preserve this read at poster scale even during diagonal motion. "
    "**Glyph / flag hard-lock:** integrated planetary-flag cloth only—left banner cloth shows **only Pluto glyph "
    "\u2647 (♇)**; right banner cloth shows **only Mars glyph \u2642 (♂)**—large clean canonical marks woven into fabric "
    "with folds, perspective, and key/rim light (**[CATSTYLE PAIR FLAG GLYPH SYSTEM v1]** cloth rules). "
    "**Never** paint **Venus glyph \u2640 (♀)** on any banner; never swap Mars/Pluto signs; never substitute female-sign "
    "geometry for Mars. "
    "**Lighting / finish:** dramatic rim and impact lighting, premium cinematic comic-poster polish, volcanic rim glow "
    "with readable midtones—faces and glyphs stay Instagram-thumb legible. "
    "**Drift negatives (this pair):** reject cute mascot comedy dominance, childish cartoon, goofy humor beats, silly gag props, "
    "toy-like cats, low-stakes playground duel, flat simplistic brawl, kawaii sticker energy, preschool simplicity—stay "
    "dead-serious mythic heavyweight."
)


MARS_PLUTO_SQUARE_TENSION_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "Venus glyph ♀ on any faction banner or flag cloth",
    "female-sign geometry substituting for Mars glyph",
    "cute mascot duel comedy as dominant read",
    "toylike or preschool-simple sparring scene",
    "chibi dominance or kawaii softness overload",
    "wrong planetary glyph on the wrong character's banner",
)


__all__ = [
    "MARS_PLUTO_SQUARE_TENSION_CREATIVE_PUBLISH_STABLE",
    "MARS_PLUTO_SQUARE_TENSION_NEGATIVE_EXTRAS",
    "MARS_PLUTO_SQUARE_TENSION_VISUAL_CANON",
    "is_mars_pluto_square_tension",
    "is_mars_pluto_square_tension_creative_publish_stable",
    "resolved_pair_flag_glyph_system_block",
]
