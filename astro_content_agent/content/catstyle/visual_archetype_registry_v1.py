"""Visual archetype fallback references when no exact pair/aspect/mode approved image exists."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

ArchetypeMode = str  # tension | flow | neutral


class VisualArchetypeEntry(BaseModel):
    """Approved archetype row: shared visual dynamics for a family of aspects."""

    archetype_key: str
    description: str = ""
    planet_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Order-insensitive planet pairs, e.g. ('Sun', 'Uranus').",
    )
    modes: list[str] = Field(
        default_factory=list,
        description="Supported modes: tension, flow, neutral (empty = any).",
    )
    aspect_types: list[str] = Field(
        default_factory=list,
        description="Optional aspect filter; empty = any major aspect.",
    )
    image_path: str = Field(description="Path relative to repo root (POSIX slashes).")
    prompt_guidance: str = Field(
        default="",
        description="Short visual-direction block appended when this archetype reference is used.",
    )
    priority: int = Field(default=0, description="Higher wins among matching archetypes.")
    active: bool = True

    def matches_pair(self, planet_a: str, planet_b: str) -> bool:
        try:
            want = frozenset({normalize_planet_name(planet_a), normalize_planet_name(planet_b)})
        except ValueError:
            return False
        for a, b in self.planet_pairs:
            try:
                got = frozenset({normalize_planet_name(a), normalize_planet_name(b)})
            except ValueError:
                continue
            if got == want:
                return True
        return False

    def matches_mode(self, mode: str) -> bool:
        mo = (mode or "").strip().lower()
        if not self.modes:
            return True
        allowed = {m.strip().lower() for m in self.modes}
        return mo in allowed or "neutral" in allowed


class ResolvedArchetypeReference(BaseModel):
    archetype_key: str
    image_path: str = Field(description="Absolute resolved filesystem path.")
    description: str = ""
    prompt_guidance: str = ""
    priority: int = 0


def _absolute_image_path(rel: str) -> str:
    rel_clean = rel.strip().replace("\\", "/")
    return str((catstyle_repo_root() / Path(rel_clean)).resolve())


def _entry(
    *,
    archetype_key: str,
    description: str,
    planet_pairs: list[tuple[str, str]],
    modes: list[str],
    image_path: str,
    prompt_guidance: str,
    priority: int = 50,
    aspect_types: list[str] | None = None,
) -> VisualArchetypeEntry:
    return VisualArchetypeEntry(
        archetype_key=archetype_key,
        description=description,
        planet_pairs=planet_pairs,
        modes=modes,
        aspect_types=aspect_types or [],
        image_path=image_path,
        prompt_guidance=prompt_guidance,
        priority=priority,
        active=True,
    )


VISUAL_ARCHETYPE_REGISTRY: Final[tuple[VisualArchetypeEntry, ...]] = (
    _entry(
        archetype_key="fire_electric_tension",
        description="Fire + electric rupture: solar heat meets sudden lightning disruption.",
        planet_pairs=[("Sun", "Uranus"), ("Mars", "Uranus")],
        modes=["tension"],
        image_path="references/catstyle_sun_uranus_conjunction_tension_approved.png",
        prompt_guidance=(
            "Archetype fire_electric_tension: epic arena scale, warm solar corona vs sharp electric "
            "zig-zag disruption, readable dual planetary identities, high contrast, no mushy fog."
        ),
        priority=80,
    ),
    _entry(
        archetype_key="fire_shadow_tension",
        description="Strike vs depth pressure: martial heat against plutonic control.",
        planet_pairs=[("Mars", "Pluto"), ("Pluto", "Mars")],
        modes=["tension"],
        image_path="references/catstyle_pluto_mars_approved.png",
        prompt_guidance=(
            "Archetype fire_shadow_tension: controlled strike energy vs cauldron-depth pressure, "
            "readable Mars and Pluto identities, arena floor, no swapped glyphs."
        ),
        priority=80,
    ),
    _entry(
        archetype_key="moon_neptune_dream_fog",
        description="Lunar vulnerability dissolving into neptunian mist.",
        planet_pairs=[("Moon", "Neptune"), ("Neptune", "Moon")],
        modes=["tension", "neutral"],
        image_path="references/catstyle_moon_saturn_square_tension_approved.png",
        prompt_guidance=(
            "Archetype moon_neptune_dream_fog: soft lunar body language, neptune mist at edges, "
            "premium arena but slightly dreamlike haze — still readable cat-planet silhouettes."
        ),
        priority=70,
    ),
    _entry(
        archetype_key="mind_expansion_flow",
        description="Quick mind meets generous horizon — light, open flow.",
        planet_pairs=[("Mercury", "Jupiter"), ("Jupiter", "Mercury")],
        modes=["flow"],
        image_path="references/catstyle_mercury_jupiter_sextile_flow_approved.png",
        prompt_guidance=(
            "Archetype mind_expansion_flow: scholar-cat Mercury + expansive Jupiter, bright arena, "
            "open gestures, polished comic poster finish, optimistic scale."
        ),
        priority=85,
    ),
    _entry(
        archetype_key="pressure_structure_tension",
        description="Emotional need vs cold structure — weight and boundary.",
        planet_pairs=[
            ("Moon", "Saturn"),
            ("Saturn", "Moon"),
            ("Jupiter", "Saturn"),
            ("Saturn", "Jupiter"),
        ],
        modes=["tension"],
        image_path="references/catstyle_moon_saturn_square_tension_approved.png",
        prompt_guidance=(
            "Archetype pressure_structure_tension: monumental arena, ringed Saturn authority, "
            "lunar vulnerability, crisp structure, Earth cue, no smoke-trail clutter."
        ),
        priority=75,
    ),
    _entry(
        archetype_key="love_magnetism_tension",
        description="Charm vs obsession — attraction with hidden leverage.",
        planet_pairs=[("Venus", "Pluto"), ("Pluto", "Venus")],
        modes=["tension"],
        image_path="references/catstyle_saturn_venus_square_tension_approved.png",
        prompt_guidance=(
            "Archetype love_magnetism_tension: Venus grace vs Pluto depth-pressure, readable rose/chain "
            "metaphors, magnetic tension without horror gore."
        ),
        priority=72,
    ),
)


def load_visual_archetype_registry() -> tuple[VisualArchetypeEntry, ...]:
    return VISUAL_ARCHETYPE_REGISTRY


def resolve_archetype_reference(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    *,
    registry: tuple[VisualArchetypeEntry, ...] | None = None,
) -> ResolvedArchetypeReference | None:
    """Pick the highest-priority active archetype matching pair + mode."""
    asp = (aspect_type or "").strip().lower()
    rows = registry if registry is not None else load_visual_archetype_registry()
    matches: list[VisualArchetypeEntry] = []
    for row in rows:
        if not row.active:
            continue
        if not row.matches_pair(planet_a, planet_b):
            continue
        if not row.matches_mode(mode):
            continue
        if row.aspect_types:
            allowed = {a.strip().lower() for a in row.aspect_types}
            if asp and asp not in allowed:
                continue
        matches.append(row)
    if not matches:
        return None
    winner = sorted(matches, key=lambda e: (-e.priority, e.archetype_key))[0]
    return ResolvedArchetypeReference(
        archetype_key=winner.archetype_key,
        image_path=_absolute_image_path(winner.image_path),
        description=winner.description,
        prompt_guidance=winner.prompt_guidance,
        priority=winner.priority,
    )


__all__ = [
    "ResolvedArchetypeReference",
    "VISUAL_ARCHETYPE_REGISTRY",
    "VisualArchetypeEntry",
    "load_visual_archetype_registry",
    "resolve_archetype_reference",
]
