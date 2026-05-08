"""Tests for Catstyle approved reference registry v1."""
from __future__ import annotations

from astro_content_agent.content.catstyle.approved_reference_registry import (
    ApprovedReferenceEntry,
    load_approved_reference_registry,
    normalize_pair_key,
    resolve_approved_reference,
)


def test_normalize_pair_key_order_insensitive() -> None:
    assert normalize_pair_key("Moon", "Saturn", "square", "tension") == normalize_pair_key(
        "Saturn", "Moon", "square", "tension"
    )
    assert normalize_pair_key("mars", "pluto", "square", "tension") == normalize_pair_key(
        "Pluto", "Mars", "SQUARE", "TENSION"
    )


def test_resolve_moon_saturn_square_tension() -> None:
    r = resolve_approved_reference("Moon", "Saturn", "square", "tension")
    assert r is not None
    assert r.registry_key == "moon_saturn_square_tension_v1"
    assert "catstyle_moon_saturn_square_tension_approved" in r.image_path.replace("\\", "/").lower()


def test_resolve_reversed_planets_same() -> None:
    a = resolve_approved_reference("Saturn", "Moon", "square", "tension")
    b = resolve_approved_reference("Moon", "Saturn", "square", "tension")
    assert a is not None and b is not None
    assert a.registry_key == b.registry_key
    assert a.image_path == b.image_path


def test_resolve_missing_returns_none() -> None:
    assert resolve_approved_reference("Sun", "Neptune", "trine", "tension") is None


def test_inactive_entry_ignored() -> None:
    reg = list(load_approved_reference_registry())
    dup = ApprovedReferenceEntry(
        registry_key="moon_saturn_square_tension_shadow",
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        image_path="references/should_not_pick.png",
        priority=999,
        active=False,
    )
    r = resolve_approved_reference("Moon", "Saturn", "square", "tension", registry=reg + [dup])
    assert r is not None
    assert r.registry_key == "moon_saturn_square_tension_v1"


def test_tie_break_higher_priority_wins() -> None:
    hi = ApprovedReferenceEntry(
        registry_key="zz_low_key_high_priority",
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        image_path="references/catstyle_moon_saturn_approved.png",
        priority=200,
        active=True,
    )
    lo = ApprovedReferenceEntry(
        registry_key="aa_high_key_low_priority",
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        image_path="references/catstyle_pluto_mars_approved.png",
        priority=50,
        active=True,
    )
    r = resolve_approved_reference("Moon", "Saturn", "square", "tension", registry=[lo, hi])
    assert r is not None
    assert r.registry_key == "zz_low_key_high_priority"


def test_tie_break_registry_key_when_priority_equal() -> None:
    a = ApprovedReferenceEntry(
        registry_key="z_second",
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        image_path="references/catstyle_moon_saturn_approved.png",
        priority=10,
        active=True,
    )
    b = ApprovedReferenceEntry(
        registry_key="m_first",
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        image_path="references/catstyle_pluto_mars_approved.png",
        priority=10,
        active=True,
    )
    r = resolve_approved_reference("Moon", "Saturn", "square", "tension", registry=[a, b])
    assert r is not None
    assert r.registry_key == "m_first"
