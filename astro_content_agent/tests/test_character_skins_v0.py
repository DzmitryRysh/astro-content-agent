"""Tests for Catstyle character skins v0 (Mars, Jupiter, Saturn)."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.character_skins_v0 import (
    CharacterSkin,
    get_character_skin,
    list_character_skins,
    normalize_skin_key,
)


def test_normalize_skin_key_hyphen_to_underscore() -> None:
    assert normalize_skin_key("Spartan-King") == "spartan_king"


def test_list_character_skins_mars() -> None:
    keys = list_character_skins("mars")
    assert keys == ["gladiator", "rambo", "spartan_king"]


def test_get_character_skin_mars_spartan_success() -> None:
    sk = get_character_skin("Mars", "spartan_king")
    assert isinstance(sk, CharacterSkin)
    assert sk.planet_name == "Mars"
    assert sk.display_name == "Spartan King"
    assert "shield" in sk.prop_elements.lower()


def test_get_character_skin_unknown_raises() -> None:
    with pytest.raises(ValueError, match="No character skin"):
        get_character_skin("Mars", "not_a_real_skin")


def test_get_character_skin_wrong_planet_raises() -> None:
    with pytest.raises(ValueError, match="No character skin .*philosopher"):
        get_character_skin("Mars", "philosopher_mentor")


def test_list_character_skins_invalid_planet_raises() -> None:
    with pytest.raises(ValueError, match="only support"):
        list_character_skins("Venus")
