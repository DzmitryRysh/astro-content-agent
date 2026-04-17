"""Major-aspect detection between planet pairs.

Supports the five standard major aspects with content-generation orb limits.
All aspects are detected by computing the shortest angular separation between
two ecliptic longitudes and comparing it to the aspect angle +/- its orb.

Aspect intensity is a linear measure of proximity to exact:
  intensity = 1.0 at exact aspect, 0.0 at the orb boundary.

Orb policy (DEFAULT_ORB_CONFIG):
  Tight enough to surface only high-confidence daily transits and suppress
  weak stretched aspects that would dilute content quality.  Stored as a
  plain dict so they can be overridden per-engine-instance in a future config
  layer without changing the detection function signature.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.schemas.astro import ASPECT_POLARITY_MAP, AspectPolarity

# ---------------------------------------------------------------------------
# Orb policy
# aspect_name -> (exact_angle_degrees, max_orb_degrees)
#
# DEFAULT_ORB_CONFIG uses tighter-than-traditional orbs suited for daily
# transit content:
#   - eliminates noise from barely-in-orb outer-planet pairings
#   - keeps the top-5 selection meaningful
#   - still captures the Moon's fast-moving aspects (moves ~13 deg/day)
#
# To experiment with wider orbs, pass a custom dict to find_aspects().
# ---------------------------------------------------------------------------

DEFAULT_ORB_CONFIG: dict[str, tuple[float, float]] = {
    "conjunction": (0.0,   6.0),
    "sextile":     (60.0,  4.0),
    "square":      (90.0,  5.0),
    "trine":       (120.0, 6.0),
    "opposition":  (180.0, 6.0),
}

# Keep the old wider config available for reference / backward compat tests
ASPECT_CONFIG = DEFAULT_ORB_CONFIG  # alias used by existing tests


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AspectResult:
    planet1: str
    planet2: str
    aspect: str
    orb: float              # degrees from exact; always ≥ 0
    max_orb: float          # orb ceiling for this aspect type
    polarity: AspectPolarity | None
    intensity: float        # 1.0 = exact, approaches 0.0 at the orb ceiling


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _angular_distance(lon1: float, lon2: float) -> float:
    """Shortest arc between two ecliptic longitudes (always 0–180°)."""
    diff = abs(lon1 - lon2) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


def find_aspects(
    positions: dict[str, PlanetPosition],
    *,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> list[AspectResult]:
    """Return all major aspects within orb, sorted by tightness (smallest orb first).

    Args:
        positions: Planet name -> PlanetPosition mapping from ephemeris.compute_positions.
        orb_config: Optional override for aspect orb limits.  Defaults to
                    DEFAULT_ORB_CONFIG.  Pass a custom dict to experiment with
                    wider or narrower orbs without touching module-level state.

    Returns:
        List of AspectResult objects sorted ascending by orb.  A single planet
        pair can appear for multiple aspect types if their separation happens to
        fall within several orbs simultaneously (rare; only possible near the
        transition between aspect windows).
    """
    config = orb_config if orb_config is not None else DEFAULT_ORB_CONFIG
    results: list[AspectResult] = []

    for p1_name, p2_name in combinations(positions.keys(), 2):
        p1 = positions[p1_name]
        p2 = positions[p2_name]
        dist = _angular_distance(p1.longitude, p2.longitude)

        for aspect_name, (angle, max_orb) in config.items():
            orb = abs(dist - angle)
            if orb <= max_orb:
                intensity = round(max(0.0, 1.0 - orb / max_orb), 4)
                results.append(AspectResult(
                    planet1=p1_name,
                    planet2=p2_name,
                    aspect=aspect_name,
                    orb=round(orb, 4),
                    max_orb=max_orb,
                    polarity=ASPECT_POLARITY_MAP.get(aspect_name),
                    intensity=intensity,
                ))

    results.sort(key=lambda r: r.orb)
    return results
