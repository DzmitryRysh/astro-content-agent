"""Tests for Catstyle manual approval (service + scripts/aca/approve_catstyle_manual_review.py)."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_manual_review import (
    MANUAL_REVIEW_VERSION,
    REVIEW_QUESTIONS,
    SUGGESTED_DECISIONS,
    approve_catstyle_manual_review,
    load_catstyle_manual_review,
)


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "approve_catstyle_manual_review.py"
    spec = importlib.util.spec_from_file_location("_approve_catstyle_manual_review_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def approve_cli():
    return _load_cli()


def _minimal_manual_review_dict(pkg_dir: Path) -> dict:
    return {
        "version": MANUAL_REVIEW_VERSION,
        "date": "2026-09-01",
        "package_dir": str(pkg_dir.resolve()),
        "quality_status": "ready",
        "quality_score": 90,
        "quality_errors": [],
        "quality_warnings": [],
        "recommended_primary_image": str(pkg_dir / "x.png"),
        "generated_image_paths": [str(pkg_dir / "x.png")],
        "style_reference_image_path": None,
        "hook": "Хук.",
        "caption": "Капция.",
        "compensation": "Комп.",
        "checklist": "Чек.",
        "carousel_slide_text": "Кар.",
        "review_questions": list(REVIEW_QUESTIONS),
        "suggested_decisions": list(SUGGESTED_DECISIONS),
        "approval_status": "pending_review",
        "reviewer_notes": "",
    }


def test_approve_updates_json_notes_and_reviewed_at(tmp_path: Path) -> None:
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "x.png").write_bytes(b"x")

    blob = _minimal_manual_review_dict(pkg_dir)
    (pkg_dir / "manual_review.json").write_text(json.dumps(blob, ensure_ascii=False), encoding="utf-8")

    updated = approve_catstyle_manual_review(
        pkg_dir, "approve", reviewer_notes="Ок к публикации.", overwrite=True
    )

    assert updated.approval_status == "approve"
    assert updated.reviewer_notes == "Ок к публикации."
    assert updated.reviewed_at
    dt = datetime.fromisoformat(updated.reviewed_at.replace("Z", "+00:00"))
    assert dt.tzinfo is not None
    assert dt.utcoffset() is not None

    disk = json.loads((pkg_dir / "manual_review.json").read_text(encoding="utf-8"))
    assert disk["approval_status"] == "approve"
    assert disk["reviewer_notes"] == "Ок к публикации."
    assert disk["reviewed_at"] == updated.reviewed_at


def test_approve_invalid_decision_raises(tmp_path: Path) -> None:
    pkg_dir = tmp_path / "p"
    pkg_dir.mkdir()
    (pkg_dir / "x.png").write_bytes(b"x")
    (pkg_dir / "manual_review.json").write_text(
        json.dumps(_minimal_manual_review_dict(pkg_dir), ensure_ascii=False),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Invalid decision"):
        approve_catstyle_manual_review(pkg_dir, "pending_review", overwrite=True)


def test_approve_md_decision_section_reflects_status(tmp_path: Path) -> None:
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "x.png").write_bytes(b"x")
    (pkg_dir / "manual_review.json").write_text(
        json.dumps(_minimal_manual_review_dict(pkg_dir), ensure_ascii=False),
        encoding="utf-8",
    )

    approve_catstyle_manual_review(pkg_dir, "revise_text", reviewer_notes="Правки текста.", overwrite=True)

    md = (pkg_dir / "manual_review.md").read_text(encoding="utf-8-sig")
    assert "`revise_text`" in md
    assert "Правки текста." in md
    assert "reviewed_at:" in md.lower() or "**reviewed_at:**" in md


def test_cli_runs_minimal_package(approve_cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "x.png").write_bytes(b"x")
    (pkg_dir / "manual_review.json").write_text(
        json.dumps(_minimal_manual_review_dict(pkg_dir), ensure_ascii=False),
        encoding="utf-8",
    )

    old = sys.argv[:]
    try:
        sys.argv = [
            "approve_catstyle_manual_review.py",
            "--package-dir",
            str(pkg_dir),
            "--decision",
            "regenerate_images",
            "--notes",
            "Нужны новые кадры.",
        ]
        assert approve_cli.main() == 0
    finally:
        sys.argv = old

    out = capsys.readouterr().out
    assert "Catstyle manual approval" in out
    assert "regenerate_images" in out
    assert "reviewed_at:" in out

    disk = load_catstyle_manual_review(pkg_dir)
    assert disk.approval_status == "regenerate_images"
    assert disk.reviewer_notes == "Нужны новые кадры."


def test_cli_invalid_decision_exits_error(approve_cli, tmp_path: Path) -> None:
    pkg_dir2 = tmp_path / "pkg2"
    pkg_dir2.mkdir()
    (pkg_dir2 / "x.png").write_bytes(b"x")
    (pkg_dir2 / "manual_review.json").write_text(
        json.dumps(_minimal_manual_review_dict(pkg_dir2), ensure_ascii=False),
        encoding="utf-8",
    )

    old = sys.argv[:]
    try:
        sys.argv = [
            "approve_catstyle_manual_review.py",
            "--package-dir",
            str(pkg_dir2),
            "--decision",
            "not_a_choice",
        ]
        with pytest.raises(SystemExit) as exc:
            approve_cli.main()
        assert exc.value.code == 2
    finally:
        sys.argv = old


def test_no_overwrite_raises_when_blocked(tmp_path: Path) -> None:
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "x.png").write_bytes(b"x")
    (pkg_dir / "manual_review.json").write_text(
        json.dumps(_minimal_manual_review_dict(pkg_dir), ensure_ascii=False),
        encoding="utf-8",
    )
    (pkg_dir / "manual_review.md").write_text("# x\n", encoding="utf-8-sig")

    with pytest.raises(FileExistsError):
        approve_catstyle_manual_review(pkg_dir, "reject", reviewer_notes="", overwrite=False)
