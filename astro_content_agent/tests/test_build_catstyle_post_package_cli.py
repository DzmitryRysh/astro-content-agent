"""Tests for scripts/aca/build_catstyle_post_package.py CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "build_catstyle_post_package.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_post_package_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def pkg_cli():
    return _load_cli()


def test_cli_builds_default_output_dir(pkg_cli, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-06-01",
        "editorial_profile": "charged",
        "jobs": [
            {
                "job_id": "x",
                "planet_a": "Jupiter",
                "planet_b": "Mars",
                "aspect_type": "square",
                "editorial_profile": "charged",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "shot_role": "hero_poster",
                "suggested_output_name": "hero.png",
                "status": "pending",
            }
        ],
    }
    mp = tmp_path / "image_generation_jobs.json"
    mp.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    gen = tmp_path / "g"
    gen.mkdir()
    (gen / "hero.png").write_text("x", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_post_package.py",
            "--manifest",
            str(mp),
            "--generated-images-dir",
            str(gen),
        ]
        assert pkg_cli.main() == 0
    finally:
        sys.argv = old

    out = tmp_path / "catstyle_post_packages" / "2026-06-01"
    assert (out / "post_package.json").is_file()
    assert (out / "post_package.md").is_file()
    assert (out / "caption.txt").is_file()
    assert (out / "hook.txt").is_file()
    blob = json.loads((out / "post_package.json").read_text(encoding="utf-8"))
    assert blob["recommended_primary_image"]
    assert blob["generated_image_paths"]


def test_cli_missing_manifest_exits_nonzero(pkg_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["build_catstyle_post_package.py", "--manifest", str(tmp_path / "missing.json")]
        assert pkg_cli.main() == 1
    finally:
        sys.argv = old
    assert capsys.readouterr().err
