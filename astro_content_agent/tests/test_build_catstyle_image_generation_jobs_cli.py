"""Tests for scripts/aca/build_catstyle_image_generation_jobs.py CLI."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    CatstyleImageGenerationJobsResult,
)


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "build_catstyle_image_generation_jobs.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_image_generation_jobs_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def jobs_cli():
    return _load_cli()


def _minimal_result() -> CatstyleImageGenerationJobsResult:
    from astro_content_agent.services.content.catstyle_image_generation_jobs import CatstyleImageGenJob

    j = CatstyleImageGenJob(
        job_id="catstyle-2026-05-02-001",
        date="2026-05-02",
        planet_a="A",
        planet_b="B",
        aspect_type="trine",
        editorial_profile="charged",
        mode="mixed",
        source="seed",
        total_score=30,
        prompt_index=1,
        variant_index=0,
        prompt_text="p1",
        negative_prompt="n",
        animation_prompt="a",
        carousel_idea="c",
        suggested_output_name="out.png",
    )
    return CatstyleImageGenerationJobsResult(
        date="2026-05-02",
        editorial_profile="charged",
        selected_candidate={"planet_a": "A", "planet_b": "B", "aspect_type": "trine", "total_score": 30},
        jobs=[j],
        output_dir="/tmp/x",
        files_written=["image_generation_jobs.json", "job_01_prompt.txt"],
        style_reference_meta={"source": "none"},
    )


def test_cli_invalid_date(jobs_cli, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = ["build_catstyle_image_generation_jobs.py", "--date", "bad-date"]
        assert jobs_cli.main() == 1
    finally:
        sys.argv = old
    assert "YYYY" in capsys.readouterr().err or "Date" in capsys.readouterr().err


def test_cli_writes_via_mock(jobs_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "cli_out"
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_image_generation_jobs.py",
            "--date",
            "2026-05-02",
            "--output-dir",
            str(out),
        ]
        with patch.object(jobs_cli, "build_catstyle_image_generation_jobs", return_value=_minimal_result()):
            assert jobs_cli.main() == 0
    finally:
        sys.argv = old
    captured = capsys.readouterr().out
    assert "2026-05-02" in captured
    assert "jobs count" in captured.lower()
    assert "1" in captured


def test_cli_partial_manual_override_exits_error(jobs_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_image_generation_jobs.py",
            "--date",
            "2026-05-02",
            "--output-dir",
            str(tmp_path / "out"),
            "--planet-a",
            "Pluto",
        ]
        assert jobs_cli.main() == 1
    finally:
        sys.argv = old
    err = capsys.readouterr().err
    assert "four flags" in err or "Manual aspect override" in err


def test_cli_passes_manual_override_kwargs(jobs_cli, tmp_path: Path) -> None:
    out = tmp_path / "cli_ov"
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_image_generation_jobs.py",
            "--date",
            "2026-05-02",
            "--output-dir",
            str(out),
            "--planet-a",
            "Pluto",
            "--planet-b",
            "Mars",
            "--aspect-type",
            "square",
            "--mode",
            "tension",
        ]
        with patch.object(jobs_cli, "build_catstyle_image_generation_jobs", return_value=_minimal_result()) as m:
            assert jobs_cli.main() == 0
    finally:
        sys.argv = old
    kw = m.call_args.kwargs
    assert kw.get("planet_a_override") == "Pluto"
    assert kw.get("planet_b_override") == "Mars"
    assert kw.get("aspect_type_override") == "square"
    assert kw.get("mode_override") == "tension"


def test_cli_passes_style_reference_image_arg(jobs_cli, tmp_path: Path) -> None:
    out = tmp_path / "cli_out"
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_image_generation_jobs.py",
            "--date",
            "2026-05-02",
            "--output-dir",
            str(out),
            "--style-reference-image",
            str(tmp_path / "ref.png"),
        ]
        with patch.object(jobs_cli, "build_catstyle_image_generation_jobs", return_value=_minimal_result()) as m:
            assert jobs_cli.main() == 0
    finally:
        sys.argv = old
    assert m.call_args.kwargs.get("style_reference_image_path") == str(tmp_path / "ref.png")


def test_cli_passes_disable_approved_reference_auto(jobs_cli, tmp_path: Path) -> None:
    out = tmp_path / "cli_dis"
    old = sys.argv[:]
    try:
        sys.argv = [
            "build_catstyle_image_generation_jobs.py",
            "--date",
            "2026-05-02",
            "--output-dir",
            str(out),
            "--disable-approved-reference-auto",
        ]
        with patch.object(jobs_cli, "build_catstyle_image_generation_jobs", return_value=_minimal_result()) as m:
            assert jobs_cli.main() == 0
    finally:
        sys.argv = old
    assert m.call_args.kwargs.get("disable_approved_reference_auto") is True
