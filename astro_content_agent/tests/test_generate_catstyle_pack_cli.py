"""Tests for scripts/aca/generate_catstyle_pack.py CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_catstyle_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    cli_path = repo / "scripts" / "aca" / "generate_catstyle_pack.py"
    spec = importlib.util.spec_from_file_location("_generate_catstyle_pack_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def catstyle_cli():
    return _load_catstyle_cli()


def test_cli_prints_pluto_venus_pack(catstyle_cli, capsys: pytest.CaptureFixture[str]) -> None:
    monkey_argv = [
        "generate_catstyle_pack.py",
        "--planet-a",
        "Pluto",
        "--planet-b",
        "Venus",
        "--aspect-type",
        "conjunction",
        "--mode",
        "tension",
    ]
    old = sys.argv[:]
    try:
        sys.argv = monkey_argv
        assert catstyle_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Pluto" in out and "Venus" in out
    assert "conjunction" in out
    assert "Image prompt 1" in out or "--- Image prompt 1 ---" in out
    assert "thick black outlines" in out.lower()


def test_cli_writes_json_when_output_provided(catstyle_cli, tmp_path: Path) -> None:
    out_file = tmp_path / "pack.json"
    old = sys.argv[:]
    try:
        sys.argv = [
            "generate_catstyle_pack.py",
            "--planet-a",
            "Pluto",
            "--planet-b",
            "Venus",
            "--aspect-type",
            "square",
            "--mode",
            "mixed",
            "--output",
            str(out_file),
        ]
        assert catstyle_cli.main() == 0
    finally:
        sys.argv = old
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["planet_a"] == "Pluto"
    assert data["planet_b"] == "Venus"
    assert data["aspect_type"] == "square"
    assert data["mode"] == "mixed"
    assert isinstance(data["image_prompts"], list)
    assert len(data["image_prompts"]) == 4
    assert "animation_prompt" in data and data["animation_prompt"]
    assert "negative_prompt" in data and data["negative_prompt"]
    assert "carousel_idea" in data and data["carousel_idea"]


def test_cli_variants_count_respected(catstyle_cli, tmp_path: Path) -> None:
    out_file = tmp_path / "v.json"
    old = sys.argv[:]
    try:
        sys.argv = [
            "generate_catstyle_pack.py",
            "--planet-a",
            "Jupiter",
            "--planet-b",
            "Mercury",
            "--aspect-type",
            "trine",
            "--mode",
            "tension",
            "--variants-count",
            "2",
            "--output",
            str(out_file),
        ]
        assert catstyle_cli.main() == 0
    finally:
        sys.argv = old
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(data["image_prompts"]) == 2


def test_cli_unsupported_pair_exits_nonzero(catstyle_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = [
            "generate_catstyle_pack.py",
            "--planet-a",
            "Sun",
            "--planet-b",
            "Mars",
            "--aspect-type",
            "conjunction",
            "--mode",
            "tension",
        ]
        assert catstyle_cli.main() == 1
    finally:
        sys.argv = old
    err = capsys.readouterr().err
    assert "No Catstyle content" in err or "outer-to-personal" in err


def test_cli_accepts_valid_skin_b(catstyle_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = [
            "generate_catstyle_pack.py",
            "--planet-a",
            "Jupiter",
            "--planet-b",
            "Mars",
            "--aspect-type",
            "square",
            "--mode",
            "tension",
            "--skin-b",
            "spartan_king",
        ]
        assert catstyle_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Spartan King" in out or "spartan" in out.lower()
    assert "Skins:" in out


def test_cli_rejects_invalid_skin(catstyle_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = [
            "generate_catstyle_pack.py",
            "--planet-a",
            "Jupiter",
            "--planet-b",
            "Mars",
            "--aspect-type",
            "square",
            "--mode",
            "tension",
            "--skin-b",
            "not_a_skin",
        ]
        assert catstyle_cli.main() == 1
    finally:
        sys.argv = old
    err = capsys.readouterr().err
    assert "No character skin" in err or "skin" in err.lower()


def test_cli_default_variants_count_is_four(catstyle_cli, tmp_path: Path) -> None:
    """Omitting --variants-count uses model default (4)."""
    out_file = tmp_path / "default_variants.json"
    old = sys.argv[:]
    try:
        sys.argv = [
            "generate_catstyle_pack.py",
            "--planet-a",
            "Moon",
            "--planet-b",
            "Uranus",
            "--aspect-type",
            "opposition",
            "--mode",
            "compensation",
            "--output",
            str(out_file),
        ]
        assert catstyle_cli.main() == 0
    finally:
        sys.argv = old
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(data["image_prompts"]) == 4
