"""Astrology engines for daily transit signal generation.

AstroEngineV0: deterministic pseudo-random stub kept for backward
    compatibility and isolated unit tests; do NOT use in production.

AstroEngineV1: real ephemeris engine backed by Swiss Ephemeris / Moshier.
    Produces real planet positions, real aspects, and real orb-based ranking.
    Deterministic from real astronomical input -- no seeded randomness.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import UTC, date, datetime

from astro_content_agent.schemas.astro import AstroDayPayload, ASPECT_POLARITY_MAP, TransitSignal


@dataclass(frozen=True)
class EngineInput:
    """Inputs for transit signal generation."""

    brand_profile_id: str
    day: date


# How many top-ranked aspects (tightest orb) to include per day
MAX_SIGNALS = 5


# ---------------------------------------------------------------------------
# V0 -- kept for backward compatibility and isolated tests only
# ---------------------------------------------------------------------------

class AstroEngineV0:
    """Deterministic pseudo-random stub. Deprecated -- do not use in production."""

    version = "v0.stub"

    _planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    _aspects = ["conjunct", "sextile", "square", "trine", "opposition"]

    def generate_day(self, inp: EngineInput) -> AstroDayPayload:
        rng = random.Random(self._seed_int(inp.brand_profile_id, inp.day))
        signals: list[TransitSignal] = []

        count = rng.randint(3, 5)
        used_keys: set[str] = set()
        for _ in range(count):
            p1, p2 = rng.sample(self._planets, 2)
            aspect = rng.choice(self._aspects)
            intensity = round(rng.random() * 0.7 + 0.2, 3)

            key = self._slug(f"{p1}-{aspect}-{p2}")
            if key in used_keys:
                continue
            used_keys.add(key)

            headline = f"{p1} {aspect} {p2}"
            summary = self._summary(p1=p1, aspect=aspect, p2=p2)
            tags = self._tags(p1=p1, aspect=aspect, p2=p2, rng=rng)
            formats = self._formats(rng=rng)
            angles = self._angles(p1=p1, aspect=aspect, p2=p2, rng=rng)
            guardrails = {
                "avoid": [
                    "guarantees or absolute predictions",
                    "fear-mongering language",
                    "repetitive hooks across multiple posts",
                ]
            }

            signals.append(
                TransitSignal(
                    key=key,
                    headline=headline,
                    summary=summary,
                    intensity=float(intensity),
                    tags=tags,
                    recommended_formats=formats,
                    content_angles=angles,
                    guardrails=guardrails,
                    aspect_polarity=ASPECT_POLARITY_MAP.get(aspect),
                )
            )

        return AstroDayPayload(
            day=inp.day,
            engine_version=self.version,
            generated_at=datetime.now(UTC),
            signals=signals,
        )

    @staticmethod
    def _seed_int(brand_profile_id: str, day: date) -> int:
        raw = f"{brand_profile_id}|{day.isoformat()}".encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        return int(digest[:16], 16)

    @staticmethod
    def _slug(s: str) -> str:
        return (
            s.strip()
            .lower()
            .replace(" ", "-")
            .replace("--", "-")
            .replace("/", "-")
        )

    @staticmethod
    def _summary(p1: str, aspect: str, p2: str) -> str:
        mapping = {
            "conjunct": "themes merge; intensity concentrates",
            "sextile": "opportunity for small wins and supportive momentum",
            "square": "friction reveals what needs adjustment",
            "trine": "flow makes it easier to act with confidence",
            "opposition": "tension invites balance and a clearer choice",
        }
        base = mapping.get(aspect, "signals a shift in focus")
        return f"{p1} and {p2}: {base}."

    @staticmethod
    def _tags(p1: str, aspect: str, p2: str, rng: random.Random) -> list[str]:
        base = {p1.lower(), p2.lower(), aspect}
        extra_pool = ["relationships", "career", "money", "wellness", "mindset", "creativity", "boundaries"]
        for _ in range(rng.randint(1, 2)):
            base.add(rng.choice(extra_pool))
        return sorted(base)

    @staticmethod
    def _formats(rng: random.Random) -> list[str]:
        pool = ["post", "carousel", "reel"]
        rng.shuffle(pool)
        return pool[: rng.randint(1, 2)]

    @staticmethod
    def _angles(p1: str, aspect: str, p2: str, rng: random.Random) -> list[str]:
        angles = [
            "one actionable reflection question",
            "a 3-step micro-ritual for the day",
            "a myth/metaphor framing of the signal",
            "a do/don't list that avoids absolutism",
            "a short journaling prompt + CTA",
        ]
        rng.shuffle(angles)
        if aspect in {"square", "opposition"} and "a do/don't list that avoids absolutism" not in angles[:2]:
            angles.insert(0, "a do/don't list that avoids absolutism")
        return angles[:3]


# ---------------------------------------------------------------------------
# V1 -- Real ephemeris engine
# ---------------------------------------------------------------------------

class AstroEngineV1:
    """Real transit signal generator backed by Swiss Ephemeris (Moshier built-in).

    Algorithm per day:
      1. Compute ecliptic longitudes for all 10 planets at noon UTC.
      2. Detect all five major aspects (conjunction, sextile, square, trine,
         opposition) within standard orb limits for every planet pair.
      3. Rank by orb tightness (smallest orb = strongest signal).
      4. Return the top MAX_SIGNALS aspects as TransitSignal objects.

    Determinism: same date yields same signals regardless of brand_profile_id.
    brand_profile_id is accepted for interface compatibility but has no effect
    on the astronomical calculation -- the sky looks the same for all brands.
    """

    version = "v1.real"

    _ASPECT_MEANING: dict[str, str] = {
        "conjunction": "themes merge; concentrated focus and intensity",
        "sextile":     "supportive opening; easier flow between these energies",
        "square":      "friction that drives adjustment; conscious effort needed",
        "trine":       "natural flow; ease and confident expression",
        "opposition":  "tension invites balance; a clear choice is forming",
    }

    _CONTENT_ANGLES: dict[str, list[str]] = {
        "conjunction": [
            "myth/metaphor framing of the merged energy",
            "one actionable reflection question",
            "a 3-step micro-ritual for the day",
        ],
        "sextile": [
            "a 3-step micro-ritual for the day",
            "one actionable reflection question",
            "a short journaling prompt + CTA",
        ],
        "square": [
            "a do/don't list that avoids absolutism",
            "one actionable reflection question",
            "a short journaling prompt + CTA",
        ],
        "trine": [
            "a 3-step micro-ritual for the day",
            "one actionable reflection question",
            "myth/metaphor framing of the supportive flow",
        ],
        "opposition": [
            "a do/don't list that avoids absolutism",
            "one actionable reflection question",
            "myth/metaphor framing of the tension",
        ],
    }

    def generate_day(self, inp: EngineInput) -> AstroDayPayload:
        from astro_content_agent.astro.classifier import classify_transit
        from astro_content_agent.astro.ephemeris import compute_positions
        from astro_content_agent.astro.aspects import find_aspects

        positions = compute_positions(inp.day)
        all_aspects = find_aspects(positions)
        top = all_aspects[:MAX_SIGNALS]

        signals: list[TransitSignal] = []
        used_keys: set[str] = set()

        for asp in top:
            key = self._slug(f"{asp.planet1}-{asp.aspect}-{asp.planet2}")
            if key in used_keys:
                continue
            used_keys.add(key)

            p1_pos = positions[asp.planet1]
            p2_pos = positions[asp.planet2]

            headline = f"{asp.planet1} {asp.aspect} {asp.planet2}"
            summary = self._build_summary(
                asp.planet1, asp.aspect, asp.planet2, asp.orb,
                p1_pos.sign, p2_pos.sign,
                p1_pos.retrograde, p2_pos.retrograde,
            )
            tags = sorted({
                asp.planet1.lower(), asp.planet2.lower(),
                asp.aspect,
                p1_pos.sign.lower(), p2_pos.sign.lower(),
            })

            signals.append(TransitSignal(
                key=key,
                headline=headline,
                summary=summary,
                intensity=asp.intensity,
                tags=tags,
                recommended_formats=["post", "reel"],
                content_angles=self._CONTENT_ANGLES.get(asp.aspect, []),
                guardrails={
                    "avoid": [
                        "guarantees or absolute predictions",
                        "fear-mongering language",
                        "repetitive hooks across multiple posts",
                    ]
                },
                aspect_polarity=asp.polarity,
                planet1_sign=p1_pos.sign,
                planet2_sign=p2_pos.sign,
                orb=asp.orb,
                planet1_retrograde=p1_pos.retrograde,
                planet2_retrograde=p2_pos.retrograde,
                signal_class=classify_transit(asp.planet1, asp.planet2, asp.orb),
            ))

        return AstroDayPayload(
            day=inp.day,
            engine_version=self.version,
            generated_at=datetime.now(UTC),
            signals=signals,
        )

    def _build_summary(
        self,
        p1: str, aspect: str, p2: str, orb: float,
        sign1: str, sign2: str,
        retro1: bool, retro2: bool,
    ) -> str:
        base = self._ASPECT_MEANING.get(aspect, "signals a shift in focus")
        retro_parts: list[str] = []
        if retro1:
            retro_parts.append(f"{p1} Rx")
        if retro2:
            retro_parts.append(f"{p2} Rx")
        retro_str = f" [{', '.join(retro_parts)}]" if retro_parts else ""
        return (
            f"{p1} ({sign1}) {aspect} {p2} ({sign2}) -- orb {orb:.2f}deg"
            f"{retro_str}: {base}."
        )

    @staticmethod
    def _slug(s: str) -> str:
        return (
            s.strip()
            .lower()
            .replace(" ", "-")
            .replace("--", "-")
            .replace("/", "-")
        )
