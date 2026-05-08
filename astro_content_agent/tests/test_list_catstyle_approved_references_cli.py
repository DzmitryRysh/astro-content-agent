"""Tests for scripts/aca/list_catstyle_approved_references.py CLI."""
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
    p = repo / "scripts" / "aca" / "list_catstyle_approved_references.py"
    spec = importlib.util.spec_from_file_location("_list_catstyle_approved_references_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def ref_cli():
    return _load_cli()


def test_list_cli_human_output(ref_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["list_catstyle_approved_references.py"]
        assert ref_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Catstyle approved reference registry" in out
    assert "moon_saturn_square_tension_v1" in out
    assert "references/catstyle_moon_saturn_square_tension_approved.png" in out


def test_list_cli_json(ref_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["list_catstyle_approved_references.py", "--json"]
        assert ref_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert isinstance(data, list)
    keys = {row["registry_key"] for row in data}
    assert "jupiter_mars_square_tension_v1" in keys
    assert all("image_path_absolute" in row for row in data)
