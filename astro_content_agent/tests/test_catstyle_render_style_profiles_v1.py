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
    assert "premium_comic_poster_v2" in RENDER_STYLE_PROFILES
    assert "premium_cg_keyart_v1" in RENDER_STYLE_PROFILES
    assert "clean_cartoon_action_v1" in RENDER_STYLE_PROFILES
    assert len(RENDER_STYLE_PROFILES) >= 4


def test_default_key_constant() -> None:
    assert DEFAULT_RENDER_STYLE_PROFILE_KEY == "premium_comic_poster_v2"


def test_lookup_and_list() -> None:
    p = get_render_style_profile("premium_comic_poster_v1")
    assert p.key == "premium_comic_poster_v1"
    keys = {x.key for x in list_render_style_profiles()}
    assert keys == set(RENDER_STYLE_PROFILES)


def test_normalize_hyphens() -> None:
    assert normalize_render_style_profile_key("premium-comic-poster-v1") == "premium_comic_poster_v1"
    assert normalize_render_style_profile_key("premium-comic-poster-v2") == "premium_comic_poster_v2"
    assert normalize_render_style_profile_key("premium-cg-keyart-v1") == "premium_cg_keyart_v1"


def test_v2_has_hardlock_and_stronger_opening() -> None:
    v2 = get_render_style_profile("premium_comic_poster_v2")
    assert v2.style_hardlock_block and "nursery" in v2.style_hardlock_block.lower()
    assert "poster-grade comic splash illustration" in v2.image_prompt_opening_line.lower()
    assert "high-drama heroic" in v2.image_prompt_opening_line.lower()
    assert "not photoreal" in v2.image_prompt_opening_line.lower()
    assert "not 3d cgi" in v2.image_prompt_opening_line.lower()
    assert "no dense microtexture layering" in v2.style_hardlock_block.lower()


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


def test_image_prompt_opening_line_nonempty_per_profile() -> None:
    for prof in list_render_style_profiles():
        assert prof.image_prompt_opening_line.strip()


def test_premium_cg_keyart_profile_cg_language_and_anti_painterly_negatives() -> None:
    cg = get_render_style_profile("premium_cg_keyart_v1")
    open_low = cg.image_prompt_opening_line.lower()
    assert open_low.startswith("premium cg key art")
    assert "2.5d" in open_low or "3d-hybrid" in open_low
    assert "game key-art" in open_low or "game key art" in open_low.replace("-", " ")
    assert "crisp silhouette" in open_low
    assert "clean" in open_low and "edge" in open_low
    assert "material separation" in open_low
    assert "high-contrast" in open_low
    assert "volumetric" in open_low
    assert "cinematic depth" in open_low
    assert "not watercolor" in open_low
    hard = cg.style_hardlock_block.lower()
    assert cg.style_hardlock_block
    assert "gouache" in hard
    assert "watercolor" in hard
    assert "storybook" in hard
    neg_joined = " ".join(cg.negative_prompt_additions).lower()
    assert "watercolor" in neg_joined
    assert "gouache" in neg_joined
    assert "storybook" in neg_joined
    assert "sketchbook" in neg_joined
    assert "fuzzy brush" in neg_joined
    assert "flat comic doodle" in neg_joined
    block = format_render_style_prompt_block(cg).lower()
    assert "premium cg key" in block
    assert "material separation" in block


def test_v2_profile_unchanged_rejects_cgi_in_opening() -> None:
    v2 = get_render_style_profile("premium_comic_poster_v2")
    assert "not 3d cgi" in v2.image_prompt_opening_line.lower()
    assert "hand-painted stylized 2d" in v2.image_prompt_opening_line.lower()
