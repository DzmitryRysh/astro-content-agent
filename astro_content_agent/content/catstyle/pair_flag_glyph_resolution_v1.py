"""Central pair-specific flag glyph resolution (order-stable staging overrides)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.mars_pluto_square_tension_canon_v1 import (
    is_mars_pluto_square_tension,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.planet_glyph_registry_v1 import format_pair_flag_glyph_system_block
from astro_content_agent.content.catstyle.sun_uranus_conjunction_tension_canon_v1 import (
    is_sun_uranus_conjunction_tension,
    sun_uranus_conjunction_tension_flag_glyph_block,
)


def resolved_pair_flag_glyph_system_block(
    planet_a: str, planet_b: str, aspect_type: str, mode: str
) -> str:
    """Pair-specific left/right banner glyphs; falls back to planet_a left / planet_b right."""
    su = sun_uranus_conjunction_tension_flag_glyph_block(planet_a, planet_b, aspect_type, mode)
    if su:
        return su
    if is_mars_pluto_square_tension(planet_a, planet_b, aspect_type, mode):
        return format_pair_flag_glyph_system_block("Pluto", "Mars").strip()
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    return format_pair_flag_glyph_system_block(pa, pb).strip()


__all__ = ["resolved_pair_flag_glyph_system_block"]
