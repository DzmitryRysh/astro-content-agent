"""Banner glyph reference assist — prompts, banner-only discipline, Sun/Uranus roles."""
from __future__ import annotations

from pathlib import Path

from astro_content_agent.content.catstyle.banner_glyph_reference_v1 import (
    BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK,
    build_banner_glyph_reference_assist,
    format_banner_glyph_reference_roles_block,
    resolve_banner_glyph_reference_paths,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_banner_only_discipline_forbids_extra_glyph_locations() -> None:
    low = BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK.lower()
    assert "exactly one" in low
    assert "left/port" in low or "left" in low
    assert "right/starboard" in low or "starboard" in low
    assert "chest" in low
    assert "armor" in low
    assert "medallion" in low
    assert "accessory" in low or "accessories" in low
    assert "portal rim" in low
    assert "floating" in low


def test_reference_roles_block_image_a_b_c(tmp_path: Path) -> None:
    sun_crop = tmp_path / "sun_banner.png"
    ura_crop = tmp_path / "uranus_banner.png"
    sun_crop.write_bytes(b"\x89PNG\r\n\x1a\n")
    ura_crop.write_bytes(b"\x89PNG\r\n\x1a\n")
    block = format_banner_glyph_reference_roles_block(
        "Sun",
        "Uranus",
        style_reference_present=True,
        glyph_ref_planet_a=str(sun_crop),
        glyph_ref_planet_b=str(ura_crop),
    )
    assert "[CATSTYLE REFERENCE IMAGE ROLES v1]" in block
    assert "Image A" in block
    assert "Image B" in block
    assert "Image C" in block
    assert "left/port" in block.lower()
    assert "right/starboard" in block.lower()
    assert "\u2609" in block or "Sun" in block
    assert "\u2645" in block or "Uranus" in block
    assert "floating sticker" in block.lower()


def test_resolve_explicit_banner_glyph_paths(tmp_path: Path) -> None:
    pa = tmp_path / "mercury_glyph.png"
    pb = tmp_path / "uranus_glyph.png"
    pa.write_bytes(b"x")
    pb.write_bytes(b"x")
    a, b = resolve_banner_glyph_reference_paths(
        "Mercury",
        "Uranus",
        explicit_planet_a=str(pa),
        explicit_planet_b=str(pb),
        use_auto_discovery=False,
    )
    assert a == str(pa.resolve())
    assert b == str(pb.resolve())


def test_sun_uranus_prompt_banner_glyph_roles_and_banner_only(tmp_path: Path) -> None:
    sun_ref = tmp_path / "sun_left_banner_glyph.png"
    ura_ref = tmp_path / "uranus_right_banner_glyph.png"
    sun_ref.write_bytes(b"\x89PNG\r\n\x1a\n")
    ura_ref.write_bytes(b"\x89PNG\r\n\x1a\n")
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_comic_poster_v2",
            shot_mode="epic_arena_showdown",
            banner_glyph_reference_planet_a=str(sun_ref),
            banner_glyph_reference_planet_b=str(ura_ref),
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    joined = "\n".join(pack.image_prompts)
    assert "[CATSTYLE BANNER-ONLY GLYPH DISCIPLINE v1]" in joined
    assert "[CATSTYLE REFERENCE IMAGE ROLES v1]" in joined
    assert "Image A" in joined and "Image B" in joined
    assert "left/port" in joined.lower() and "Sun" in joined
    assert "right/starboard" in joined.lower() and "Uranus" in joined
    assert "left/port" in joined.lower()
    assert "right/starboard" in joined.lower()
    assert pack.banner_glyph_reference_assist is not None
    assert pack.banner_glyph_reference_assist["banner_glyph_reference_planet_a_path"]
    assert pack.banner_glyph_reference_assist["banner_glyph_reference_planet_b_path"]
    assert "[FLAG GLYPH FIDELITY LOCK v1]" in joined


def test_prompt_includes_pair_flag_system_without_glyph_refs() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Jupiter",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    joined = "\n".join(pack.image_prompts)
    assert "[CATSTYLE PAIR FLAG GLYPH SYSTEM v1]" in joined
    assert "[CATSTYLE BANNER-ONLY GLYPH DISCIPLINE v1]" in joined
    assert "[CATSTYLE REFERENCE IMAGE ROLES v1]" not in joined


def test_build_assist_metadata_none_without_resolved_paths() -> None:
    assist = build_banner_glyph_reference_assist(
        "Sun",
        "Uranus",
        explicit_glyph_a="/nonexistent/sun.png",
        explicit_glyph_b=None,
        use_auto_discovery=False,
    )
    assert assist is None
