"""Tests for scripts/aca/build_catstyle_publish_handoff.py CLI."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from astro_content_agent.tests.test_catstyle_publish_handoff import _write_bundle


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "build_catstyle_publish_handoff.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_publish_handoff_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def ph_cli():
    return _load_cli()


def test_cli_default_output_dir(
    ph_cli, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pkg_dir = _write_bundle(tmp_path)
    monkeypatch.chdir(tmp_path)
    old_argv = sys.argv[:]
    try:
        sys.argv = ["build_catstyle_publish_handoff.py", "--package-dir", str(pkg_dir)]
        assert ph_cli.main() == 0
    finally:
        sys.argv = old_argv

    out = tmp_path / "catstyle_publish_handoffs" / "2026-10-15"
    assert (out / "publish_handoff.json").is_file()
    assert (out / "publish_handoff.md").is_file()
    assert (out / "caption_final.txt").is_file()
    assert (out / "primary_image_path.txt").is_file()
    assert (out / "publish_checklist.txt").is_file()

    cap = capsys.readouterr().out
    assert "Catstyle publish handoff" in cap
    assert "ready_for_manual_publish" in cap or "status:" in cap


def test_cli_rejected_package_exits_error(ph_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pkg_dir = _write_bundle(tmp_path, approval_status="reject")
    old = sys.argv[:]
    try:
        sys.argv = ["build_catstyle_publish_handoff.py", "--package-dir", str(pkg_dir)]
        assert ph_cli.main() == 1
    finally:
        sys.argv = old
    assert "approve" in capsys.readouterr().err.lower()
