"""Real planet-position calculations via Swiss Ephemeris (pyswisseph).

Uses the Moshier built-in algorithm (FLG_MOSEPH), which requires no separate
ephemeris data files and is accurate to within a few arc-seconds for all
planets Sun–Pluto. This accuracy is more than adequate for orb-based transit
detection used in daily content generation.

Daily transit generation uses noon UTC (12:00) as the representative moment,
which is a standard convention for "day charts" in mundane astrology.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import swisseph as swe

# ---------------------------------------------------------------------------
# Planet registry – ordered by traditional speed (fastest first)
# ---------------------------------------------------------------------------

PLANETS: dict[str, int] = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus":   swe.VENUS,
    "Mars":    swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn":  swe.SATURN,
    "Uranus":  swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto":   swe.PLUTO,
}

ZODIAC_SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Moshier built-in + include speed (to detect retrograde)
_CALC_FLAG: int = swe.FLG_MOSEPH | swe.FLG_SPEED


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlanetPosition:
    name: str
    longitude: float    # ecliptic longitude 0–360°
    sign: str           # zodiac sign name
    sign_degree: float  # degrees within the sign (0–30)
    retrograde: bool    # True when apparent motion is retrograde (speed_lon < 0)
    speed: float        # degrees/day in ecliptic longitude


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def sign_for_longitude(longitude: float) -> tuple[str, float]:
    """Return (sign_name, degree_within_sign) for any ecliptic longitude."""
    lon = longitude % 360.0
    idx = int(lon / 30)
    return ZODIAC_SIGNS[idx], round(lon - idx * 30, 4)


def compute_positions(day: date, *, hour_utc: float = 12.0) -> dict[str, PlanetPosition]:
    """Compute ecliptic positions for all tracked planets at *hour_utc* UTC on *day*.

    Args:
        day: Calendar date for which to compute positions.
        hour_utc: Decimal hour in Universal Time (default 12.0 = noon).

    Returns:
        Mapping of planet name → PlanetPosition. Always contains all 10 planets.

    Raises:
        RuntimeError: If the Swiss Ephemeris library returns an error for any planet.
    """
    jd = swe.julday(day.year, day.month, day.day, hour_utc)
    positions: dict[str, PlanetPosition] = {}

    for name, planet_id in PLANETS.items():
        xx, retval = swe.calc_ut(jd, planet_id, _CALC_FLAG)
        if retval < 0:
            raise RuntimeError(
                f"swisseph error computing {name} on {day}: retval={retval}"
            )
        lon = xx[0] % 360.0
        speed = xx[3]   # degrees/day; negative means retrograde
        sign, deg = sign_for_longitude(lon)
        positions[name] = PlanetPosition(
            name=name,
            longitude=round(lon, 6),
            sign=sign,
            sign_degree=deg,
            retrograde=speed < 0.0,
            speed=round(speed, 6),
        )

    return positions
