"""Tests for scripts/aca/check_catstyle_post_package.py CLI."""
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
    p = repo / "scripts" / "aca" / "check_catstyle_post_package.py"
    spec = importlib.util.spec_from_file_location("_check_catstyle_post_package_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def qc_cli():
    return _load_cli()


def test_cli_human_readable(qc_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    img_dir = tmp_path / "i"
    img_dir.mkdir()
    png = img_dir / "p.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    pkg = {
        "date": "2026-02-02",
        "hook": "Хук на русском.",
        "caption": "Подпись.",
        "compensation": "Комп.",
        "checklist": "Чек.",
        "carousel_slide_text": "Карусель.",
        "shot_mode": "standard",
        "generated_image_paths": [str(png.resolve())],
        "recommended_primary_image": str(png.resolve()),
        "image_jobs_summary": [
            {"job_id": "j", "planet_a": "A", "planet_b": "B", "aspect_type": "trine"}
        ],
    }
    (pkg_dir / "post_package.json").write_text(json.dumps(pkg, ensure_ascii=False), encoding="utf-8")

    old = sys.argv[:]
    try:
        sys.argv = ["check_catstyle_post_package.py", "--package-dir", str(pkg_dir)]
        assert qc_cli.main() == 0
    finally:
        sys.argv = old

    out = capsys.readouterr().out
    assert "Catstyle post package quality" in out
    assert "status:" in out
    assert "score:" in out
    assert "primary_image:" in out
    assert "errors:" in out
    assert "warnings:" in out
    assert "passed:" in out


def test_cli_json_output(qc_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    img_dir = tmp_path / "i"
    img_dir.mkdir()
    png = img_dir / "p.png"
    png.write_bytes(b"x")
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    pkg = {
        "date": "2026-02-02",
        "hook": "Хук.",
        "caption": "Кап.",
        "compensation": "Комп.",
        "checklist": "Чек.",
        "carousel_slide_text": "Кар.",
        "shot_mode": "standard",
        "generated_image_paths": [str(png.resolve())],
        "recommended_primary_image": str(png.resolve()),
        "image_jobs_summary": [
            {"job_id": "j", "planet_a": "A", "planet_b": "B", "aspect_type": "sq"}
        ],
    }
    (pkg_dir / "post_package.json").write_text(json.dumps(pkg, ensure_ascii=False), encoding="utf-8")

    old = sys.argv[:]
    try:
        sys.argv = ["check_catstyle_post_package.py", "--package-dir", str(pkg_dir), "--json"]
        assert qc_cli.main() == 0
    finally:
        sys.argv = old

    blob = json.loads(capsys.readouterr().out)
    assert blob["package_dir"]
    assert "score" in blob
    assert blob["status"] in ("ready", "needs_attention")
