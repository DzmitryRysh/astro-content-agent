"""Tests for scripts/aca/export_catstyle_image_prompts.py CLI."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.services.content.catstyle_prompt_export import CatstylePromptExportResult


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    cli_path = repo / "scripts" / "aca" / "export_catstyle_image_prompts.py"
    spec = importlib.util.spec_from_file_location("_export_catstyle_image_prompts_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def export_cli():
    return _load_cli()


def _ok_result() -> CatstylePromptExportResult:
    return CatstylePromptExportResult(
        date="2026-05-02",
        output_dir="/tmp/x",
        files_written=["prompt_1.txt"],
        selected_candidate={"planet_a": "A", "planet_b": "B", "aspect_type": "trine", "total_score": 30},
        secondary_supportive_candidate=None,
        success=True,
    )


def test_cli_invalid_date(export_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["export_catstyle_image_prompts.py", "--date", "not-a-date"]
        assert export_cli.main() == 1
    finally:
        sys.argv = old
    assert "YYYY" in capsys.readouterr().err or "Date" in capsys.readouterr().err


def test_cli_writes_files(export_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "exp"
    old = sys.argv[:]
    mock_export = None
    try:
        sys.argv = [
            "export_catstyle_image_prompts.py",
            "--date",
            "2026-05-02",
            "--output-dir",
            str(out),
        ]
        with patch.object(export_cli, "export_catstyle_image_prompts", return_value=_ok_result()) as m:
            mock_export = m
            assert export_cli.main() == 0
    finally:
        sys.argv = old
    assert mock_export is not None
    mock_export.assert_called_once()
    call_args = mock_export.call_args[0]
    assert call_args[0].isoformat() == "2026-05-02"
    assert Path(call_args[1]).resolve() == out.resolve()
    captured = capsys.readouterr().out
    assert "2026-05-02" in captured
    assert "prompt_1.txt" in captured


def test_cli_failure_when_no_export(export_cli, capsys: pytest.CaptureFixture[str]) -> None:
    bad = CatstylePromptExportResult(
        date="2026-06-01",
        output_dir="/tmp/y",
        files_written=[],
        selected_candidate=None,
        success=False,
        message="No candidates.",
    )
    old = sys.argv[:]
    try:
        sys.argv = ["export_catstyle_image_prompts.py", "--date", "2026-06-01", "--output-dir", str(Path("/tmp/z"))]
        with patch.object(export_cli, "export_catstyle_image_prompts", return_value=bad):
            assert export_cli.main() == 1
    finally:
        sys.argv = old
    err = capsys.readouterr().err
    assert "No candidates" in err
