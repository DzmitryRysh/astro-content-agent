"""Tests for optional Catstyle glyph overlay tooling and in-scene flag glyph prompts."""
from __future__ import annotations

import filecmp
from pathlib import Path

import pytest
from PIL import Image

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_symbol_overlay import (
    PLANET_GLYPHS,
    SYMBOLS_FIXED_STEM_TAG,
    apply_dual_flag_symbol_overlay,
    apply_symbol_overlay,
    assert_publication_uses_symbols_fixed,
    default_overlay_output_path,
    default_symbols_fixed_output_path,
    glyph_for_planet,
    is_symbols_fixed_path,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_canonical_glyph_mapping_core_planets() -> None:
    assert PLANET_GLYPHS["mercury"] == "\u263f"  # ☿
    assert PLANET_GLYPHS["jupiter"] == "\u2643"  # ♃
    assert PLANET_GLYPHS["mars"] == "\u2642"  # ♂
    assert PLANET_GLYPHS["saturn"] == "\u2644"  # ♄
    assert PLANET_GLYPHS["venus"] == "\u2640"  # ♀
    assert PLANET_GLYPHS["moon"] == "\u263d"  # ☽
    assert PLANET_GLYPHS["pluto"] == "\u2647"  # ♇
    assert PLANET_GLYPHS["sun"] == "\u2609"  # ☉
    assert PLANET_GLYPHS["uranus"] == "\u2645"  # ♅
    assert PLANET_GLYPHS["neptune"] == "\u2646"  # ♆


def test_glyph_for_planet_case_insensitive() -> None:
    assert glyph_for_planet("Mercury") == "\u263f"
    assert glyph_for_planet("jupiter") == "\u2643"


def test_apply_symbol_overlay_writes_new_file_preserves_original(tmp_path: Path) -> None:
    src = tmp_path / "src.png"
    Image.new("RGB", (200, 200), color=(40, 60, 90)).save(src)
    before = src.read_bytes()
    out = tmp_path / "out_overlay.png"
    apply_symbol_overlay(
        src,
        out,
        glyph="\u2643",
        x_norm=0.5,
        y_norm=0.5,
        size_px=40,
        premium_glow=False,
    )
    assert out.is_file()
    assert src.read_bytes() == before
    assert not filecmp.cmp(src, out, shallow=False)


def test_default_overlay_output_path_suffix() -> None:
    p = Path("/tmp/x/catstyle_2026-05-09_001_mercury_jupiter_sextile_flow.png")
    assert default_overlay_output_path(p).name == "catstyle_2026-05-09_001_mercury_jupiter_sextile_flow_overlay.png"


def test_default_symbols_fixed_output_path_suffix() -> None:
    p = Path("/tmp/x/catstyle_2026-05-09_001_mercury_jupiter_sextile_flow.png")
    assert default_symbols_fixed_output_path(p).name == (
        "catstyle_2026-05-09_001_mercury_jupiter_sextile_flow_symbols_fixed.png"
    )


def test_dual_flag_overlay_creates_symbols_fixed_preserves_source(tmp_path: Path) -> None:
    src = tmp_path / "catstyle_2026-05-09_001_mercury_jupiter_sextile_flow.png"
    Image.new("RGB", (400, 400), color=(20, 20, 40)).save(src)
    before = src.read_bytes()
    out = default_symbols_fixed_output_path(src)
    apply_dual_flag_symbol_overlay(
        src,
        out,
        planet_a="mercury",
        planet_b="jupiter",
        layout_preset="poster_ab",
        size_px=48,
    )
    assert out.is_file()
    assert is_symbols_fixed_path(out)
    assert src.read_bytes() == before
    assert out.name.endswith("_symbols_fixed.png")


def test_mars_saturn_dual_overlay_uses_correct_glyphs(tmp_path: Path) -> None:
    src = tmp_path / "pair.png"
    Image.new("RGB", (300, 300), color=(10, 10, 10)).save(src)
    out = tmp_path / "pair_symbols_fixed.png"
    apply_dual_flag_symbol_overlay(src, out, planet_a="mars", planet_b="saturn", size_px=36)
    assert out.is_file()


def test_assert_publication_uses_symbols_fixed_accepts_and_rejects(tmp_path: Path) -> None:
    ok = tmp_path / "hero_symbols_fixed.png"
    Image.new("RGB", (10, 10), (0, 0, 0)).save(ok)
    assert_publication_uses_symbols_fixed(ok)

    bad = tmp_path / "hero_raw.png"
    Image.new("RGB", (10, 10), (0, 0, 0)).save(bad)
    with pytest.raises(ValueError, match="symbols_fixed"):
        assert_publication_uses_symbols_fixed(bad)


def test_mercury_jupiter_flow_prompt_integrated_flag_glyph_language() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mercury",
            planet_b="Jupiter",
            aspect_type="sextile",
            mode="flow",
            premium_art_direction=True,
        )
    )
    blob = " ".join(pack.image_prompts)
    lower = blob.lower()
    assert "symbol overlay v1" not in lower
    assert "post-overlay" not in lower and "composited after" not in lower
    assert "catstyle pair flag glyph system v1" in lower
    assert "flag glyphs:" in lower and "pair flag glyph system v1" in lower
    assert "heraldic gold" in lower or "embroidered-thread emblem" in lower
    assert "mercury–jupiter flow cast v1" in lower or "mercury-jupiter flow cast v1" in lower.replace("–", "-")
    assert "jupiter" in lower and "mercury" in lower
    assert "left/port faction banner" in lower
    assert "right/starboard faction banner" in lower
    assert "[jupiter ♃ hardening]" in lower
    assert "[mercury ☿ hardening]" in lower
    assert "floating" in lower
    assert "\u2643" in blob or "♃" in blob
    assert "\u263f" in blob or "☿" in blob


def test_negative_prompt_excludes_sticker_float_and_malformed_glyphs() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mercury",
            planet_b="Jupiter",
            aspect_type="sextile",
            mode="flow",
            premium_art_direction=True,
        )
    )
    neg = (pack.negative_prompt or "").lower()
    assert "malformed" in neg or "pseudo" in neg or "glyph" in neg
    assert "floating" in neg and "sticker" in neg


def test_generic_post_package_checklist_does_not_require_symbols_fixed(tmp_path: Path) -> None:
    from astro_content_agent.services.content.catstyle_post_package import build_catstyle_post_package

    manifest = {
        "date": "2026-11-01",
        "editorial_profile": "balanced",
        "selected_candidate": {
            "planet_a": "Sun",
            "planet_b": "Venus",
            "aspect_type": "trine",
            "mode_recommendation": "flow",
            "total_score": 5,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Sun",
                "planet_b": "Venus",
                "aspect_type": "trine",
                "editorial_profile": "balanced",
                "mode": "flow",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "sv.png",
                "status": "pending",
            },
        ],
    }
    mp = tmp_path / "manifest.json"
    mp.write_text(__import__("json").dumps(manifest), encoding="utf-8")
    pkg = build_catstyle_post_package(mp)
    cl = pkg.checklist.lower()
    assert "нарисованы в ткани" in cl or "флагах" in cl
    assert "symbols_fixed" not in cl
    assert SYMBOLS_FIXED_STEM_TAG not in cl
