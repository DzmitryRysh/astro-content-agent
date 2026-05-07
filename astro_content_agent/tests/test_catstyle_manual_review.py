"""Tests for Catstyle manual review builder."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_manual_review import (
    MANUAL_REVIEW_VERSION,
    REVIEW_QUESTIONS,
    SUGGESTED_DECISIONS,
    build_catstyle_manual_review,
    write_catstyle_manual_review,
)
from astro_content_agent.services.content.catstyle_post_package_quality import (
    CatstylePostPackageQualityResult,
)


def _write_post_package(tmp_path: Path, *, hook: str = "Хук.") -> Path:
    img_dir = tmp_path / "imgs"
    img_dir.mkdir()
    p = img_dir / "primary.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n")
    alt = img_dir / "alt.png"
    alt.write_bytes(b"\x89PNG\r\n\x1a\n")
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    pkg = {
        "version": "catstyle-post-package-v1",
        "date": "2026-07-01",
        "editorial_profile": "charged",
        "hook": hook,
        "caption": "Подпись на русском.",
        "compensation": "Компенсация практичная.",
        "checklist": "Чеклист.",
        "carousel_slide_text": "Карусель текст.",
        "shot_mode": "hero_pair",
        "style_reference_image_path": "references/style.png",
        "generated_image_paths": [str(p.resolve()), str(alt.resolve())],
        "recommended_primary_image": str(p.resolve()),
        "image_jobs_summary": [
            {"job_id": "j1", "planet_a": "Jupiter", "planet_b": "Mars", "aspect_type": "square"}
        ],
        "source_manifest_path": str(tmp_path / "m.json"),
    }
    (pkg_dir / "post_package.json").write_text(json.dumps(pkg, ensure_ascii=False), encoding="utf-8")
    return pkg_dir


def test_build_includes_quality_and_images(tmp_path: Path) -> None:
    pkg_dir = _write_post_package(tmp_path)
    qc = CatstylePostPackageQualityResult(
        status="ready",
        score=93,
        passed_checks=["ok"],
        warnings=[],
        errors=[],
        package_dir=str(pkg_dir.resolve()),
        recommended_primary_image=None,
    )
    r = build_catstyle_manual_review(pkg_dir, quality_result=qc)
    assert r.version == MANUAL_REVIEW_VERSION
    assert r.date == "2026-07-01"
    assert r.package_dir == str(pkg_dir.resolve())
    assert r.quality_status == "ready"
    assert r.quality_score == 93
    assert len(r.generated_image_paths) == 2
    assert r.style_reference_image_path == "references/style.png"
    assert r.recommended_primary_image
    assert r.review_questions == REVIEW_QUESTIONS
    assert len(r.suggested_decisions) == len(SUGGESTED_DECISIONS)
    assert {d["value"] for d in r.suggested_decisions} == {"approve", "revise_text", "regenerate_images", "reject"}
    assert r.approval_status == "pending_review"
    assert r.reviewer_notes == ""
    assert r.reviewed_at is None


def test_build_runs_quality_when_not_passed(tmp_path: Path) -> None:
    pkg_dir = _write_post_package(tmp_path)
    r = build_catstyle_manual_review(pkg_dir)
    assert r.quality_score >= 0
    assert r.quality_status in ("ready", "needs_attention")


def test_write_creates_json_and_md(tmp_path: Path) -> None:
    pkg_dir = _write_post_package(tmp_path)
    r = build_catstyle_manual_review(pkg_dir)
    out = tmp_path / "out"
    out.mkdir()
    names = write_catstyle_manual_review(r, out, overwrite=False)
    assert set(names) == {"manual_review.json", "manual_review.md"}
    blob = json.loads((out / "manual_review.json").read_text(encoding="utf-8"))
    assert blob["version"] == MANUAL_REVIEW_VERSION
    assert blob["approval_status"] == "pending_review"
    assert blob.get("reviewed_at") is None
    assert len(blob["review_questions"]) == len(REVIEW_QUESTIONS)
    assert "Подпись" in blob["caption"]
    md_raw = (out / "manual_review.md").read_bytes()
    assert md_raw.startswith(b"\xef\xbb\xbf")
    md = (out / "manual_review.md").read_text(encoding="utf-8-sig")
    assert "# Catstyle manual review" in md
    assert "Quality summary" in md
    assert "Review questions" in md
    assert "Suggested decisions" in md
    assert "Основная картинка сильнее альтернативной?" in md
    assert "```text" not in md


def test_missing_post_package_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        build_catstyle_manual_review(empty)


def test_write_refuses_overwrite(tmp_path: Path) -> None:
    pkg_dir = _write_post_package(tmp_path)
    r = build_catstyle_manual_review(pkg_dir)
    write_catstyle_manual_review(r, pkg_dir, overwrite=False)
    with pytest.raises(FileExistsError):
        write_catstyle_manual_review(r, pkg_dir, overwrite=False)
