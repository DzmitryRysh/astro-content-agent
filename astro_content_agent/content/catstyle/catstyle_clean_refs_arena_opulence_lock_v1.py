"""Clean-refs arena opulence, lighting richness, and scale dominance (v1)."""
from __future__ import annotations

from typing import Final

ARENA_OPULENCE_HARDLOCK_MARKER: Final[str] = "[ARENA OPULENCE HARDLOCK v1]"
ARENA_LIGHTING_RICHNESS_MARKER: Final[str] = "[ARENA LIGHTING RICHNESS v1]"
ARENA_SCALE_DOMINANCE_MARKER: Final[str] = "[ARENA SCALE DOMINANCE v3]"
ARENA_PRIORITY_SAFETY_MARKER: Final[str] = "[ARENA PRIORITY SAFETY v1]"

# Background-only arena guidance; planet identity and material fidelity take precedence.
ARENA_OPULENCE_HARDLOCK_BLOCK: Final[str] = (
    "[ARENA OPULENCE HARDLOCK v1] Match approved arena ref: imperial golden/amber coliseum—monumental arches, "
    "balconies, statues, torchlight, gilded stone; rich regal upscale, not plain empty dark muddy austere."
)

ARENA_LIGHTING_RICHNESS_BLOCK: Final[str] = (
    "[ARENA LIGHTING RICHNESS v1] Warm golden torchlight, amber glow, luminous edges, readable depth, premium contrast; "
    "visible arches, statues, tiers—no underexposed arena."
)

ARENA_SCALE_DOMINANCE_BLOCK: Final[str] = (
    "[ARENA SCALE DOMINANCE v3] Epic coliseum around fighters—tall tiers, deep perspective, layered arches, monumental "
    "scale; not dark generic hall or shallow room."
)

ARENA_PRIORITY_SAFETY_BLOCK: Final[str] = (
    "[ARENA PRIORITY SAFETY v1] Arena opulence is background support only. It must not override or weaken approved "
    "planet-cat identity, material fidelity, face morphology, costume detail, or premium character rendering."
)

CLEAN_REFS_ARENA_OPULENCE_PROMPT_BLOCKS: Final[tuple[str, ...]] = (
    ARENA_OPULENCE_HARDLOCK_BLOCK,
    ARENA_LIGHTING_RICHNESS_BLOCK,
    ARENA_SCALE_DOMINANCE_BLOCK,
    ARENA_PRIORITY_SAFETY_BLOCK,
)

CLEAN_REFS_ARENA_OPULENCE_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "dark muddy arena",
    "plain empty hall",
    "weak coliseum architecture",
    "flat circular room",
    "underlit arena",
    "cheap fantasy hall",
    "dull stone arena",
    "no golden richness",
    "missing statues",
    "missing layered balconies",
    "poor arena depth",
    "generic background",
)

__all__ = [
    "ARENA_LIGHTING_RICHNESS_BLOCK",
    "ARENA_LIGHTING_RICHNESS_MARKER",
    "ARENA_OPULENCE_HARDLOCK_BLOCK",
    "ARENA_OPULENCE_HARDLOCK_MARKER",
    "ARENA_PRIORITY_SAFETY_BLOCK",
    "ARENA_PRIORITY_SAFETY_MARKER",
    "ARENA_SCALE_DOMINANCE_BLOCK",
    "ARENA_SCALE_DOMINANCE_MARKER",
    "CLEAN_REFS_ARENA_OPULENCE_NEGATIVE_EXTRAS",
    "CLEAN_REFS_ARENA_OPULENCE_PROMPT_BLOCKS",
]
