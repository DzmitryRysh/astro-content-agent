"""Tests for Catstyle post package builder (manifest → local IG-ready bundle)."""
from __future__ import annotations

import json
import re
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
    assert pkg.planet_a == "Jupiter" and pkg.planet_b == "Mars"
    assert pkg.aspect_type == "square" and pkg.mode == "tension"
    assert pkg.hook.strip()
    assert pkg.caption.strip()
    assert pkg.carousel_slide_text.strip()
    assert pkg.compensation.strip()
    assert pkg.checklist.strip()
    assert "Юпитер" in pkg.hook or "Юпитер" in pkg.caption
    assert pkg.source_manifest_path == str(mp.resolve())


def test_venus_pluto_opposition_tension_aspect_aware_copy(tmp_path: Path) -> None:
    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-08-10",
        "editorial_profile": "charged",
        "manual_aspect_override": {
            "enabled": True,
            "planet_a": "Venus",
            "planet_b": "Pluto",
            "aspect_type": "opposition",
            "mode": "tension",
        },
        "selected_candidate": {
            "planet_a": "Venus",
            "planet_b": "Pluto",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
            "total_score": 0,
            "source": "manual_override",
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Venus",
                "planet_b": "Pluto",
                "aspect_type": "opposition",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "shot_role": "hero_poster",
                "suggested_output_name": "catstyle_2026-08-10_001_venus_pluto_opposition_tension.png",
                "status": "pending",
            },
            {
                "job_id": "j2",
                "planet_a": "Venus",
                "planet_b": "Pluto",
                "aspect_type": "opposition",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 2,
                "variant_index": 0,
                "shot_role": "alternate_action_angle",
                "suggested_output_name": "catstyle_2026-08-10_002_venus_pluto_opposition_tension.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    gen = tmp_path / "gen_vp"
    gen.mkdir()
    for name in (
        "catstyle_2026-08-10_001_venus_pluto_opposition_tension.png",
        "catstyle_2026-08-10_002_venus_pluto_opposition_tension.png",
    ):
        (gen / name).write_bytes(b"\x89PNG\r\n\x1a\n")
    pkg = build_catstyle_post_package(mp, generated_images_dir=gen)
    assert "Пакет Catstyle для ручной сборки" not in pkg.caption
    assert "Венера" in pkg.hook or "Венера" in pkg.caption
    assert "Плутон" in pkg.hook or "Плутон" in pkg.caption
    assert "магнитизм" in pkg.caption.lower()
    assert "границ" in pkg.compensation.lower()


def test_mercury_jupiter_sextile_flow_caption_instagram_ready(tmp_path: Path) -> None:
    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-06-10",
        "editorial_profile": "charged",
        "sky_scan_mode": "day-window",
        "sky_scan_step_hours_utc": 2,
        "manual_aspect_override": {
            "enabled": True,
            "planet_a": "Mercury",
            "planet_b": "Jupiter",
            "aspect_type": "sextile",
            "mode": "flow",
        },
        "selected_candidate": {
            "planet_a": "Mercury",
            "planet_b": "Jupiter",
            "aspect_type": "sextile",
            "mode_recommendation": "flow",
            "total_score": 0,
            "source": "manual_override",
            "manual_override_sky_timing_match": True,
            "orb": 0.35,
            "closest_hour_utc": 8,
            "window_first_seen_hour_utc": 0,
            "window_last_seen_hour_utc": 22,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Mercury",
                "planet_b": "Jupiter",
                "aspect_type": "sextile",
                "editorial_profile": "charged",
                "mode": "flow",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "catstyle_2026-06-10_001_mercury_jupiter_sextile_flow.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    gen = tmp_path / "gen_mj"
    gen.mkdir()
    (gen / "catstyle_2026-06-10_001_mercury_jupiter_sextile_flow.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    pkg = build_catstyle_post_package(mp, generated_images_dir=gen)
    assert "Пакет Catstyle для ручной сборки" not in pkg.caption
    assert "Меркурий" in pkg.caption and "Юпитер" in pkg.caption
    assert "20 минут" in pkg.caption or "гипотез" in pkg.caption.lower()
    assert "**Про сроки:**" in pkg.caption
    assert "Окно аспекта" in pkg.caption
    assert "1–2 дня" in pkg.caption or "около 3 дней" in pkg.caption
    cap_l = pkg.caption.lower()
    assert "utc" not in cap_l
    assert "орбис" not in cap_l


def test_pluto_mars_square_tension_aspect_aware_copy(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-08-11",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Mars",
            "planet_b": "Pluto",
            "aspect_type": "square",
            "mode_recommendation": "tension",
            "total_score": 40,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Mars",
                "planet_b": "Pluto",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "pm.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    assert "Пакет Catstyle для ручной сборки" not in pkg.caption
    assert "Плутон" in pkg.hook or "Плутон" in pkg.caption
    assert "Марс" in pkg.hook or "Марс" in pkg.caption
    assert "контролируемое действие" in pkg.compensation.lower() or "контролируемое" in pkg.compensation.lower()


def test_moon_saturn_square_tension_aspect_aware_copy_and_reversed_order(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-09-01",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Saturn",
            "planet_b": "Moon",
            "aspect_type": "square",
            "mode_recommendation": "tension",
            "total_score": 10,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Saturn",
                "planet_b": "Moon",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "ms.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    assert "Пакет Catstyle для ручной сборки поста" not in pkg.caption
    assert "Луна" in pkg.hook or "Луна" in pkg.caption
    assert "Сатурн" in pkg.hook or "Сатурн" in pkg.caption
    assert "не наказывай себя" in pkg.compensation.lower() or "потребность" in pkg.compensation.lower()


def test_venus_mars_square_tension_aspect_aware_copy_and_reversed_order(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-09-02",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Mars",
            "planet_b": "Venus",
            "aspect_type": "square",
            "mode_recommendation": "tension",
            "total_score": 10,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Mars",
                "planet_b": "Venus",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "vm.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    assert "Пакет Catstyle для ручной сборки поста" not in pkg.caption
    assert "Венера" in pkg.hook or "Венера" in pkg.caption
    assert "Марс" in pkg.hook or "Марс" in pkg.caption
    assert "хими" in pkg.caption.lower() or "хаос" in pkg.compensation.lower()


def test_mercury_neptune_square_tension_aspect_aware_copy_and_reversed_order(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-09-03",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Neptune",
            "planet_b": "Mercury",
            "aspect_type": "square",
            "mode_recommendation": "tension",
            "total_score": 10,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Neptune",
                "planet_b": "Mercury",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "mn.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    assert "Пакет Catstyle для ручной сборки поста" not in pkg.caption
    assert "Меркур" in pkg.hook or "Меркур" in pkg.caption
    assert "Нептун" in pkg.hook or "Нептун" in pkg.caption
    assert "проверь факты" in pkg.compensation.lower() or "прямой вопрос" in pkg.compensation.lower()


def test_sun_uranus_square_tension_aspect_aware_copy_and_reversed_order(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-09-04",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Uranus",
            "planet_b": "Sun",
            "aspect_type": "square",
            "mode_recommendation": "tension",
            "total_score": 10,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Uranus",
                "planet_b": "Sun",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "su.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    assert "Пакет Catstyle для ручной сборки поста" not in pkg.caption
    assert "Солнце" in pkg.hook or "Солнце" in pkg.caption
    assert "Уран" in pkg.hook or "Уран" in pkg.caption
    assert "не сжигай" in pkg.compensation.lower() or "бунт" in pkg.compensation.lower()


def test_jupiter_saturn_square_tension_aspect_aware_copy_and_reversed_order(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-09-05",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Saturn",
            "planet_b": "Jupiter",
            "aspect_type": "square",
            "mode_recommendation": "tension",
            "total_score": 10,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Saturn",
                "planet_b": "Jupiter",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "js.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    assert "Пакет Catstyle для ручной сборки поста" not in pkg.caption
    assert "Юпитер" in pkg.hook or "Юпитер" in pkg.caption
    assert "Сатурн" in pkg.hook or "Сатурн" in pkg.caption
    assert "дедлайн" in pkg.compensation.lower() or "измерим" in pkg.compensation.lower()


def test_unsupported_aspect_moon_saturn_opposition_still_generic(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-09-06",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Moon",
            "planet_b": "Saturn",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
            "total_score": 10,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Moon",
                "planet_b": "Saturn",
                "aspect_type": "opposition",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "mso.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    assert "Пакет Catstyle для ручной сборки поста" not in pkg.caption


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
    assert "Венера" in pkg.caption or "Нептун" in pkg.caption or "венера" in pkg.caption.lower()
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
    assert (out / "hook.txt").read_text(encoding="utf-8-sig").strip()
    assert (out / "post_package.md").read_text(encoding="utf-8-sig").startswith("# Catstyle post package")


def test_human_text_files_utf8_sig_json_utf8_cyrillic(tmp_path: Path) -> None:
    """Windows-friendly BOM on .md/.txt; JSON UTF-8 without BOM; Cyrillic preserved."""
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
                "suggested_output_name": "x.png",
                "status": "pending",
            },
        ],
    }
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    out = tmp_path / "enc"
    write_catstyle_post_package(pkg, out, overwrite=False)

    bom = b"\xef\xbb\xbf"
    for fname in (
        "post_package.md",
        "caption.txt",
        "hook.txt",
        "compensation.txt",
        "checklist.txt",
    ):
        data = (out / fname).read_bytes()
        assert data.startswith(bom), f"{fname} should start with UTF-8 BOM for PowerShell"
        text_sig = (out / fname).read_text(encoding="utf-8-sig")
        assert re.search(r"[\u0400-\u04FF]", text_sig), f"{fname} should contain Cyrillic"

    hook_txt = (out / "hook.txt").read_text(encoding="utf-8-sig")
    assert "Юпитер" in hook_txt and "Марс" in hook_txt

    json_bytes = (out / "post_package.json").read_bytes()
    assert not json_bytes.startswith(bom), "JSON should not use BOM"
    raw_text = json_bytes.decode("utf-8")
    assert "\\u04" not in raw_text, "Cyrillic should not be JSON unicode-escaped on disk"
    parsed = json.loads(raw_text)
    assert "Юпитер" in parsed["hook"] or "Марс" in parsed["hook"]
    assert "Юпитер" in parsed["caption"] or "Марс" in parsed["caption"]
    assert parsed.get("planet_a") == "Jupiter"
    assert parsed.get("planet_b") == "Mars"


def test_write_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    manifest = {"date": "2026-03-03", "editorial_profile": "charged", "jobs": []}
    mp = _write_manifest(tmp_path, manifest)
    pkg = build_catstyle_post_package(mp)
    out = tmp_path / "pkg"
    write_catstyle_post_package(pkg, out, overwrite=False)
    with pytest.raises(FileExistsError):
        write_catstyle_post_package(pkg, out, overwrite=False)
