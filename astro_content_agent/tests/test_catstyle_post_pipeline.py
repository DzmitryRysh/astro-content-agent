"""Tests for Catstyle post pipeline orchestrator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import astro_content_agent.services.content.catstyle_post_pipeline as pipeline_mod
from astro_content_agent.services.content.catstyle_post_package_quality import CatstylePostPackageQualityResult
from astro_content_agent.services.content.catstyle_post_pipeline import run_catstyle_post_pipeline


def _write_manifest_and_images(tmp_path: Path) -> tuple[Path, Path]:
    """Minimal single-job manifest + matching PNG on disk."""
    date = "2026-11-30"
    img_name = "catstyle_2026-11-30_001_venus_neptune_trine_flow.png"
    gen = tmp_path / "gen"
    gen.mkdir()
    (gen / img_name).write_bytes(b"\x89PNG\r\n\x1a\n")

    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": date,
        "editorial_profile": "balanced",
        "selected_candidate": {
            "planet_a": "Venus",
            "planet_b": "Neptune",
            "aspect_type": "trine",
            "mode_recommendation": "flow",
            "total_score": 40,
        },
        "jobs": [
            {
                "job_id": "j1",
                "date": date,
                "planet_a": "Venus",
                "planet_b": "Neptune",
                "aspect_type": "trine",
                "editorial_profile": "balanced",
                "mode": "flow",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": img_name,
                "status": "pending",
            }
        ],
    }
    mp = tmp_path / "image_generation_jobs.json"
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return mp, gen


def test_pipeline_without_approve_review_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    mp, gen = _write_manifest_and_images(tmp_path)

    r = run_catstyle_post_pipeline(mp, generated_images_dir=gen, overwrite=True)

    assert r.status == "review_ready"
    assert r.quality_status == "ready"
    assert r.publish_handoff_dir is None
    pkg_dir = tmp_path / "catstyle_post_packages" / "2026-11-30"
    assert (pkg_dir / "post_package.json").is_file()
    assert (pkg_dir / "manual_review.json").is_file()
    assert r.manual_review_path == str((pkg_dir / "manual_review.json").resolve())


def test_pipeline_with_approve_ready_for_publish(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    mp, gen = _write_manifest_and_images(tmp_path)

    r = run_catstyle_post_pipeline(
        mp,
        generated_images_dir=gen,
        approve=True,
        approval_notes="Ship it.",
        overwrite=True,
    )

    assert r.status == "ready_for_manual_publish"
    assert r.publish_handoff_dir
    ph = Path(r.publish_handoff_dir)
    assert (ph / "publish_handoff.json").is_file()
    assert (ph / "caption_final.txt").is_file()


def test_pipeline_needs_attention_when_qc_not_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    mp, gen = _write_manifest_and_images(tmp_path)

    def _bad_qc(package_dir: Path):
        return CatstylePostPackageQualityResult(
            status="needs_attention",
            score=50,
            passed_checks=[],
            warnings=["warn"],
            errors=["qc gate failed"],
            package_dir=str(package_dir),
            recommended_primary_image=None,
        )

    monkeypatch.setattr(pipeline_mod, "check_catstyle_post_package", _bad_qc)

    r = run_catstyle_post_pipeline(
        mp,
        generated_images_dir=gen,
        approve=True,
        approval_notes="x",
        overwrite=True,
    )

    assert r.status == "needs_attention"
    assert r.errors
    assert "qc gate failed" in r.errors[0]
    assert r.publish_handoff_dir is None
    ph = tmp_path / "catstyle_publish_handoffs" / "2026-11-30" / "publish_handoff.json"
    assert not ph.is_file()


def test_pipeline_approval_notes_empty_allowed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    mp, gen = _write_manifest_and_images(tmp_path)

    r = run_catstyle_post_pipeline(mp, generated_images_dir=gen, approve=True, approval_notes="", overwrite=True)

    assert r.status == "ready_for_manual_publish"
    pkg_dir = tmp_path / "catstyle_post_packages" / "2026-11-30"
    blob = json.loads((pkg_dir / "manual_review.json").read_text(encoding="utf-8"))
    assert blob["approval_status"] == "approve"
    assert blob["reviewer_notes"] == ""
