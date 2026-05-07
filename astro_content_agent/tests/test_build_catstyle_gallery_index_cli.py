"""Tests for scripts/aca/build_catstyle_gallery_index.py CLI."""
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
    p = repo / "scripts" / "aca" / "build_catstyle_gallery_index.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_gallery_index_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def gi_cli():
    return _load_cli()


def _write_handoff(root: Path, date: str, *, publish_status: str = "ready_for_manual_publish", approval_status: str = "approve") -> None:
    hdir = root / date
    hdir.mkdir(parents=True, exist_ok=True)
    pkg_dir = root / "pkg" / date
    pkg_dir.mkdir(parents=True, exist_ok=True)
    post_path = pkg_dir / "post_package.json"
    post_path.write_text(
        json.dumps(
            {
                "date": date,
                "planet_a": "Pluto",
                "planet_b": "Mars",
                "aspect_type": "square",
                "mode": "tension",
                "aspect_summary": "Pluto square Mars",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    payload = {
        "date": date,
        "publish_status": publish_status,
        "approval_status": approval_status,
        "reviewed_at": "2026-10-01T12:00:00+00:00",
        "created_at": "2026-10-01T12:30:00+00:00",
        "recommended_primary_image": str((hdir / "hero.png").resolve()),
        "caption_final": "Подпись.",
        "hook": "Хук.",
        "reviewer_notes": "ok",
        "source_post_package_path": str(post_path.resolve()),
        "source_manual_review_path": str((pkg_dir / "manual_review.json").resolve()),
    }
    (hdir / "hero.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (hdir / "publish_handoff.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_cli_builds_gallery_index_files(gi_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "catstyle_publish_handoffs"
    _write_handoff(root, "2026-10-01")
    _write_handoff(root, "2026-10-02")
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_gallery_index.py",
            "--handoffs-dir",
            str(root),
            "--output-dir",
            str(root),
        ]
        assert gi_cli.main() == 0
    finally:
        sys.argv = old
    assert (root / "gallery_index.json").is_file()
    assert (root / "gallery_index.md").is_file()
    out = capsys.readouterr().out
    assert "Catstyle gallery index" in out
    assert "posts_indexed" in out


def test_cli_json_output_and_include_not_ready(gi_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "catstyle_publish_handoffs"
    _write_handoff(root, "2026-10-03")
    _write_handoff(root, "2026-10-04", publish_status="draft", approval_status="pending_review")
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_gallery_index.py",
            "--handoffs-dir",
            str(root),
            "--output-dir",
            str(root),
            "--include-not-ready",
            "--json",
        ]
        assert gi_cli.main() == 0
    finally:
        sys.argv = old
    payload = json.loads(capsys.readouterr().out)
    assert payload["posts_indexed"] == 2
    assert set(payload["files_written"]) == {"gallery_index.json", "gallery_index.md"}
