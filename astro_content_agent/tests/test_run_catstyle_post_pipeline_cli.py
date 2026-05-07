"""Tests for scripts/aca/run_catstyle_post_pipeline.py CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _write_manifest_and_images(tmp_path: Path) -> tuple[Path, Path]:
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


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "run_catstyle_post_pipeline.py"
    spec = importlib.util.spec_from_file_location("_run_catstyle_post_pipeline_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def pipe_cli():
    return _load_cli()


def test_cli_human_readable(pipe_cli, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    mp, gen = _write_manifest_and_images(tmp_path)

    old = sys.argv[:]
    try:
        sys.argv = [
            "run_catstyle_post_pipeline.py",
            "--manifest",
            str(mp),
            "--generated-images-dir",
            str(gen),
            "--overwrite",
        ]
        assert pipe_cli.main() == 0
    finally:
        sys.argv = old

    out = capsys.readouterr().out
    assert "Catstyle post pipeline" in out
    assert "review_ready" in out


def test_cli_json_output(pipe_cli, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    mp, gen = _write_manifest_and_images(tmp_path)

    old = sys.argv[:]
    try:
        sys.argv = [
            "run_catstyle_post_pipeline.py",
            "--manifest",
            str(mp),
            "--generated-images-dir",
            str(gen),
            "--overwrite",
            "--approve",
            "--json",
        ]
        assert pipe_cli.main() == 0
    finally:
        sys.argv = old

    blob = json.loads(capsys.readouterr().out)
    assert blob["status"] == "ready_for_manual_publish"
    assert blob["publish_handoff_dir"]
    assert blob["date"] == "2026-11-30"
