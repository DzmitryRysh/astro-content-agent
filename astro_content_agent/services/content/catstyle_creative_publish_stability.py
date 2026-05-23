"""Creative publish stability gate for Catstyle daily auto-publish (no Instagram API changes)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    has_exact_approved_reference: bool = False
    has_archetype_reference: bool = False
    has_approved_reference: bool = False  # backward-compat alias for exact tier
    has_stable_visual_canon: bool = False
    force_publish_unstable: bool = False
    reference_tier: str = "none"


def is_stable_pair_visual_canon(planet_a: str, planet_b: str, aspect_type: str, mode: str) -> bool:
    """Pair-specific visual canon rows marked stable for auto-publish."""
    return is_mars_pluto_square_tension_creative_publish_stable(planet_a, planet_b, aspect_type, mode)


def _tier_from_meta(style_reference_meta: dict[str, Any] | None) -> str:
    if not style_reference_meta:
        return "none"
    return str(style_reference_meta.get("reference_tier") or "none").strip().lower()


def evaluate_creative_publish_stability(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    *,
    force_publish_unstable: bool = False,
    allow_archetype_publish: bool = False,
    style_reference_meta: dict[str, Any] | None = None,
) -> CreativePublishStabilityResult:
    """
    Auto-publish rules (v2 reference tiers):

    - **exact** approved pair reference → publish allowed
    - **archetype** fallback → validate-only by default; publish only with ``allow_archetype_publish``
    - **none** → blocked unless ``force_publish_unstable`` or mars-pluto stable visual canon
    """
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    asp = (aspect_type or "").strip().lower()
    mo = (mode or "").strip().lower()
    tier = _tier_from_meta(style_reference_meta)

    if force_publish_unstable:
        return CreativePublishStabilityResult(
            stable=True,
            reason="force_publish_unstable override",
            force_publish_unstable=True,
            reference_tier=tier,
            has_archetype_reference=tier == "archetype",
            has_exact_approved_reference=tier == "exact",
            has_approved_reference=tier == "exact",
        )

    exact = resolve_approved_reference(pa, pb, asp, mo)
    if exact is not None or tier == "exact":
        key = (exact.registry_key if exact else None) or (
            str(style_reference_meta.get("approved_reference_registry_key") or "")
            if style_reference_meta
            else ""
        ) or "exact_from_meta"
        return CreativePublishStabilityResult(
            stable=True,
            reason=f"approved_reference:{key}",
            has_exact_approved_reference=True,
            has_approved_reference=True,
            reference_tier="exact",
        )

    if tier == "archetype" or (
        style_reference_meta and style_reference_meta.get("archetype_reference_used")
    ):
        if allow_archetype_publish:
            ak = str(style_reference_meta.get("archetype_key") or "archetype") if style_reference_meta else "archetype"
            return CreativePublishStabilityResult(
                stable=True,
                reason=f"archetype_reference:{ak}",
                has_archetype_reference=True,
                reference_tier="archetype",
            )
        return CreativePublishStabilityResult(
            stable=False,
            reason="archetype_reference_validate_only",
            has_archetype_reference=True,
            reference_tier="archetype",
        )

    if is_stable_pair_visual_canon(pa, pb, asp, mo):
        return CreativePublishStabilityResult(
            stable=True,
            reason="stable_visual_canon",
            has_stable_visual_canon=True,
            reference_tier=tier,
        )

    return CreativePublishStabilityResult(
        stable=False,
        reason="no_approved_reference_or_stable_canon",
        reference_tier=tier,
    )


CREATIVE_PUBLISH_BLOCKED_MESSAGE = (
    "Manual review required: this pair/aspect/mode has no exact approved reference and no stable visual canon. "
    "Use --validate-only to check publish prerequisites, --reference-candidates to generate review images, "
    "or --force-publish-unstable to override (logged)."
)

CREATIVE_PUBLISH_BLOCKED_ARCHETYPE_MESSAGE = (
    "Publish blocked: only an archetype fallback reference is available (not an exact pair reference). "
    "Use --validate-only to verify prerequisites, approve an exact reference, or pass --allow-archetype-publish."
)


__all__ = [
    "CREATIVE_PUBLISH_BLOCKED_ARCHETYPE_MESSAGE",
    "CREATIVE_PUBLISH_BLOCKED_MESSAGE",
    "CreativePublishStabilityResult",
    "evaluate_creative_publish_stability",
    "is_stable_pair_visual_canon",
]
