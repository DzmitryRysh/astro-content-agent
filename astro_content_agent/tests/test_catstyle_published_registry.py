"""Tests for Catstyle published registry service."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_published_registry import (
    CatstylePublishedRegistryError,
    mark_catstyle_handoff_published,
    write_catstyle_published_record,
)


def _write_handoff(tmp_path: Path, *, status: str = "ready_for_manual_publish") -> Path:
    hdir = tmp_path / "catstyle_publish_handoffs" / "2026-11-01"
    hdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": "2026-11-01",
        "publish_status": status,
        "approval_status": "approve",
        "recommended_primary_image": str((hdir / "hero.png").resolve()),
        "caption_final": "Финальная подпись.",
        "hook": "Хук.",
    }
    (hdir / "hero.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (hdir / "publish_handoff.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return hdir


def test_valid_handoff_creates_publish_record_files(tmp_path: Path) -> None:
    hdir = _write_handoff(tmp_path)
    rec = mark_catstyle_handoff_published(
        hdir,
        instagram_url="https://instagram.com/p/abc123",
        notes="posted manually",
    )
    names = write_catstyle_published_record(rec, hdir, overwrite=False)
    assert set(names) == {"publish_record.json", "publish_record.md"}
    assert (hdir / "publish_record.json").is_file()
    assert (hdir / "publish_record.md").is_file()
    blob = json.loads((hdir / "publish_record.json").read_text(encoding="utf-8"))
    assert blob["publish_state"] == "published_manual"
    assert blob["instagram_url"] == "https://instagram.com/p/abc123"
    assert blob["notes"] == "posted manually"


def test_missing_handoff_fails(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Missing publish_handoff.json"):
        mark_catstyle_handoff_published(tmp_path / "missing")


def test_non_ready_handoff_fails(tmp_path: Path) -> None:
    hdir = _write_handoff(tmp_path, status="draft")
    with pytest.raises(CatstylePublishedRegistryError, match="ready_for_manual_publish"):
        mark_catstyle_handoff_published(hdir)


def test_published_at_is_timezone_aware_utc_iso(tmp_path: Path) -> None:
    hdir = _write_handoff(tmp_path)
    rec = mark_catstyle_handoff_published(hdir)
    dt = datetime.fromisoformat(rec.published_at.replace("Z", "+00:00"))
    assert dt.tzinfo is not None
    assert dt.utcoffset() == timezone.utc.utcoffset(dt)
