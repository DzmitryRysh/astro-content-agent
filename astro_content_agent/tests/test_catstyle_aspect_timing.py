"""Tests for Catstyle aspect timing in post package, captions, and publish handoff."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from astro_content_agent.services.content.catstyle_aspect_timing import (
    build_aspect_timing_from_manifest,
    format_ru_timing_caption_append,
)
from astro_content_agent.services.content.catstyle_manual_review import (
    approve_catstyle_manual_review,
    build_catstyle_manual_review,
    write_catstyle_manual_review,
)
from astro_content_agent.services.content.catstyle_post_package import (
    build_catstyle_post_package,
    render_catstyle_post_package_markdown,
    write_catstyle_post_package,
)
from astro_content_agent.services.content.catstyle_publish_handoff import (
    build_catstyle_publish_handoff,
    render_catstyle_publish_handoff_markdown,
    write_catstyle_publish_handoff,
)


def _manifest_minimal(**extra: object) -> dict:
    base = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-05-08",
        "editorial_profile": "balanced",
        "selected_candidate": {
            "planet_a": "Jupiter",
            "planet_b": "Mercury",
            "aspect_type": "sextile",
            "mode_recommendation": "flow",
            "total_score": 10,
        },
        "jobs": [
            {
                "job_id": "catstyle-2026-05-08-001",
                "date": "2026-05-08",
                "planet_a": "Jupiter",
                "planet_b": "Mercury",
                "aspect_type": "sextile",
                "editorial_profile": "balanced",
                "mode": "flow",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "catstyle_2026-05-08_001_jupiter_mercury_sextile_flow.png",
                "status": "pending",
            }
        ],
    }
    base.update(extra)
    return base


def _write_jobs(tmp_path: Path, data: dict) -> Path:
    mp = tmp_path / "image_generation_jobs.json"
    mp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return mp


def test_post_package_timing_block_and_caption_when_window_metadata(tmp_path: Path) -> None:
    man = _manifest_minimal(
        sky_scan_mode="day-window",
        sky_scan_step_hours_utc=2,
        selected_candidate={
            "planet_a": "Jupiter",
            "planet_b": "Mercury",
            "aspect_type": "sextile",
            "mode_recommendation": "flow",
            "total_score": 10,
            "orb": 0.41,
            "window_first_seen_hour_utc": 0,
            "window_last_seen_hour_utc": 22,
            "closest_hour_utc": 8,
        },
    )
    mp = _write_jobs(tmp_path, man)
    pkg = build_catstyle_post_package(mp)

    assert pkg.aspect_timing is not None
    assert pkg.aspect_timing.timing_status == "sky_window_utc"
    assert pkg.aspect_timing.peak_at_utc and "2026-05-08T08:00:00+00:00" in pkg.aspect_timing.peak_at_utc
    assert pkg.aspect_timing.window_start_utc and "T00:00:00+00:00" in pkg.aspect_timing.window_start_utc

    md = render_catstyle_post_package_markdown(pkg)
    assert "## Aspect timing (UTC)" in md
    assert "sky_window_utc" in md

    assert "**Про сроки:**" in pkg.caption
    assert "Окно аспекта" in pkg.caption
    cap_low = pkg.caption.lower()
    assert "utc" not in cap_low
    assert "орбис" not in cap_low
    assert "эксклюзивная" not in cap_low
    assert "шаг 2" not in pkg.caption
    assert "orb_at_post_date" in md or "peak_at_utc" in md


def test_fallback_missing_exact_window_no_extra_dates(tmp_path: Path) -> None:
    """Do not invent a second calendar day when the manifest only supplies the post date."""
    man = _manifest_minimal(
        date="2026-06-09",
        sky_scan_mode="noon",
        sky_scan_step_hours_utc=None,
        selected_candidate={
            "planet_a": "Jupiter",
            "planet_b": "Mars",
            "aspect_type": "square",
            "mode_recommendation": "tension",
            "total_score": 38,
        },
    )
    man["jobs"][0]["date"] = "2026-06-09"
    mp = _write_jobs(tmp_path, man)
    pkg = build_catstyle_post_package(mp)

    assert pkg.aspect_timing is not None
    assert pkg.aspect_timing.timing_status == "missing_exact_window"
    assert "10 июня" not in pkg.caption
    assert "2026-06-10" not in pkg.caption


def test_orb_only_estimate_branch(tmp_path: Path) -> None:
    man = _manifest_minimal(
        sky_scan_mode="noon",
        selected_candidate={
            "planet_a": "Jupiter",
            "planet_b": "Mercury",
            "aspect_type": "sextile",
            "mode_recommendation": "flow",
            "total_score": 10,
            "orb": 0.55,
        },
    )
    mp = _write_jobs(tmp_path, man)
    meta = build_aspect_timing_from_manifest(json.loads(mp.read_text(encoding="utf-8")))
    assert meta.timing_status == "orb_only_estimate"
    txt = format_ru_timing_caption_append(meta, post_date=date(2026, 5, 8), personal_planet="Mercury")
    assert "орбис" not in txt.lower()
    assert "utc" not in txt.lower()
    assert "день публикации" in txt.lower()


def test_format_ru_never_invents_peak_without_source_hour(tmp_path: Path) -> None:
    meta = build_aspect_timing_from_manifest(
        {
            "date": "2026-05-08",
            "sky_scan_mode": "noon",
            "selected_candidate": {
                "planet_a": "Jupiter",
                "planet_b": "Mars",
                "aspect_type": "trine",
                "mode_recommendation": "mixed",
                "total_score": 20,
                "orb": None,
            },
            "jobs": [],
        }
    )
    assert meta.timing_status == "missing_exact_window"
    assert meta.peak_at_utc is None
    para = format_ru_timing_caption_append(meta, post_date=date(2026, 5, 8), personal_planet="Mars")
    assert "08:00" not in para
    assert "день публикации" in para.lower()


def test_publish_handoff_markdown_includes_timing(tmp_path: Path) -> None:
    man = _manifest_minimal(
        sky_scan_mode="day-window",
        sky_scan_step_hours_utc=2,
        selected_candidate={
            "planet_a": "Jupiter",
            "planet_b": "Mercury",
            "aspect_type": "sextile",
            "mode_recommendation": "flow",
            "total_score": 10,
            "orb": 0.2,
            "window_first_seen_hour_utc": 0,
            "window_last_seen_hour_utc": 22,
            "closest_hour_utc": 8,
        },
    )
    mp = _write_jobs(tmp_path, man)
    gen = tmp_path / "gen"
    gen.mkdir()
    png = gen / "catstyle_2026-05-08_001_jupiter_mercury_sextile_flow.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")

    pkg = build_catstyle_post_package(mp, generated_images_dir=gen)
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    write_catstyle_post_package(pkg, pkg_dir, overwrite=False)
    mr = build_catstyle_manual_review(pkg_dir)
    write_catstyle_manual_review(mr, pkg_dir, overwrite=False)
    approve_catstyle_manual_review(pkg_dir, "approve", "ok")

    h = build_catstyle_publish_handoff(pkg_dir)
    assert h.aspect_timing is not None
    md = render_catstyle_publish_handoff_markdown(h)
    assert "## Aspect timing (UTC)" in md
    assert "peak_at_utc" in md or "window_start_utc" in md
    assert "**Про сроки:**" in h.caption_final

    out = tmp_path / "ho"
    write_catstyle_publish_handoff(h, out, overwrite=False)
    cap_txt = (out / "caption_final.txt").read_text(encoding="utf-8-sig")
    assert "**Про сроки:**" in cap_txt
    cl = cap_txt.lower()
    assert "utc" not in cl
    assert "орбис" not in cl
    assert "эксклюзивная" not in cl
    assert "шаг 2" not in cap_txt


def test_manual_override_manifest_timing_is_missing_window(tmp_path: Path) -> None:
    meta = build_aspect_timing_from_manifest(
        {
            "date": "2026-08-10",
            "sky_scan_mode": "manual_override",
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
            },
            "jobs": [],
        }
    )
    assert meta.timing_status == "missing_exact_window"
    assert meta.sky_scan_mode == "manual_override"
    assert meta.data_source == "manifest_manual_override_v1"


def test_manual_override_day_window_match_data_source(tmp_path: Path) -> None:
    man = {
        "date": "2026-06-10",
        "sky_scan_mode": "day-window",
        "sky_scan_step_hours_utc": 2,
        "manual_aspect_override": {"enabled": True, "planet_a": "Mercury", "planet_b": "Jupiter", "aspect_type": "sextile", "mode": "flow"},
        "selected_candidate": {
            "planet_a": "Mercury",
            "planet_b": "Jupiter",
            "aspect_type": "sextile",
            "mode_recommendation": "flow",
            "total_score": 0,
            "manual_override_sky_timing_match": True,
            "orb": 0.4,
            "closest_hour_utc": 8,
            "window_first_seen_hour_utc": 0,
            "window_last_seen_hour_utc": 22,
            "window_start_hour_utc": 0,
            "window_end_hour_utc": 22,
        },
        "jobs": [],
    }
    mp = tmp_path / "m.json"
    mp.write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    pkg = build_catstyle_post_package(mp)
    assert pkg.aspect_timing is not None
    assert pkg.aspect_timing.timing_status == "sky_window_utc"
    assert pkg.aspect_timing.data_source == "manual_override_with_timing_v1"
    md = render_catstyle_post_package_markdown(pkg)
    assert "## Aspect timing (UTC)" in md
    assert "**Про сроки:**" in pkg.caption
    assert "utc" not in pkg.caption.lower()


def test_manual_override_with_timing_handoff_caption_final(tmp_path: Path) -> None:
    man = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-06-10",
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
            "orb": 0.4,
            "closest_hour_utc": 8,
            "window_first_seen_hour_utc": 0,
            "window_last_seen_hour_utc": 22,
            "window_start_hour_utc": 0,
            "window_end_hour_utc": 22,
        },
        "jobs": [
            {
                "job_id": "catstyle-2026-06-10-001",
                "date": "2026-06-10",
                "planet_a": "Mercury",
                "planet_b": "Jupiter",
                "aspect_type": "sextile",
                "editorial_profile": "charged",
                "mode": "flow",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "catstyle_2026-06-10_001_mercury_jupiter_sextile_flow.png",
                "status": "pending",
            }
        ],
    }
    mp = tmp_path / "mj.json"
    mp.write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    gen = tmp_path / "g2"
    gen.mkdir()
    png = gen / "catstyle_2026-06-10_001_mercury_jupiter_sextile_flow.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    pkg = build_catstyle_post_package(mp, generated_images_dir=gen)
    pkg_dir = tmp_path / "pkg_mj"
    pkg_dir.mkdir()
    write_catstyle_post_package(pkg, pkg_dir, overwrite=False)
    mr = build_catstyle_manual_review(pkg_dir)
    write_catstyle_manual_review(mr, pkg_dir, overwrite=False)
    approve_catstyle_manual_review(pkg_dir, "approve", "ok")
    h = build_catstyle_publish_handoff(pkg_dir)
    md = render_catstyle_publish_handoff_markdown(h)
    assert "## Aspect timing (UTC)" in md
    assert "manual_override_with_timing_v1" in md
    out = tmp_path / "ho_mj"
    write_catstyle_publish_handoff(h, out, overwrite=False)
    cap = (out / "caption_final.txt").read_text(encoding="utf-8-sig")
    assert "Окно аспекта" in cap
    assert "Меркурий" in cap
    assert "**Про сроки:**" in cap
    assert "1–2 дня" in cap or "около 3 дней" in cap
    low = cap.lower()
    assert "utc" not in low
    assert "орбис" not in low
    assert "эксклюзивная" not in low
    assert "шаг 2" not in low
    assert "window_start_utc" in md or "peak_at_utc" in md
    assert "orb_at_post_date" in md or "sky_scan_step_hours_utc" in md


def test_manual_override_day_window_miss_data_source() -> None:
    meta = build_aspect_timing_from_manifest(
        {
            "date": "2026-06-10",
            "sky_scan_mode": "day-window",
            "sky_scan_step_hours_utc": 2,
            "manual_aspect_override": {"enabled": True, "planet_a": "Mercury", "planet_b": "Jupiter", "aspect_type": "sextile", "mode": "flow"},
            "selected_candidate": {
                "planet_a": "Mercury",
                "planet_b": "Jupiter",
                "aspect_type": "sextile",
                "mode_recommendation": "flow",
                "total_score": 0,
                "manual_override_sky_timing_match": False,
            },
            "jobs": [],
        }
    )
    assert meta.timing_status == "missing_exact_window"
    assert meta.data_source == "manual_override_no_sky_match_v1"
