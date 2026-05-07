"""Tests for Catstyle post package quality gate."""
from __future__ import annotations

import json
from pathlib import Path

from astro_content_agent.services.content.catstyle_post_package_quality import (
    check_catstyle_post_package,
)


def _write_package(
    tmp_path: Path,
    *,
    hook: str = "Юпитер и Марс — тест.",
    caption: str = "Подпись с кириллицей.",
    compensation: str = "Компенсация: один шаг.",
    checklist: str = "Чеклист: ☐ пункт.",
    carousel: str = "Слайды карусели.",
    shot_mode: str = "hero_pair",
    paths: list[str] | None = None,
    primary: str | None = None,
    primary_missing: bool = False,
    jobs_summary: list[dict] | None = None,
    style_ref: str | None = None,
) -> Path:
    img_dir = tmp_path / "out_imgs"
    img_dir.mkdir()
    p_a = img_dir / "hero.png"
    p_b = img_dir / "alt.png"
    p_a.write_bytes(b"\x89PNG\r\n\x1a\n")
    p_b.write_bytes(b"\x89PNG\r\n\x1a\n")

    if paths is None:
        paths_list = [str(p_a.resolve()), str(p_b.resolve())]
    else:
        paths_list = paths

    if primary_missing:
        prim = str((tmp_path / "nosuch.png").resolve())
    elif primary is not None:
        prim = primary
    elif paths_list:
        prim = paths_list[0]
    else:
        prim = str(p_a.resolve())

    if jobs_summary is None:
        jobs_summary = [
            {
                "job_id": "j1",
                "planet_a": "Jupiter",
                "planet_b": "Mars",
                "aspect_type": "square",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "hero.png",
                "shot_role": "hero_poster",
                "status": "generated",
                "mode": "tension",
            },
            {
                "job_id": "j2",
                "planet_a": "Jupiter",
                "planet_b": "Mars",
                "aspect_type": "square",
                "prompt_index": 2,
                "variant_index": 0,
                "suggested_output_name": "alt.png",
                "shot_role": "alternate_action_angle",
                "status": "generated",
                "mode": "tension",
            },
        ]

    pkg = {
        "version": "catstyle-post-package-v1",
        "date": "2026-06-01",
        "editorial_profile": "charged",
        "aspect_summary": "Jupiter square Mars",
        "hook": hook,
        "caption": caption,
        "compensation": compensation,
        "checklist": checklist,
        "carousel_slide_text": carousel,
        "shot_mode": shot_mode,
        "style_reference_image_path": style_ref,
        "image_jobs_summary": jobs_summary,
        "generated_image_paths": paths_list,
        "recommended_primary_image": prim,
        "source_manifest_path": str(tmp_path / "manifest.json"),
        "world_template": "wt",
        "scene_template": "st",
        "render_style_profile": "rs",
    }
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "post_package.json").write_text(
        json.dumps(pkg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return pkg_dir


def test_ready_package_full_score(tmp_path: Path) -> None:
    pkg_dir = _write_package(tmp_path, style_ref="references/ref.png")
    r = check_catstyle_post_package(pkg_dir)
    assert r.status == "ready"
    assert r.score >= 85
    assert not r.errors
    assert r.recommended_primary_image
    assert any("no common mojibake" in p.lower() for p in r.passed_checks)
    assert any("Cyrillic" in p for p in r.passed_checks)


def test_missing_primary_image_file_needs_attention(tmp_path: Path) -> None:
    pkg_dir = _write_package(tmp_path, primary_missing=True)
    r = check_catstyle_post_package(pkg_dir)
    assert r.status == "needs_attention"
    assert r.errors
    assert any("does not exist" in e for e in r.errors)


def test_mojibake_triggers_error(tmp_path: Path) -> None:
    pkg_dir = _write_package(tmp_path, hook="Ð¤ÐµÐ¹Ðº UTF-8 breakage")
    r = check_catstyle_post_package(pkg_dir)
    assert r.status == "needs_attention"
    assert any("mojibake" in e.lower() for e in r.errors)


def test_hero_pair_single_image_warning(tmp_path: Path) -> None:
    img_dir = tmp_path / "imgs"
    img_dir.mkdir()
    only = img_dir / "one.png"
    only.write_bytes(b"\x89PNG\r\n\x1a\n")
    pkg_dir = _write_package(tmp_path, paths=[str(only.resolve())], shot_mode="hero_pair")
    r = check_catstyle_post_package(pkg_dir)
    assert any("hero_pair" in w and "2" in w for w in r.warnings)
    assert r.status == "ready"
    assert not r.errors


def test_missing_generated_paths_array_error(tmp_path: Path) -> None:
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    img_dir = tmp_path / "imgs"
    img_dir.mkdir()
    one = img_dir / "a.png"
    one.write_bytes(b"x")
    pkg = {
        "date": "2026-01-01",
        "hook": "Ю",
        "caption": "Ю",
        "compensation": "Ю",
        "checklist": "Ю",
        "carousel_slide_text": "Ю",
        "generated_image_paths": [],
        "recommended_primary_image": str(one.resolve()),
        "image_jobs_summary": [
            {"planet_a": "A", "planet_b": "B", "aspect_type": "sq", "job_id": "x"}
        ],
    }
    (pkg_dir / "post_package.json").write_text(json.dumps(pkg, ensure_ascii=False), encoding="utf-8")
    r = check_catstyle_post_package(pkg_dir)
    assert r.status == "needs_attention"
    assert any("at least one" in e for e in r.errors)


def test_planet_aspect_warning_on_bad_jobs(tmp_path: Path) -> None:
    pkg_dir = _write_package(tmp_path, jobs_summary=[{"job_id": "x"}])
    r = check_catstyle_post_package(pkg_dir)
    assert any("Planet/aspect" in w for w in r.warnings)
