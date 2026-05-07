"""Tests for scripts/aca/mark_catstyle_published.py CLI."""
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
    p = repo / "scripts" / "aca" / "mark_catstyle_published.py"
    spec = importlib.util.spec_from_file_location("_mark_catstyle_published_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def pub_cli():
    return _load_cli()


def _write_handoff(tmp_path: Path, *, status: str = "ready_for_manual_publish") -> Path:
    hdir = tmp_path / "catstyle_publish_handoffs" / "2026-11-02"
    hdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": "2026-11-02",
        "publish_status": status,
        "approval_status": "approve",
        "recommended_primary_image": str((hdir / "hero.png").resolve()),
        "caption_final": "caption",
        "hook": "hook",
    }
    (hdir / "hero.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (hdir / "publish_handoff.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return hdir


def test_cli_marks_published_and_writes_files(pub_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    hdir = _write_handoff(tmp_path)
    old = sys.argv[:]
    try:
        sys.argv = [
            "mark_catstyle_published.py",
            "--handoff-dir",
            str(hdir),
            "--instagram-url",
            "https://instagram.com/p/abc",
            "--notes",
            "done",
        ]
        assert pub_cli.main() == 0
    finally:
        sys.argv = old
    assert (hdir / "publish_record.json").is_file()
    assert (hdir / "publish_record.md").is_file()
    out = capsys.readouterr().out
    assert "Catstyle published record" in out
    blob = json.loads((hdir / "publish_record.json").read_text(encoding="utf-8"))
    assert blob["instagram_url"] == "https://instagram.com/p/abc"
    assert blob["notes"] == "done"


def test_cli_non_ready_fails(pub_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    hdir = _write_handoff(tmp_path, status="draft")
    old = sys.argv[:]
    try:
        sys.argv = ["mark_catstyle_published.py", "--handoff-dir", str(hdir)]
        assert pub_cli.main() == 1
    finally:
        sys.argv = old
    assert "ready_for_manual_publish" in capsys.readouterr().err
