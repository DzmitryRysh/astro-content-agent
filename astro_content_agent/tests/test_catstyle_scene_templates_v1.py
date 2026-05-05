"""Tests for Catstyle scene templates v1."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.scene_templates_v1 import (
    SCENE_TEMPLATES,
    find_scene_templates_for_context,
    get_scene_template,
    list_scene_templates,
    normalize_scene_template_key,
    validate_explicit_scene_template,
)


def test_expected_registry_size() -> None:
    assert len(SCENE_TEMPLATES) == 15


def test_lookup_and_list() -> None:
    assert get_scene_template("mars_spartan_cliff_kick").energy == "charged"
    keys = {x.template_key for x in list_scene_templates()}
    assert keys == set(SCENE_TEMPLATES)


def test_unknown_scene_template_raises_clearly() -> None:
    with pytest.raises(ValueError, match="Unknown Catstyle scene template.*Known keys"):
        normalize_scene_template_key("missing_scene")


def test_find_scene_templates_jupiter_mars_square_spartan_surfaces_cliff_kick() -> None:
    ranked = find_scene_templates_for_context(
        "Jupiter",
        "Mars",
        aspect_type="square",
        skin_b="spartan_king",
        editorial_profile="charged",
    )
    assert ranked and ranked[0].template_key == "mars_spartan_cliff_kick"


def test_find_scene_templates_uranus_venus_square_surfaces_expected() -> None:
    ranked = find_scene_templates_for_context(
        "Uranus",
        "Venus",
        aspect_type="square",
        editorial_profile="charged",
    )
    keys_in_order = [t.template_key for t in ranked[:5]]
    assert "uranus_electric_wind_burst" in keys_in_order
    assert "venus_marilyn_wind_grate" in keys_in_order


def test_find_scene_templates_pluto_mars_square_surfaces_tricycle() -> None:
    ranked = find_scene_templates_for_context(
        "Pluto",
        "Mars",
        aspect_type="square",
        editorial_profile="charged",
    )
    assert ranked and ranked[0].template_key == "pluto_tricycle_showdown"


def test_find_scene_templates_stable_ordering_deterministic() -> None:
    a = find_scene_templates_for_context("Uranus", "Venus", aspect_type="square", editorial_profile="charged")
    b = find_scene_templates_for_context("Uranus", "Venus", aspect_type="square", editorial_profile="charged")
    assert [t.template_key for t in a] == [t.template_key for t in b]


def test_validate_explicit_scene_incompatible_raises() -> None:
    with pytest.raises(ValueError, match="incompatible"):
        validate_explicit_scene_template(
            "venus_marilyn_wind_grate",
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
        )
