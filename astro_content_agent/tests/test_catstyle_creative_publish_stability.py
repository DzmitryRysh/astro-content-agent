"""Creative publish stability gate (approved reference, stable canon, force override)."""
from __future__ import annotations

from astro_content_agent.services.content.catstyle_creative_publish_stability import (
    evaluate_creative_publish_stability,
)


def test_mercury_jupiter_flow_stable_via_approved_reference() -> None:
    r = evaluate_creative_publish_stability("Mercury", "Jupiter", "sextile", "flow")
    assert r.stable
    assert r.has_approved_reference
    assert "mercury_jupiter" in r.reason


def test_mars_pluto_square_tension_stable_via_visual_canon(monkeypatch) -> None:
    monkeypatch.setattr(
        "astro_content_agent.services.content.catstyle_creative_publish_stability.resolve_approved_reference",
        lambda *a, **k: None,
    )
    r = evaluate_creative_publish_stability("Mars", "Pluto", "square", "tension")
    assert r.stable
    assert r.has_stable_visual_canon
    assert r.reason == "stable_visual_canon"


def test_jupiter_moon_unstable_without_override() -> None:
    r = evaluate_creative_publish_stability("Jupiter", "Moon", "square", "tension")
    assert not r.stable
    assert r.reason == "no_approved_reference_or_stable_canon"


def test_force_publish_unstable_allows() -> None:
    r = evaluate_creative_publish_stability(
        "Jupiter", "Moon", "square", "tension", force_publish_unstable=True
    )
    assert r.stable
    assert r.force_publish_unstable
