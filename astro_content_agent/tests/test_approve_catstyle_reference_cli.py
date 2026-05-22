"""Tests for Catstyle reference approval service + CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from astro_content_agent.content.catstyle.approved_reference_registry import (
    approved_references_json_path,
    normalize_pair_key,
    read_registry_entries,
    resolve_approved_reference,
)
from astro_content_agent.services.content import catstyle_reference_approval as approval_service
from astro_content_agent.services.content.catstyle_reference_image_validation import PNG_SIGNATURE
from astro_content_agent.tests.catstyle_reference_test_helpers import (
    write_png_signature_stub,
    write_valid_reference_png,
)


def _load_cli(script_name: str, module_name: str):
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / script_name
    spec = importlib.util.spec_from_file_location(module_name, p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_seed_registry(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"version":"catstyle-approved-references-v1","entries":[]}\n', encoding="utf-8")


def _write_png(path: Path, *, color: tuple[int, int, int] = (40, 80, 120)) -> None:
    write_valid_reference_png(path, color=color)


def test_approval_service_copies_image_and_creates_registry_entry(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    registry_path = repo / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"
    _write_seed_registry(registry_path)
    src = repo / "catstyle_image_jobs" / "x.png"
    _write_png(src)

    res = approval_service.approve_catstyle_reference(
        source_image=src,
        planet_a="Saturn",
        planet_b="Moon",
        aspect_type="square",
        mode="tension",
        label="Moon Saturn approved cold pressure reference",
        notes="Best frame.",
        repo_root=repo,
        registry_json_path=registry_path,
    )
    assert res.target_image == "references/catstyle_moon_saturn_square_tension_approved.png"
    assert (repo / "references" / "catstyle_moon_saturn_square_tension_approved.png").is_file()

    rows = read_registry_entries(registry_path)
    assert len(rows) == 1
    assert normalize_pair_key(rows[0].planet_a, rows[0].planet_b, rows[0].aspect_type, rows[0].mode) == normalize_pair_key(
        "Moon", "Saturn", "square", "tension"
    )
    hit = resolve_approved_reference("Moon", "Saturn", "square", "tension", registry=rows)
    assert hit is not None
    assert "catstyle_moon_saturn_square_tension_approved.png" in hit.image_path.replace("\\", "/")


def test_approval_service_duplicate_without_overwrite_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    registry_path = repo / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"
    _write_seed_registry(registry_path)
    src = repo / "a.png"
    _write_png(src)
    approval_service.approve_catstyle_reference(
        source_image=src,
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        repo_root=repo,
        registry_json_path=registry_path,
    )
    with pytest.raises(approval_service.CatstyleReferenceApprovalError, match="already exists"):
        approval_service.approve_catstyle_reference(
            source_image=src,
            planet_a="Saturn",
            planet_b="Moon",
            aspect_type="square",
            mode="tension",
            repo_root=repo,
            registry_json_path=registry_path,
        )


def test_approval_service_overwrite_updates_existing_entry(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    registry_path = repo / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"
    _write_seed_registry(registry_path)
    src1 = repo / "a.png"
    src2 = repo / "b.png"
    _write_png(src1, color=(10, 20, 30))
    _write_png(src2, color=(200, 50, 50))
    approval_service.approve_catstyle_reference(
        source_image=src1,
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        label="v1",
        repo_root=repo,
        registry_json_path=registry_path,
    )
    res2 = approval_service.approve_catstyle_reference(
        source_image=src2,
        planet_a="Saturn",
        planet_b="Moon",
        aspect_type="square",
        mode="tension",
        label="v2",
        notes="overwrite",
        overwrite=True,
        repo_root=repo,
        registry_json_path=registry_path,
    )
    assert res2.overwrite is True
    rows = read_registry_entries(registry_path)
    assert len(rows) == 1
    assert rows[0].label == "v2"
    target = repo / "references" / "catstyle_moon_saturn_square_tension_approved.png"
    assert target.stat().st_size > 10_000
    assert target.read_bytes()[:8] == PNG_SIGNATURE
    assert target.read_bytes() != src1.read_bytes()


def test_approval_rejects_stub_png_signature(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    registry_path = repo / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"
    _write_seed_registry(registry_path)
    stub = repo / "stub.png"
    write_png_signature_stub(stub)
    with pytest.raises(approval_service.CatstyleReferenceApprovalError, match="8-byte PNG signature stub"):
        approval_service.approve_catstyle_reference(
            source_image=stub,
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            repo_root=repo,
            registry_json_path=registry_path,
        )


def test_production_reference_not_overwritten_by_invalid_source(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    registry_path = repo / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"
    _write_seed_registry(registry_path)
    target = repo / "references" / "catstyle_sun_uranus_conjunction_tension_approved.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    write_valid_reference_png(target, color=(1, 2, 3))
    before = target.read_bytes()
    stub = repo / "bad.png"
    write_png_signature_stub(stub)
    with pytest.raises(approval_service.CatstyleReferenceApprovalError, match="8-byte PNG signature stub"):
        approval_service.approve_catstyle_reference(
            source_image=stub,
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            overwrite=True,
            repo_root=repo,
            registry_json_path=registry_path,
        )
    assert target.read_bytes() == before


def test_approve_cli_and_list_cli_with_temp_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    registry_path = repo / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"
    _write_seed_registry(registry_path)
    src = repo / "generated" / "sample.png"
    _write_png(src)

    # Service module uses imported function names; patch there directly.
    monkeypatch.setattr(approval_service, "catstyle_repo_root", lambda: repo)
    monkeypatch.setattr(approval_service, "approved_references_json_path", lambda: registry_path)

    approve_cli = _load_cli("approve_catstyle_reference.py", "_approve_catstyle_reference_cli")
    old = sys.argv[:]
    try:
        sys.argv = [
            "approve_catstyle_reference.py",
            "--image-path",
            str(src),
            "--planet-a",
            "Moon",
            "--planet-b",
            "Saturn",
            "--aspect-type",
            "square",
            "--mode",
            "tension",
            "--label",
            "Moon Saturn approved cold pressure reference",
            "--notes",
            "Best frame.",
            "--overwrite",
        ]
        assert approve_cli.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "Catstyle reference approval" in out
    assert "catstyle_moon_saturn_square_tension_approved.png" in out

    # list CLI reads registry module helper; patch to temp registry path.
    import astro_content_agent.content.catstyle.approved_reference_registry as reg_mod

    monkeypatch.setattr(reg_mod, "approved_references_json_path", lambda: registry_path)
    list_cli = _load_cli("list_catstyle_approved_references.py", "_list_catstyle_approved_references_cli_tmp")
    old2 = sys.argv[:]
    try:
        sys.argv = ["list_catstyle_approved_references.py", "--json"]
        assert list_cli.main() == 0
    finally:
        sys.argv = old2
    data = json.loads(capsys.readouterr().out)
    keys = {row["registry_key"] for row in data}
    assert "moon_saturn_square_tension_v1" in keys

