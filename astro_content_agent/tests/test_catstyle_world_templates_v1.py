"""Tests for Catstyle world templates v1."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.world_templates_v1 import (
    DEFAULT_WORLD_TEMPLATE_KEY,
    get_world_template,
    list_world_templates,
    normalize_world_template_key,
)


def test_cosmic_zodiac_arena_exists() -> None:
    wt = get_world_template(DEFAULT_WORLD_TEMPLATE_KEY)
    assert wt.template_key == "cosmic_zodiac_arena"
    assert "disc" in wt.setting_line.lower() or "arena" in wt.setting_line.lower()


def test_lookup_and_list() -> None:
    keys = {x.template_key for x in list_world_templates()}
    assert "cosmic_zodiac_arena" in keys
    assert get_world_template("cosmic_zodiac_arena").display_name


def test_normalize_accepts_hyphens_and_case() -> None:
    assert normalize_world_template_key("Cosmic-Zodiac-Arena") == "cosmic_zodiac_arena"


def test_unknown_world_template_raises_clearly() -> None:
    with pytest.raises(ValueError, match="Unknown Catstyle world template.*Known keys"):
        normalize_world_template_key("not_a_world")
