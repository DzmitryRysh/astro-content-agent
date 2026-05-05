"""Tests for scripts/aca/execute_catstyle_image_jobs.py CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from astro_content_agent.core.config import get_settings
from astro_content_agent.services.content.catstyle_image_providers import (
    OpenAICatstyleImageProvider,
    get_catstyle_image_provider,
)

_MINI_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "execute_catstyle_image_jobs.py"
    spec = importlib.util.spec_from_file_location("_execute_catstyle_image_jobs_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def jobs_cli():
    return _load_cli()


@pytest.fixture(autouse=True)
def _reset_settings_cache_cli() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _manifest(tmp_path: Path) -> Path:
    mp = tmp_path / "image_generation_jobs.json"
    mp.write_text(
        json.dumps(
            {
                "version": "catstyle-image-generation-jobs-v0",
                "jobs": [
                    {
                        "job_id": "j1",
                        "suggested_output_name": "a.png",
                        "prompt_index": 1,
                        "prompt_text": "hello",
                        "negative_prompt": "n",
                        "animation_prompt": "a",
                        "carousel_idea": "c",
                        "status": "pending",
                        "date": "2026-05-02",
                        "planet_a": "A",
                        "planet_b": "B",
                        "aspect_type": "sq",
                        "editorial_profile": "charged",
                        "mode": "t",
                        "source": "s",
                        "total_score": 1,
                        "variant_index": 0,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return mp


def test_generic_cli_runs_stub_provider(jobs_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    mp = _manifest(tmp_path)
    out = tmp_path / "gen"
    old = sys.argv[:]
    try:
        sys.argv = [
            "execute_catstyle_image_jobs.py",
            "--manifest",
            str(mp),
            "--provider",
            "stub",
            "--output-dir",
            str(out),
        ]
        assert jobs_cli.main() == 0
    finally:
        sys.argv = old
    out_cap = capsys.readouterr().out
    assert "provider:" in out_cap.lower()
    assert "stub" in out_cap.lower()
    assert (out / "generated_stub_01.txt").is_file()


def test_generic_cli_accepts_openai_image_provider(
    jobs_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_client = MagicMock()
    mock_client.images.generate.return_value = SimpleNamespace(
        data=[SimpleNamespace(b64_json=_MINI_PNG_B64, url=None)]
    )

    def fake_get(name: str):
        if name == "openai_image":
            return OpenAICatstyleImageProvider(client=mock_client)
        return get_catstyle_image_provider(name)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-unit-test")
    monkeypatch.setattr(
        "astro_content_agent.services.content.catstyle_image_generation_executor.get_catstyle_image_provider",
        fake_get,
    )
    mp = _manifest(tmp_path)
    out = tmp_path / "gen_openai"
    old = sys.argv[:]
    try:
        sys.argv = [
            "execute_catstyle_image_jobs.py",
            "--manifest",
            str(mp),
            "--provider",
            "openai_image",
            "--output-dir",
            str(out),
        ]
        assert jobs_cli.main() == 0
    finally:
        sys.argv = old
    out_cap = capsys.readouterr().out
    assert "openai_image" in out_cap.lower()
    assert "output_files:" in out_cap.lower()
    assert (out / "a.png").is_file()
