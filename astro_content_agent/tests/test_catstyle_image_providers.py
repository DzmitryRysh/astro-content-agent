"""Tests for Catstyle image providers (stub + OpenAI Images)."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from astro_content_agent.core.config import get_settings
from astro_content_agent.services.content.catstyle_image_providers import (
    OpenAICatstyleImageProvider,
    StubCatstyleImageProvider,
    get_catstyle_image_provider,
)
from astro_content_agent.services.content import catstyle_image_providers as cap

# 1x1 transparent PNG
_MINI_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _job(seq: int = 1) -> dict:
    return {
        "job_id": f"j-{seq}",
        "suggested_output_name": f"out{seq}.png",
        "prompt_index": seq,
        "prompt_text": "hello " * 50,
        "status": "pending",
        "_stub_output_seq": seq,
    }


def _openai_job(seq: int = 1) -> dict:
    return {
        "job_id": f"j-{seq}",
        "suggested_output_name": f"out{seq}.png",
        "prompt_index": seq,
        "prompt_text": "A simple test image of a red circle on white.",
        "negative_prompt": "text, watermark",
        "status": "pending",
        "_stub_output_seq": seq,
    }


def test_stub_provider_writes_json_stub(tmp_path: Path) -> None:
    p = StubCatstyleImageProvider()
    out = tmp_path / "o"
    out.mkdir()
    r = p.generate(_job(1), out, overwrite=False)
    assert r.provider == "stub"
    assert r.status == "generated_stub"
    assert r.output_filename == "generated_stub_01.txt"
    assert (out / "generated_stub_01.txt").is_file()
    blob = json.loads((out / "generated_stub_01.txt").read_text(encoding="utf-8"))
    assert blob["note"] == "Stub only. No image API was called."


def test_stub_provider_skips_existing_without_overwrite(tmp_path: Path) -> None:
    p = StubCatstyleImageProvider()
    out = tmp_path / "o"
    out.mkdir()
    p.generate(_job(1), out, overwrite=False)
    r2 = p.generate(_job(1), out, overwrite=False)
    assert r2.status == "skipped_existing"


def test_stub_provider_overwrites_when_flag_true(tmp_path: Path) -> None:
    p = StubCatstyleImageProvider()
    out = tmp_path / "o"
    out.mkdir()
    p.generate(_job(1), out, overwrite=False)
    first = (out / "generated_stub_01.txt").read_text(encoding="utf-8")
    job2 = {**_job(1), "prompt_text": "different content " * 30}
    r2 = p.generate(job2, out, overwrite=True)
    assert r2.status == "generated_stub"
    second = (out / "generated_stub_01.txt").read_text(encoding="utf-8")
    assert first != second
    assert "different" in second


def test_get_provider_stub() -> None:
    prov = get_catstyle_image_provider("stub")
    assert isinstance(prov, StubCatstyleImageProvider)


def test_get_provider_openai_image() -> None:
    prov = get_catstyle_image_provider("openai_image")
    assert isinstance(prov, OpenAICatstyleImageProvider)


def test_get_provider_unsupported_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported Catstyle image provider"):
        get_catstyle_image_provider("openai")


def test_openai_writes_png_from_mocked_b64(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-unit-test")
    get_settings.cache_clear()
    mock_client = MagicMock()
    mock_client.images.generate.return_value = SimpleNamespace(
        data=[SimpleNamespace(b64_json=_MINI_PNG_B64, url=None)]
    )
    p = OpenAICatstyleImageProvider(client=mock_client)
    out = tmp_path / "g"
    out.mkdir()
    r = p.generate(_openai_job(1), out, overwrite=False)
    assert r.provider == "openai_image"
    assert r.status == "generated"
    assert r.output_filename == "out1.png"
    dest = out / "out1.png"
    assert dest.is_file()
    assert dest.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    mock_client.images.generate.assert_called_once()
    call_kw = mock_client.images.generate.call_args.kwargs
    assert call_kw["model"]
    assert "Avoid / negative guidance:" in call_kw["prompt"]


def test_openai_missing_api_key_returns_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Empty env overrides any OPENAI_API_KEY from .env (delenv alone would fall back to .env).
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    p = OpenAICatstyleImageProvider(client=MagicMock())
    r = p.generate(_openai_job(1), tmp_path, overwrite=False)
    assert r.status == "failed"
    assert r.message and "OPENAI_API_KEY" in r.message
    assert (tmp_path / "out1.png").is_file() is False


def test_openai_skips_existing_without_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-unit-test")
    get_settings.cache_clear()
    mock_client = MagicMock()
    mock_client.images.generate.return_value = SimpleNamespace(
        data=[SimpleNamespace(b64_json=_MINI_PNG_B64, url=None)]
    )
    p = OpenAICatstyleImageProvider(client=mock_client)
    out = tmp_path / "g"
    out.mkdir()
    p.generate(_openai_job(1), out, overwrite=False)
    mock_client.images.generate.reset_mock()
    r2 = p.generate(_openai_job(1), out, overwrite=False)
    assert r2.status == "skipped_existing"
    mock_client.images.generate.assert_not_called()


def test_openai_overwrites_when_flag_true(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-unit-test")
    get_settings.cache_clear()
    mock_client = MagicMock()
    mock_client.images.generate.return_value = SimpleNamespace(
        data=[SimpleNamespace(b64_json=_MINI_PNG_B64, url=None)]
    )
    p = OpenAICatstyleImageProvider(client=mock_client)
    out = tmp_path / "g"
    out.mkdir()
    p.generate(_openai_job(1), out, overwrite=False)
    mock_client.images.generate.reset_mock()
    r2 = p.generate(_openai_job(1), out, overwrite=True)
    assert r2.status == "generated"
    assert mock_client.images.generate.call_count == 1


def test_openai_api_error_sanitizes_secrets_in_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-unit-test")
    get_settings.cache_clear()
    mock_client = MagicMock()
    secret_token = "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890abcdef"
    mock_client.images.generate.side_effect = RuntimeError(f"upstream {secret_token} boom")

    p = OpenAICatstyleImageProvider(client=mock_client)
    r = p.generate(_openai_job(1), tmp_path, overwrite=False)
    assert r.status == "failed"
    assert secret_token not in (r.message or "")
    assert "REDACTED" in (r.message or "")


def test_sanitize_error_message_strips_key_like_strings() -> None:
    raw = "Error: sk-proj-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa token leaked"
    out = cap._sanitize_error_message(raw)
    assert "sk-proj" not in out
    assert "REDACTED" in out
