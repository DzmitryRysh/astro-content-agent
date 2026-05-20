"""Creative publish stability gate for Catstyle daily auto-publish (no Instagram API changes)."""
from __future__ import annotations

from dataclasses import dataclass

from astro_content_agent.content.catstyle.approved_reference_registry import resolve_approved_reference
from astro_content_agent.content.catstyle.mars_pluto_square_tension_canon_v1 import (
    is_mars_pluto_square_tension_creative_publish_stable,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name


@dataclass(frozen=True)
class CreativePublishStabilityResult:
    """Whether real Instagram publish is allowed without explicit operator override."""

    stable: bool
    reason: str
    has_approved_reference: bool = False
    has_stable_visual_canon: bool = False
    force_publish_unstable: bool = False


def is_stable_pair_visual_canon(planet_a: str, planet_b: str, aspect_type: str, mode: str) -> bool:
    """Pair-specific visual canon rows marked stable for auto-publish."""
    return is_mars_pluto_square_tension_creative_publish_stable(planet_a, planet_b, aspect_type, mode)


def evaluate_creative_publish_stability(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    *,
    force_publish_unstable: bool = False,
) -> CreativePublishStabilityResult:
    """
    Auto-publish is allowed when an approved reference exists, a stable visual canon exists,
    or the operator passes ``force_publish_unstable``.
    """
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    asp = (aspect_type or "").strip().lower()
    mo = (mode or "").strip().lower()

    if force_publish_unstable:
        return CreativePublishStabilityResult(
            stable=True,
            reason="force_publish_unstable override",
            force_publish_unstable=True,
        )

    hit = resolve_approved_reference(pa, pb, asp, mo)
    if hit is not None:
        return CreativePublishStabilityResult(
            stable=True,
            reason=f"approved_reference:{hit.registry_key}",
            has_approved_reference=True,
        )

    if is_stable_pair_visual_canon(pa, pb, asp, mo):
        return CreativePublishStabilityResult(
            stable=True,
            reason="stable_visual_canon",
            has_stable_visual_canon=True,
        )

    return CreativePublishStabilityResult(
        stable=False,
        reason="no_approved_reference_or_stable_canon",
    )


CREATIVE_PUBLISH_BLOCKED_MESSAGE = (
    "Manual review required: this pair/aspect/mode has no approved reference and no stable visual canon. "
    "Use --validate-only to check publish prerequisites, or --force-publish-unstable to override (logged)."
)


__all__ = [
    "CREATIVE_PUBLISH_BLOCKED_MESSAGE",
    "CreativePublishStabilityResult",
    "evaluate_creative_publish_stability",
    "is_stable_pair_visual_canon",
]
