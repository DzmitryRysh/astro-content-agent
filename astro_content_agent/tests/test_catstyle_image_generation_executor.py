"""Tests for Catstyle image generation executor stub v0."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_image_generation_executor import (
    CatstyleImageExecutorStubResult,
    execute_catstyle_image_jobs,
    execute_catstyle_image_jobs_stub,
)


def _write_manifest(path: Path, jobs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "version": "catstyle-image-generation-jobs-v0",
                "date": "2026-05-02",
                "jobs": jobs,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _sample_job(i: int, status: str = "pending") -> dict:
    return {
        "job_id": f"catstyle-2026-05-02-{i:03d}",
        "date": "2026-05-02",
        "planet_a": "Jupiter",
        "planet_b": "Mars",
        "aspect_type": "square",
        "editorial_profile": "charged",
        "mode": "tension",
        "source": "seed",
        "total_score": 38,
        "prompt_index": i,
        "variant_index": 0,
        "prompt_text": f"Prompt body number {i} " * 20,
        "negative_prompt": "neg",
        "animation_prompt": "anim",
        "carousel_idea": "car",
        "suggested_output_name": f"out_{i}.png",
        "status": status,
    }


def test_stub_writes_one_file_per_job_and_execution_manifest(tmp_path: Path) -> None:
    mpath = tmp_path / "image_generation_jobs.json"
    _write_manifest(mpath, [_sample_job(1), _sample_job(2)])
    out = tmp_path / "stub_out"
    r = execute_catstyle_image_jobs_stub(mpath, output_dir=out, overwrite=False)
    assert isinstance(r, CatstyleImageExecutorStubResult)
    assert r.status == "completed_stub"
    assert r.jobs_processed == 2
    assert len(r.outputs) == 2
    assert all(o.status == "generated_stub" for o in r.outputs)
    assert (out / "generated_stub_01.txt").is_file()
    assert (out / "generated_stub_02.txt").is_file()
    data = json.loads((out / "generated_stub_01.txt").read_text(encoding="utf-8"))
    assert data["status"] == "generated_stub"
    assert data["note"] == "Stub only. No image API was called."
    assert "Prompt body number 1" in data["prompt_preview"]
    exec_path = out / "image_generation_execution_stub.json"
    assert exec_path.is_file()
    ex = json.loads(exec_path.read_text(encoding="utf-8"))
    assert ex["jobs_processed"] == 2
    assert len(ex["outputs"]) == 2
    assert ex["source_manifest_path"] == str(mpath.resolve())


def test_default_output_dir_is_manifest_parent_generated_stub(tmp_path: Path) -> None:
    mpath = tmp_path / "pack" / "image_generation_jobs.json"
    _write_manifest(mpath, [_sample_job(1)])
    r = execute_catstyle_image_jobs_stub(mpath, output_dir=None)
    assert r.outputs_dir == str((mpath.parent / "generated_stub").resolve())
    assert (mpath.parent / "generated_stub" / "generated_stub_01.txt").is_file()


def test_skip_existing_when_overwrite_false(tmp_path: Path) -> None:
    mpath = tmp_path / "image_generation_jobs.json"
    _write_manifest(mpath, [_sample_job(1)])
    out = tmp_path / "out"
    execute_catstyle_image_jobs_stub(mpath, output_dir=out, overwrite=False)
    r2 = execute_catstyle_image_jobs_stub(mpath, output_dir=out, overwrite=False)
    assert r2.skipped_count == 1
    assert r2.outputs[0].status == "skipped_existing"
    assert r2.stub_files_written == []


def test_overwrite_true_rewrites(tmp_path: Path) -> None:
    mpath = tmp_path / "image_generation_jobs.json"
    _write_manifest(mpath, [_sample_job(1)])
    out = tmp_path / "out"
    execute_catstyle_image_jobs_stub(mpath, output_dir=out, overwrite=False)
    p1 = (out / "generated_stub_01.txt").read_text(encoding="utf-8")
    _write_manifest(mpath, [_sample_job(99)])
    r2 = execute_catstyle_image_jobs_stub(mpath, output_dir=out, overwrite=True)
    assert r2.outputs[0].status == "generated_stub"
    p2 = (out / "generated_stub_01.txt").read_text(encoding="utf-8")
    assert p1 != p2
    assert "99" in p2


def test_invalid_manifest_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        execute_catstyle_image_jobs_stub(bad)


def test_missing_jobs_key_raises(tmp_path: Path) -> None:
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"date": "2026-05-02"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing 'jobs'"):
        execute_catstyle_image_jobs_stub(p)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not found"):
        execute_catstyle_image_jobs_stub(tmp_path / "nope.json")


def test_empty_jobs_returns_no_jobs(tmp_path: Path) -> None:
    mpath = tmp_path / "image_generation_jobs.json"
    _write_manifest(mpath, [])
    r = execute_catstyle_image_jobs_stub(mpath, output_dir=tmp_path / "z")
    assert r.status == "no_jobs"
    assert r.jobs_processed == 0
    assert r.outputs == []


def test_execute_catstyle_image_jobs_stub_matches_generic_stub(tmp_path: Path) -> None:
    mpath = tmp_path / "image_generation_jobs.json"
    _write_manifest(mpath, [_sample_job(1)])
    out_a = tmp_path / "cmp_a"
    out_b = tmp_path / "cmp_b"
    a = execute_catstyle_image_jobs_stub(mpath, output_dir=out_a, overwrite=False)
    b = execute_catstyle_image_jobs(mpath, provider_name="stub", output_dir=out_b, overwrite=False)
    assert isinstance(a, CatstyleImageExecutorStubResult) and isinstance(b, CatstyleImageExecutorStubResult)
    assert a.status == b.status == "completed_stub"
    assert a.provider_name == b.provider_name == "stub"
    assert len(a.outputs) == len(b.outputs) == 1
    assert a.outputs[0].job_id == b.outputs[0].job_id


def test_unsupported_provider_raises_before_io(tmp_path: Path) -> None:
    mpath = tmp_path / "image_generation_jobs.json"
    _write_manifest(mpath, [_sample_job(1)])
    with pytest.raises(ValueError, match="Unsupported Catstyle image provider"):
        execute_catstyle_image_jobs(mpath, provider_name="dalle", output_dir=tmp_path / "x")


def test_no_pending_jobs_writes_execution_manifest(tmp_path: Path) -> None:
    mpath = tmp_path / "image_generation_jobs.json"
    _write_manifest(mpath, [_sample_job(1, status="done")])
    out = tmp_path / "out"
    r = execute_catstyle_image_jobs_stub(mpath, output_dir=out)
    assert r.status == "no_pending_jobs"
    assert (out / "image_generation_execution_stub.json").is_file()
