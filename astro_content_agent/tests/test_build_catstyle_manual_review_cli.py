"""Tests for scripts/aca/build_catstyle_manual_review.py CLI."""
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
    p = repo / "scripts" / "aca" / "build_catstyle_manual_review.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_manual_review_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def mr_cli():
    return _load_cli()


def test_cli_writes_into_package_dir_by_default(mr_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    img_dir = tmp_path / "imgs"
    img_dir.mkdir()
    png = img_dir / "p.png"
    png.write_bytes(b"x")
    alt = img_dir / "a.png"
    alt.write_bytes(b"x")
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    pkg = {
        "date": "2026-08-08",
        "hook": "Х.",
        "caption": "К.",
        "compensation": "К.",
        "checklist": "Ч.",
        "carousel_slide_text": "К.",
        "shot_mode": "standard",
        "generated_image_paths": [str(png.resolve()), str(alt.resolve())],
        "recommended_primary_image": str(png.resolve()),
        "style_reference_image_path": None,
        "image_jobs_summary": [
            {"job_id": "j", "planet_a": "A", "planet_b": "B", "aspect_type": "sq"}
        ],
        "source_manifest_path": str(tmp_path / "x.json"),
    }
    (pkg_dir / "post_package.json").write_text(json.dumps(pkg, ensure_ascii=False), encoding="utf-8")

    old = sys.argv[:]
    try:
        sys.argv = ["build_catstyle_manual_review.py", "--package-dir", str(pkg_dir)]
        assert mr_cli.main() == 0
    finally:
        sys.argv = old

    assert (pkg_dir / "manual_review.json").is_file()
    assert (pkg_dir / "manual_review.md").is_file()
    out = capsys.readouterr().out
    assert "Catstyle manual review" in out
    assert "manual_review.json" in out


def test_cli_missing_package_dir_file_errors(mr_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["build_catstyle_manual_review.py", "--package-dir", str(tmp_path / "nopkg")]
        assert mr_cli.main() == 1
    finally:
        sys.argv = old
    assert capsys.readouterr().err
