"""Tests for scripts/aca/rank_catstyle_candidates.py CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_rank_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    cli_path = repo / "scripts" / "aca" / "rank_catstyle_candidates.py"
    spec = importlib.util.spec_from_file_location("_rank_catstyle_candidates_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def rank_cli():
    return _load_rank_cli()


def test_cli_prints_ranked_result(rank_cli, capsys: pytest.CaptureFixture[str]) -> None:
    payload = json.dumps(
        [
            {"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "conjunction"},
            {"planet_a": "Jupiter", "planet_b": "Mercury", "aspect_type": "trine"},
        ]
    )
    old = sys.argv[:]
    try:
        sys.argv = ["rank_catstyle_candidates.py", "--candidates-json", payload]
        assert rank_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Pluto" in out and "Venus" in out
    assert "Catstyle candidate ranking" in out
    assert "total=" in out


def test_cli_writes_json_output(rank_cli, tmp_path: Path) -> None:
    out_file = tmp_path / "ranked.json"
    payload = json.dumps([{"planet_a": "Moon", "planet_b": "Uranus", "aspect_type": "square"}])
    old = sys.argv[:]
    try:
        sys.argv = [
            "rank_catstyle_candidates.py",
            "--candidates-json",
            payload,
            "--output",
            str(out_file),
        ]
        assert rank_cli.main() == 0
    finally:
        sys.argv = old
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert "ranked" in data and "unsupported" in data
    assert len(data["ranked"]) == 1
    assert data["ranked"][0]["planet_a"] in ("Moon", "Uranus")


def test_cli_shows_unsupported_section(rank_cli, capsys: pytest.CaptureFixture[str]) -> None:
    payload = json.dumps(
        [
            {"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "conjunction"},
            {"planet_a": "Sun", "planet_b": "Mars", "aspect_type": "square"},
        ]
    )
    old = sys.argv[:]
    try:
        sys.argv = ["rank_catstyle_candidates.py", "--candidates-json", payload]
        assert rank_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Unsupported" in out
    assert "Sun" in out and "Mars" in out


def test_cli_reads_input_file(rank_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    inp = tmp_path / "in.json"
    inp.write_text(
        json.dumps([{"planet_a": "Saturn", "planet_b": "Venus", "aspect_type": "trine"}]),
        encoding="utf-8",
    )
    old = sys.argv[:]
    try:
        sys.argv = ["rank_catstyle_candidates.py", "--input", str(inp)]
        assert rank_cli.main() == 0
    finally:
        sys.argv = old
    assert "Saturn" in capsys.readouterr().out


def test_cli_reads_input_file_with_utf8_bom(rank_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """PowerShell Set-Content -Encoding UTF8 may write UTF-8 with BOM; utf-8-sig strips it for json.loads."""
    inp = tmp_path / "in_bom.json"
    body = json.dumps([{"planet_a": "Pluto", "planet_b": "Venus", "aspect_type": "conjunction"}])
    inp.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
    old = sys.argv[:]
    try:
        sys.argv = ["rank_catstyle_candidates.py", "--input", str(inp)]
        assert rank_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Pluto" in out and "Venus" in out
    assert "Invalid JSON" not in out
