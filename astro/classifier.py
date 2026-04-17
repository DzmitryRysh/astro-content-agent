"""Transit signal classification: foreground vs background.

A transit signal is either:
  foreground -- a strong candidate for today's content hook; at least one of
                the two planets is inner/fast, OR the aspect is so tight that
                even a slow-outer pair deserves attention.
  background -- a slow outer-planet aspect that stays in orb for weeks or
                months; still astrologically real and useful as structural
                context, but should not dominate daily hooks on its own.

Classification heuristic
------------------------
Step 1 -- planet-speed test:
  If at least one planet is NOT in OUTER_SLOW_PLANETS (i.e. it is Sun, Moon,
  Mercury, Venus, Mars, or Jupiter) -> foreground.

  OUTER_SLOW_PLANETS = {Saturn, Uranus, Neptune, Pluto}
  These four move so slowly that any pair between them can stay within a 6-deg
  orb for months (Saturn-Pluto: ~2 yr; Neptune-Pluto: ~decade).

  Jupiter is explicitly kept out of OUTER_SLOW because Jupiter-X aspects cycle
  on a 12-year period and provide digestible, topical content hooks.

Step 2 -- tight-orb override:
  Even when both planets are slow-outer, if the aspect is within
  TIGHT_ORB_THRESHOLD degrees of exact, the signal is elevated to foreground.
  Rationale: a Saturn-Pluto exact conjunction is historically significant;
  skipping it from the daily hook list would be wrong.

The function is pure and side-effect-free so it is trivially testable and
usable as a prompt-layer utility later without any service dependencies.
"""
from __future__ import annotations

from typing import Literal

SignalClass = Literal["foreground", "background"]

# Planets whose mutual aspects persist for months to years at typical orbs.
# Jupiter is intentionally excluded -- its cycle is short enough to be topical.
OUTER_SLOW_PLANETS: frozenset[str] = frozenset({"Saturn", "Uranus", "Neptune", "Pluto"})

# Orb threshold below which even a slow-outer pair is treated as foreground.
TIGHT_ORB_OVERRIDE: float = 1.0  # degrees


def classify_transit(
    planet1: str,
    planet2: str,
    orb: float | None,
) -> SignalClass:
    """Return the signal class for a transit between *planet1* and *planet2*.

    Args:
        planet1: Name of the first planet (e.g. "Saturn").
        planet2: Name of the second planet (e.g. "Pluto").
        orb:     Degrees from exact aspect; ``None`` is treated as unknown
                 (the tight-orb override is not applied when orb is unknown).

    Returns:
        ``"foreground"`` or ``"background"``.
    """
    both_outer_slow = planet1 in OUTER_SLOW_PLANETS and planet2 in OUTER_SLOW_PLANETS

    if not both_outer_slow:
        return "foreground"

    # Both planets are slow-outer -> background by default.
    # Elevate to foreground only if the aspect is unusually tight.
    if orb is not None and orb < TIGHT_ORB_OVERRIDE:
        return "foreground"

    return "background"
