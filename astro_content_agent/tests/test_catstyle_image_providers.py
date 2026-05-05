"""Tests for Catstyle image provider abstraction v0."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_image_providers import (
    StubCatstyleImageProvider,
    get_catstyle_image_provider,
)


def _job(seq: int = 1) -> dict:
    return {
        "job_id": f"j-{seq}",
        "suggested_output_name": f"out{seq}.png",
        "prompt_index": seq,
        "prompt_text": "hello " * 50,
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


def test_get_provider_unsupported_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported Catstyle image provider"):
        get_catstyle_image_provider("openai")
