"""Tests for Catstyle render style profiles v1."""
from __future__ import annotations

import pytest

from astro_content_agent.content.catstyle.render_style_profiles_v1 import (
    DEFAULT_RENDER_STYLE_PROFILE_KEY,
    RENDER_STYLE_PROFILES,
    format_render_style_prompt_block,
    get_render_style_profile,
    list_render_style_profiles,
    normalize_render_style_profile_key,
)


def test_registry_contains_required_profiles() -> None:
    assert "premium_comic_poster_v1" in RENDER_STYLE_PROFILES
    assert "clean_cartoon_action_v1" in RENDER_STYLE_PROFILES
    assert len(RENDER_STYLE_PROFILES) >= 2


def test_default_key_constant() -> None:
    assert DEFAULT_RENDER_STYLE_PROFILE_KEY == "premium_comic_poster_v1"


def test_lookup_and_list() -> None:
    p = get_render_style_profile("premium_comic_poster_v1")
    assert p.key == "premium_comic_poster_v1"
    keys = {x.key for x in list_render_style_profiles()}
    assert keys == set(RENDER_STYLE_PROFILES)


def test_normalize_hyphens() -> None:
    assert normalize_render_style_profile_key("premium-comic-poster-v1") == "premium_comic_poster_v1"


def test_unknown_profile_raises() -> None:
    with pytest.raises(ValueError, match="Unknown Catstyle render style profile.*Known keys"):
        normalize_render_style_profile_key("not_a_profile")


def test_format_block_has_banner_and_lines() -> None:
    prof = get_render_style_profile("premium_comic_poster_v1")
    block = format_render_style_prompt_block(prof)
    assert "[RENDER STYLE v1 - high-priority visual finish]" in block
    assert "Composition:" in block and "Linework:" in block
    assert "Must have:" in block and "Avoid:" in block


def test_negative_additions_nonempty() -> None:
    for prof in list_render_style_profiles():
        assert prof.negative_prompt_additions
        for item in prof.negative_prompt_additions:
            assert item.strip()
