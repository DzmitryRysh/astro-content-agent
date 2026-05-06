"""Tests for Catstyle post package builder (manifest → local IG-ready bundle)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_post_package import (
    POST_PACKAGE_VERSION,
    build_catstyle_post_package,
    write_catstyle_post_package,
)


def _write_manifest(tmp_path: Path, data: dict) -> Path:
    mp = tmp_path / "image_generation_jobs.json"
    mp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return mp


def test_package_json_fields_and_jupiter_mars_russian(tmp_path: Path) -> None:
    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-05-02",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Jupiter",
            "planet_b": "Mars",
            "aspect_type": "square",
            "mode_recommendation": "tension",
            "total_score": 38,
        },
        "jobs": [
            {
                "job_id": "catstyle-2026-05-02-001",
                "date": "2026-05-02",
                "planet_a": "Jupiter",
                "planet_b": "Mars",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "shot_role": "hero_poster",
                "style_reference_image_path": "references/cat_ref.png",
                "world_template_key": "cosmic_zodiac_arena",
                "scene_template_key": "mars_kick",
                "render_style_profile_key": "premium_comic_poster_v2",
                "suggested_output_name": "catstyle_2026-05-02_001_jupiter_mars_square_tension.png",
                "status": "pending",
            },
            {
                "job_id": "catstyle-2026-05-02-002",
                "date": "2026-05-02",
                "planet_a": "Jupiter",
                "planet_b": "Mars",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 2,
                "variant_index": 0,
                "shot_role": "alternate_action_angle",
                "style_reference_image_path": "references/cat_ref.png",
                "world_template_key": "cosmic_zodiac_arena",
                "scene_template_key": "mars_kick",
                "render_style_profile_key": "premium_comic_poster_v2",
                "suggested_output_name": "catstyle_2026-05-02_002_jupiter_mars_square_tension.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    gen = tmp_path / "gen"
    gen.mkdir()
    p1 = gen / "catstyle_2026-05-02_001_jupiter_mars_square_tension.png"
    p2 = gen / "catstyle_2026-05-02_002_jupiter_mars_square_tension.png"
    p1.write_bytes(b"\x89PNG\r\n\x1a\n")
    p2.write_bytes(b"\x89PNG\r\n\x1a\n")

    pkg = build_catstyle_post_package(mp, generated_images_dir=gen)

    assert pkg.version == POST_PACKAGE_VERSION
    assert pkg.date == "2026-05-02"
    assert pkg.editorial_profile == "charged"
    assert pkg.aspect_summary and "Jupiter" in pkg.aspect_summary and "Mars" in pkg.aspect_summary
    assert pkg.world_template == "cosmic_zodiac_arena"
    assert pkg.scene_template == "mars_kick"
    assert pkg.render_style_profile == "premium_comic_poster_v2"
    assert pkg.shot_mode == "hero_pair"
    assert pkg.style_reference_image_path == "references/cat_ref.png"
    assert len(pkg.image_jobs_summary) == 2
    assert len(pkg.generated_image_paths) == 2
    assert pkg.recommended_primary_image == str(p1.resolve())
    assert pkg.hook.strip()
    assert pkg.caption.strip()
    assert pkg.carousel_slide_text.strip()
    assert pkg.compensation.strip()
    assert pkg.checklist.strip()
    assert "Юпитер" in pkg.hook or "Юпитер" in pkg.caption
    assert pkg.source_manifest_path == str(mp.resolve())


def test_generic_pack_when_not_jupiter_mars_square(tmp_path: Path) -> None:
    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-01-01",
        "editorial_profile": "balanced",
        "selected_candidate": {"planet_a": "Venus", "planet_b": "Neptune", "aspect_type": "trine", "total_score": 40},
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Venus",
                "planet_b": "Neptune",
                "aspect_type": "trine",
                "editorial_profile": "balanced",
                "mode": "flow",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "out.png",
                "status": "pending",
            }
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    assert pkg.shot_mode == "standard"
    assert "Catstyle" in pkg.caption or "Аспект" in pkg.hook
    assert pkg.style_reference_image_path is None


def test_generated_paths_empty_when_dir_missing(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-01-02",
        "editorial_profile": "charged",
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "A",
                "planet_b": "B",
                "aspect_type": "sq",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "missing.png",
                "status": "pending",
            }
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp, generated_images_dir=tmp_path / "nope")
    assert pkg.generated_image_paths == []
    assert pkg.recommended_primary_image is None


def test_write_package_creates_all_files(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-03-03",
        "editorial_profile": "charged",
        "jobs": [],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    out = tmp_path / "pkg"
    names = write_catstyle_post_package(pkg, out, overwrite=False)
    assert set(names) == {
        "post_package.json",
        "post_package.md",
        "caption.txt",
        "hook.txt",
        "compensation.txt",
        "checklist.txt",
    }
    raw = json.loads((out / "post_package.json").read_text(encoding="utf-8"))
    assert raw["version"] == POST_PACKAGE_VERSION
    assert (out / "hook.txt").read_text(encoding="utf-8").strip()
    assert (out / "post_package.md").read_text(encoding="utf-8").startswith("# Catstyle post package")


def test_write_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    manifest = {"date": "2026-03-03", "editorial_profile": "charged", "jobs": []}
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    out = tmp_path / "pkg"
    write_catstyle_post_package(pkg, out, overwrite=False)
    with pytest.raises(FileExistsError):
        write_catstyle_post_package(pkg, out, overwrite=False)
