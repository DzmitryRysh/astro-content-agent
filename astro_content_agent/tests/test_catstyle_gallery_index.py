"""Tests for Catstyle gallery index builder."""
from __future__ import annotations

import json
from pathlib import Path

from astro_content_agent.services.content.catstyle_gallery_index import (
    build_catstyle_gallery_index,
    write_catstyle_gallery_index,
)


def _write_handoff(
    root: Path,
    date: str,
    *,
    publish_status: str = "ready_for_manual_publish",
    approval_status: str = "approve",
    caption: str = "Подпись для ручного поста.",
    hook: str = "Хук.",
    include_aspect_in_handoff: bool = False,
) -> Path:
    hdir = root / date
    hdir.mkdir(parents=True, exist_ok=True)
    pkg = root / "pkg" / date
    pkg.mkdir(parents=True, exist_ok=True)
    post = {
        "date": date,
        "planet_a": "Venus",
        "planet_b": "Pluto",
        "aspect_type": "opposition",
        "mode": "tension",
        "aspect_summary": "Venus opposition Pluto (режим: tension)",
        "manual_aspect_override": {
            "enabled": True,
            "planet_a": "Venus",
            "planet_b": "Pluto",
            "aspect_type": "opposition",
            "mode": "tension",
        },
    }
    post_path = pkg / "post_package.json"
    post_path.write_text(json.dumps(post, ensure_ascii=False), encoding="utf-8")

    handoff = {
        "version": "catstyle-publish-handoff-v1",
        "date": date,
        "package_dir": str(pkg.resolve()),
        "source_post_package_path": str(post_path.resolve()),
        "source_manual_review_path": str((pkg / "manual_review.json").resolve()),
        "publish_status": publish_status,
        "approval_status": approval_status,
        "reviewed_at": "2026-10-01T12:00:00+00:00",
        "reviewer_notes": "notes",
        "recommended_primary_image": str((hdir / "hero.png").resolve()),
        "generated_image_paths": [str((hdir / "hero.png").resolve())],
        "caption_final": caption,
        "hook": hook,
        "carousel_text": "car",
        "compensation": "comp",
        "publish_checklist": "check",
        "created_at": "2026-10-01T12:30:00+00:00",
    }
    if include_aspect_in_handoff:
        handoff.update(
            {
                "planet_a": "Venus",
                "planet_b": "Pluto",
                "aspect_type": "opposition",
                "mode": "tension",
                "aspect_summary": "Venus opposition Pluto (режим: tension)",
            }
        )
    (hdir / "hero.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (hdir / "publish_handoff.json").write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")
    return hdir


def test_indexes_multiple_valid_handoffs(tmp_path: Path) -> None:
    root = tmp_path / "catstyle_publish_handoffs"
    _write_handoff(root, "2026-10-01", include_aspect_in_handoff=True)
    _write_handoff(root, "2026-10-02", include_aspect_in_handoff=True)
    idx = build_catstyle_gallery_index(root)
    assert idx.posts_indexed == 2
    assert len(idx.entries) == 2
    assert all(e.publish_status == "ready_for_manual_publish" for e in idx.entries)


def test_skips_not_ready_by_default(tmp_path: Path) -> None:
    root = tmp_path / "catstyle_publish_handoffs"
    _write_handoff(root, "2026-10-03")
    _write_handoff(root, "2026-10-04", publish_status="draft", approval_status="pending_review")
    idx = build_catstyle_gallery_index(root, include_not_ready=False)
    assert idx.posts_indexed == 1
    assert idx.entries[0].date == "2026-10-03"


def test_include_not_ready_includes_them(tmp_path: Path) -> None:
    root = tmp_path / "catstyle_publish_handoffs"
    _write_handoff(root, "2026-10-05")
    _write_handoff(root, "2026-10-06", publish_status="draft", approval_status="pending_review")
    idx = build_catstyle_gallery_index(root, include_not_ready=True)
    dates = {e.date for e in idx.entries}
    assert dates == {"2026-10-05", "2026-10-06"}


def test_extracts_aspect_metadata_from_source_post_package(tmp_path: Path) -> None:
    root = tmp_path / "catstyle_publish_handoffs"
    _write_handoff(root, "2026-10-07", include_aspect_in_handoff=False)
    idx = build_catstyle_gallery_index(root)
    e = idx.entries[0]
    assert e.planet_a == "Venus"
    assert e.planet_b == "Pluto"
    assert e.aspect_type == "opposition"
    assert e.mode == "tension"
    assert e.manual_aspect_override and e.manual_aspect_override.get("enabled") is True


def test_writes_gallery_index_json_and_md(tmp_path: Path) -> None:
    root = tmp_path / "catstyle_publish_handoffs"
    _write_handoff(root, "2026-10-08")
    idx = build_catstyle_gallery_index(root)
    out = tmp_path / "out"
    names = write_catstyle_gallery_index(idx, out, overwrite=True)
    assert set(names) == {"gallery_index.json", "gallery_index.md"}
    assert (out / "gallery_index.json").is_file()
    assert (out / "gallery_index.md").is_file()


def test_gallery_detects_publish_record_and_markdown_shows_published_manual(tmp_path: Path) -> None:
    root = tmp_path / "catstyle_publish_handoffs"
    hdir = _write_handoff(root, "2026-10-09")
    rec = {
        "version": "catstyle-published-record-v1",
        "publish_state": "published_manual",
        "published_at": "2026-10-09T19:30:00+00:00",
        "handoff_dir": str(hdir.resolve()),
        "source_publish_handoff_path": str((hdir / "publish_handoff.json").resolve()),
        "recommended_primary_image": str((hdir / "hero.png").resolve()),
        "caption_final": "Подпись",
        "hook": "Хук",
        "instagram_url": "https://instagram.com/p/demo",
        "notes": "posted",
    }
    (hdir / "publish_record.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    idx = build_catstyle_gallery_index(root)
    assert idx.entries[0].publish_state == "published_manual"
    assert idx.entries[0].published_at == "2026-10-09T19:30:00+00:00"
    assert idx.entries[0].instagram_url == "https://instagram.com/p/demo"
    out = tmp_path / "g"
    write_catstyle_gallery_index(idx, out, overwrite=True)
    md = (out / "gallery_index.md").read_text(encoding="utf-8-sig")
    assert "published_manual" in md
