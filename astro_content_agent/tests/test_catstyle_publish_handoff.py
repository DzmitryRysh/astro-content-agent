"""Tests for Catstyle publish handoff builder."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_manual_review import (
    MANUAL_REVIEW_VERSION,
    approve_catstyle_manual_review,
    build_catstyle_manual_review,
    write_catstyle_manual_review,
)
from astro_content_agent.services.content.catstyle_post_package import (
    POST_PACKAGE_VERSION,
    build_catstyle_post_package,
    write_catstyle_post_package,
)
from astro_content_agent.services.content.catstyle_publish_handoff import (
    PUBLISH_HANDOFF_VERSION,
    CatstylePublishHandoffError,
    build_catstyle_publish_handoff,
    write_catstyle_publish_handoff,
)


def _write_bundle(
    tmp_path: Path,
    *,
    approval_status: str = "approve",
    quality_status: str = "ready",
    quality_score: int = 92,
    primary_exists: bool = True,
) -> Path:
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    img_dir = pkg_dir / "imgs"
    img_dir.mkdir()
    primary = img_dir / "hero.png"
    primary.write_bytes(b"\x89PNG\r\n\x1a\n")
    alt = img_dir / "alt.png"
    alt.write_bytes(b"\x89PNG\r\n\x1a\n")

    primary_path = str(primary.resolve()) if primary_exists else str((pkg_dir / "missing.png").resolve())

    post_pkg = {
        "version": POST_PACKAGE_VERSION,
        "date": "2026-10-15",
        "editorial_profile": "charged",
        "aspect_summary": "Jupiter square Mars",
        "hook": "Хук короткий.",
        "caption": "Подпись финальная для поста.",
        "carousel_slide_text": "Текст карусели.",
        "compensation": "Компенсация.",
        "checklist": "Чеклист для поста.",
        "shot_mode": "hero_pair",
        "style_reference_image_path": None,
        "world_template": "wt",
        "scene_template": "st",
        "render_style_profile": "rs",
        "generated_image_paths": [str(primary.resolve()), str(alt.resolve())],
        "recommended_primary_image": primary_path,
        "image_jobs_summary": [{"job_id": "j1"}],
        "source_manifest_path": str(tmp_path / "manifest.json"),
    }
    (pkg_dir / "post_package.json").write_text(json.dumps(post_pkg, ensure_ascii=False), encoding="utf-8")

    manual = {
        "version": MANUAL_REVIEW_VERSION,
        "date": "2026-10-15",
        "package_dir": str(pkg_dir.resolve()),
        "quality_status": quality_status,
        "quality_score": quality_score,
        "quality_errors": [],
        "quality_warnings": [],
        "recommended_primary_image": primary_path,
        "generated_image_paths": post_pkg["generated_image_paths"],
        "style_reference_image_path": None,
        "hook": post_pkg["hook"],
        "caption": post_pkg["caption"],
        "compensation": post_pkg["compensation"],
        "checklist": post_pkg["checklist"],
        "carousel_slide_text": post_pkg["carousel_slide_text"],
        "review_questions": [],
        "suggested_decisions": [],
        "approval_status": approval_status,
        "reviewer_notes": "Ок.",
        "reviewed_at": "2026-10-15T14:00:00+00:00",
    }
    (pkg_dir / "manual_review.json").write_text(json.dumps(manual, ensure_ascii=False), encoding="utf-8")
    return pkg_dir


def test_approved_build_and_write(tmp_path: Path) -> None:
    pkg_dir = _write_bundle(tmp_path)
    h = build_catstyle_publish_handoff(pkg_dir)
    assert h.version == PUBLISH_HANDOFF_VERSION
    assert h.publish_status == "ready_for_manual_publish"
    assert h.approval_status == "approve"
    assert h.caption_final == "Подпись финальная для поста."
    assert Path(h.recommended_primary_image).is_file()
    dt = datetime.fromisoformat(h.created_at.replace("Z", "+00:00"))
    assert dt.tzinfo is not None

    out = tmp_path / "handoff_out"
    names = write_catstyle_publish_handoff(h, out, overwrite=False)
    assert set(names) == {
        "publish_handoff.json",
        "publish_handoff.md",
        "caption_final.txt",
        "primary_image_path.txt",
        "publish_checklist.txt",
    }
    assert (out / "caption_final.txt").read_text(encoding="utf-8-sig").strip() == h.caption_final
    assert (out / "primary_image_path.txt").read_text(encoding="utf-8-sig").strip() == h.recommended_primary_image
    md = (out / "publish_handoff.md").read_text(encoding="utf-8-sig")
    assert "ready_for_manual_publish" in md
    blob = json.loads((out / "publish_handoff.json").read_text(encoding="utf-8"))
    assert blob["publish_status"] == "ready_for_manual_publish"


def test_handoff_caption_final_reflects_aspect_aware_post_package(tmp_path: Path) -> None:
    """Publish handoff copies caption from post_package built with Venus–Pluto opposition template."""
    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-08-12",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": "Pluto",
            "planet_b": "Venus",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
            "total_score": 0,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Pluto",
                "planet_b": "Venus",
                "aspect_type": "opposition",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "shot_role": "hero_poster",
                "suggested_output_name": "catstyle_2026-08-12_001_pluto_venus_opposition_tension.png",
                "status": "pending",
            },
            {
                "job_id": "j2",
                "planet_a": "Pluto",
                "planet_b": "Venus",
                "aspect_type": "opposition",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 2,
                "variant_index": 0,
                "shot_role": "alternate_action_angle",
                "suggested_output_name": "catstyle_2026-08-12_002_pluto_venus_opposition_tension.png",
                "status": "pending",
            },
        ],
    }
    mp = tmp_path / "jobs.json"
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    gen = tmp_path / "gen_handoff"
    gen.mkdir()
    for name in (
        "catstyle_2026-08-12_001_pluto_venus_opposition_tension.png",
        "catstyle_2026-08-12_002_pluto_venus_opposition_tension.png",
    ):
        (gen / name).write_bytes(b"\x89PNG\r\n\x1a\n")

    pkg = build_catstyle_post_package(mp, generated_images_dir=gen)
    assert "Пакет Catstyle для ручной сборки" not in pkg.caption

    pkg_dir = tmp_path / "full_pkg"
    pkg_dir.mkdir()
    write_catstyle_post_package(pkg, pkg_dir, overwrite=False)

    mr = build_catstyle_manual_review(pkg_dir)
    write_catstyle_manual_review(mr, pkg_dir, overwrite=False)
    approve_catstyle_manual_review(pkg_dir, "approve", "ok")

    h = build_catstyle_publish_handoff(pkg_dir)
    assert "Венера" in h.caption_final and "Плутон" in h.caption_final
    assert h.caption_final == pkg.caption.strip()


def test_non_approve_fails(tmp_path: Path) -> None:
    pkg_dir = _write_bundle(tmp_path, approval_status="reject")
    with pytest.raises(CatstylePublishHandoffError, match="approve"):
        build_catstyle_publish_handoff(pkg_dir)


def test_missing_primary_fails(tmp_path: Path) -> None:
    pkg_dir = _write_bundle(tmp_path, primary_exists=False)
    with pytest.raises(CatstylePublishHandoffError, match="does not exist"):
        build_catstyle_publish_handoff(pkg_dir)


def test_quality_not_ready_fails(tmp_path: Path) -> None:
    pkg_dir = _write_bundle(tmp_path, quality_status="needs_attention")
    with pytest.raises(CatstylePublishHandoffError, match="quality_status"):
        build_catstyle_publish_handoff(pkg_dir)


def test_quality_score_low_fails(tmp_path: Path) -> None:
    pkg_dir = _write_bundle(tmp_path, quality_score=70)
    with pytest.raises(CatstylePublishHandoffError, match="quality_score"):
        build_catstyle_publish_handoff(pkg_dir)


def test_empty_hook_fails(tmp_path: Path) -> None:
    pkg_dir = _write_bundle(tmp_path)
    post = json.loads((pkg_dir / "post_package.json").read_text(encoding="utf-8"))
    post["hook"] = "   "
    (pkg_dir / "post_package.json").write_text(json.dumps(post, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(CatstylePublishHandoffError, match="hook"):
        build_catstyle_publish_handoff(pkg_dir)
