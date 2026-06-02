"""Tests for Catstyle per-planet approved character references (v1)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
    APPROVED_PLANET_REFERENCE_LOCK_MARKER,
    ApprovedPlanetReferenceEntry,
    build_job_reference_images,
    format_catstyle_modular_reference_roles_prefix,
    planet_reference_target_relpath,
    read_planet_registry_entries,
    resolve_approved_planet_reference,
    resolve_planet_reference,
    write_planet_registry_entries,
)
from astro_content_agent.core.config import get_settings
from astro_content_agent.tests.catstyle_reference_test_helpers import write_valid_reference_png
from astro_content_agent.services.content import catstyle_image_providers as cap
from astro_content_agent.services.content.catstyle_image_generation_executor import execute_catstyle_image_jobs
from astro_content_agent.services.content.catstyle_image_generation_jobs import build_catstyle_image_generation_jobs
from astro_content_agent.services.content.catstyle_planet_reference_approval import approve_catstyle_planet_reference
from astro_content_agent.services.content.catstyle_image_providers import OpenAICatstyleImageProvider

_MINI_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

_REGISTERED_PLANETS = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
]


def test_resolve_highest_priority_active_reference(tmp_path: Path) -> None:
    reg = tmp_path / "planet_refs.json"
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="saturn_low",
                planet="Saturn",
                image_path="references/saturn_low.png",
                priority=10,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="saturn_high",
                planet="Saturn",
                image_path="references/saturn_high.png",
                priority=100,
                active=True,
            ),
        ],
    )
    hit = resolve_approved_planet_reference("Saturn", registry=read_planet_registry_entries(reg))
    assert hit is not None
    assert hit.registry_key == "saturn_high"


def test_inactive_planet_reference_ignored(tmp_path: Path) -> None:
    reg = tmp_path / "planet_refs.json"
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="moon_off",
                planet="Moon",
                image_path="references/moon_off.png",
                priority=200,
                active=False,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="moon_on",
                planet="Moon",
                image_path="references/moon_on.png",
                priority=50,
                active=True,
            ),
        ],
    )
    hit = resolve_approved_planet_reference("Moon", registry=read_planet_registry_entries(reg))
    assert hit is not None
    assert hit.registry_key == "moon_on"


def test_approve_writes_registry_and_deterministic_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "references").mkdir()
    reg = repo / "astro_content_agent" / "content" / "catstyle" / "approved_planet_references.json"
    reg.parent.mkdir(parents=True)
    reg.write_text('{"version":"catstyle-approved-planet-reference-v1","entries":[]}\n', encoding="utf-8")
    src = tmp_path / "saturn_src.png"
    write_valid_reference_png(src)
    result = approve_catstyle_planet_reference(
        source_image=src,
        planet="Saturn",
        registry_key="cold_authority_v1",
        label="Cold Saturn",
        repo_root=repo,
        registry_json_path=reg,
    )
    expected_rel = planet_reference_target_relpath("Saturn", "cold_authority_v1")
    assert result.target_image == expected_rel
    assert (repo / expected_rel).is_file()
    entries = read_planet_registry_entries(reg)
    assert len(entries) == 1
    assert entries[0].planet == "Saturn"
    assert entries[0].registry_key == "cold_authority_v1"


def test_build_jobs_manifest_includes_planet_references_when_files_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reg = tmp_path / "approved_planet_references.json"
    moon_png = tmp_path / "moon.png"
    saturn_png = tmp_path / "saturn.png"
    moon_png.write_bytes(b"m")
    saturn_png.write_bytes(b"s")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="moon_v1",
                planet="Moon",
                image_path=str(moon_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="saturn_v1",
                planet="Saturn",
                image_path=str(saturn_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    out = tmp_path / "jobs"
    r = build_catstyle_image_generation_jobs(
        date(2026, 5, 20),
        planet_a_override="Moon",
        planet_b_override="Saturn",
        aspect_type_override="square",
        mode_override="tension",
        disable_approved_reference_auto=True,
        disable_arena_reference_auto=True,
        use_planet_reference_auto=True,
        render_style_profile_key="premium_cg_keyart_v1",
        output_dir=out,
        jobs_count=1,
    )
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    pr = manifest["planet_references"]
    assert pr["planet_a"]["used"] is True
    assert pr["planet_b"]["used"] is True
    assert r.jobs[0].planet_a_reference_image_path == str(moon_png.resolve())
    assert r.jobs[0].planet_b_reference_image_path == str(saturn_png.resolve())
    refs = r.jobs[0].reference_images
    assert [row["role"] for row in refs] == ["planet_a", "planet_b"]
    assert refs[0]["path"] == str(moon_png.resolve())
    assert refs[1]["path"] == str(saturn_png.resolve())
    assert APPROVED_PLANET_REFERENCE_LOCK_MARKER in r.jobs[0].prompt_text
    assert "primary visual source of truth" in r.jobs[0].prompt_text
    assert "Old planet canon is symbolic only" in r.jobs[0].prompt_text
    assert "Saturn must not soften into generic dark boss cat" in r.jobs[0].prompt_text
    assert "[CG MATERIAL FINISH HARDLOCK v2]" in r.jobs[0].prompt_text
    assert "moon may hold, brace, swing, or strike with pillow energy" not in r.jobs[0].prompt_text.lower()
    assert "saturn may use chain/control as saturnian restraint" not in r.jobs[0].prompt_text.lower()
    summary = (out / "manifest_summary.txt").read_text(encoding="utf-8")
    assert "Planet references" in summary
    assert "moon_v1" in summary
    assert "saturn_v1" in summary


def test_missing_planet_references_do_not_fail_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = tmp_path / "empty.json"
    write_planet_registry_entries(reg, [])
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    r = build_catstyle_image_generation_jobs(
        date(2026, 5, 20),
        planet_a_override="Moon",
        planet_b_override="Saturn",
        aspect_type_override="square",
        mode_override="tension",
        disable_approved_reference_auto=True,
        disable_arena_reference_auto=True,
        jobs_count=1,
    )
    assert r.jobs
    assert r.jobs[0].planet_a_reference_image_path is None
    assert r.jobs[0].planet_b_reference_image_path is None
    assert r.planet_references_meta is not None
    assert r.planet_references_meta["planet_a"]["used"] is False
    assert r.planet_references_meta["planet_b"]["used"] is False


def test_provider_reference_order_arena_planets_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI" + "_API_KEY", "test-fake-key-for-unit-test")
    get_settings.cache_clear()
    mock_client = MagicMock()
    mock_client.images.edit.return_value = SimpleNamespace(
        data=[SimpleNamespace(b64_json=_MINI_PNG_B64, url=None)]
    )
    paths = {
        "arena": tmp_path / "arena.png",
        "pa": tmp_path / "moon.png",
        "pb": tmp_path / "saturn.png",
        "pair": tmp_path / "pair.png",
    }
    for p in paths.values():
        p.write_bytes(b"x")
    provider = OpenAICatstyleImageProvider(client=mock_client)
    out = tmp_path / "out"
    out.mkdir()
    job = {
        "job_id": "j-1",
        "planet_a": "Moon",
        "planet_b": "Saturn",
        "suggested_output_name": "out1.png",
        "prompt_index": 1,
        "prompt_text": "Test.",
        "negative_prompt": "",
        "reference_images": [
            {"role": "planet_a", "path": str(paths["pa"])},
            {"role": "planet_b", "path": str(paths["pb"])},
            {"role": "arena", "path": str(paths["arena"])},
            {"role": "pair_style", "path": str(paths["pair"])},
        ],
        "arena_reference_image_path": str(paths["arena"]),
        "planet_a_reference_image_path": str(paths["pa"]),
        "planet_b_reference_image_path": str(paths["pb"]),
        "style_reference_image_path": str(paths["pair"]),
        "_stub_output_seq": 1,
    }
    r = provider.generate(job, out, overwrite=False)
    assert r.status == "generated"
    roles = r.metadata.get("reference_image_roles") or []
    assert roles == ["planet_a", "planet_b", "arena", "pair_style"]
    prompt = mock_client.images.edit.call_args.kwargs.get("prompt", "")
    assert "[CATSTYLE REFERENCE IMAGE ROLES v3]" in prompt
    assert "**Image A**" in prompt and "environment reference ONLY" in prompt
    assert "**Image B**" in prompt and "Moon" in prompt and "character reference ONLY" in prompt
    assert "**Image C**" in prompt and "Saturn" in prompt
    assert "**Image D**" in prompt and "optional pair/aspect" in prompt.lower()
    assert "override Image A environment" in prompt
    assert "override per-planet character identity" in prompt


def test_ordered_paths_planets_before_arena_before_pair(tmp_path: Path) -> None:
    files = {k: tmp_path / f"{k}.png" for k in ("arena", "pa", "pb", "pair")}
    for f in files.values():
        f.write_bytes(b"x")
    job = {
        "reference_images": [
            {"role": "planet_a", "path": str(files["pa"])},
            {"role": "planet_b", "path": str(files["pb"])},
            {"role": "arena", "path": str(files["arena"])},
            {"role": "pair_style", "path": str(files["pair"])},
        ]
    }
    ordered = cap._ordered_reference_paths_from_job(job)
    assert [role for role, _ in ordered] == ["planet_a", "planet_b", "arena", "pair_style"]


def test_modular_roles_prefix_pair_cannot_override_planets() -> None:
    prefix = format_catstyle_modular_reference_roles_prefix(
        arena_reference_present=True,
        planet_a_reference_present=True,
        planet_b_reference_present=True,
        pair_style_reference_present=True,
        planet_a_name="Moon",
        planet_b_name="Saturn",
    )
    assert "Modular priority lock" in prefix
    assert "optional pair/aspect" in prefix.lower()
    assert "override per-planet character identity" in prefix


def test_resolve_planet_reference_graceful_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = tmp_path / "empty.json"
    write_planet_registry_entries(reg, [])
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    res = resolve_planet_reference("Pluto")
    assert res.used is False
    assert res.source == "none"


def test_build_job_reference_images_order_and_dedupe(tmp_path: Path) -> None:
    arena = tmp_path / "arena.png"
    moon = tmp_path / "moon.png"
    saturn = tmp_path / "saturn.png"
    pair = arena
    for p in (arena, moon, saturn):
        p.write_bytes(b"x")
    refs = build_job_reference_images(
        arena_reference_image_path=str(arena),
        planet_a_reference_image_path=str(moon),
        planet_b_reference_image_path=str(saturn),
        style_reference_image_path=str(pair),
    )
    assert [row["role"] for row in refs] == ["planet_a", "planet_b", "arena"]
    assert len(refs) == 3
    paths = [row["path"] for row in refs]
    assert len(paths) == len(set(paths))


def test_jobs_reference_images_full_order_with_arena_and_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reg = tmp_path / "approved_planet_references.json"
    arena_png = tmp_path / "arena.png"
    moon_png = tmp_path / "moon.png"
    saturn_png = tmp_path / "saturn.png"
    pair_png = tmp_path / "pair.png"
    for p in (arena_png, moon_png, saturn_png, pair_png):
        p.write_bytes(b"x")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="moon_v1",
                planet="Moon",
                image_path=str(moon_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="saturn_v1",
                planet="Saturn",
                image_path=str(saturn_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    monkeypatch.setattr(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.resolve_arena_reference",
        lambda **kwargs: (str(arena_png.resolve()), {"arena_reference_used": True}),
    )
    monkeypatch.setattr(
        "astro_content_agent.services.content.catstyle_image_generation_jobs._resolve_final_style_reference",
        lambda **kwargs: (str(pair_png.resolve()), {"source": "explicit", "reference_tier": "exact"}),
    )
    r = build_catstyle_image_generation_jobs(
        date(2026, 5, 20),
        planet_a_override="Moon",
        planet_b_override="Saturn",
        aspect_type_override="square",
        mode_override="tension",
        disable_approved_reference_auto=True,
        disable_arena_reference_auto=False,
        use_planet_reference_auto=True,
        output_dir=tmp_path / "jobs",
        jobs_count=1,
    )
    refs = r.jobs[0].reference_images
    assert [row["role"] for row in refs] == ["planet_a", "planet_b", "arena", "pair_style"]
    assert len({row["path"] for row in refs}) == len(refs)


def test_provider_uses_reference_images_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI" + "_API_KEY", "test-fake-key-for-unit-test")
    get_settings.cache_clear()
    mock_client = MagicMock()
    mock_client.images.edit.return_value = SimpleNamespace(
        data=[SimpleNamespace(b64_json=_MINI_PNG_B64, url=None)]
    )
    moon = tmp_path / "moon.png"
    saturn = tmp_path / "saturn.png"
    moon.write_bytes(b"x")
    saturn.write_bytes(b"x")
    provider = OpenAICatstyleImageProvider(client=mock_client)
    out = tmp_path / "out"
    out.mkdir()
    job = {
        "job_id": "j-ref-list",
        "planet_a": "Moon",
        "planet_b": "Saturn",
        "suggested_output_name": "out1.png",
        "prompt_index": 1,
        "prompt_text": "Test.",
        "negative_prompt": "",
        "reference_images": [
            {"role": "planet_a", "path": str(moon)},
            {"role": "planet_b", "path": str(saturn)},
        ],
        "_stub_output_seq": 1,
    }
    r = provider.generate(job, out, overwrite=False)
    assert r.status == "generated"
    roles = r.metadata.get("reference_image_roles") or []
    assert roles == ["planet_a", "planet_b"]


def test_execution_manifest_logs_all_job_reference_images(tmp_path: Path) -> None:
    refs = {
        "pa": tmp_path / "pa.png",
        "pb": tmp_path / "pb.png",
        "arena": tmp_path / "arena.png",
        "pair": tmp_path / "pair.png",
    }
    for p in refs.values():
        p.write_bytes(b"x")
    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": "2026-05-20",
        "editorial_profile": "charged",
        "jobs": [
            {
                "job_id": "j-1",
                "suggested_output_name": "out1.png",
                "prompt_index": 1,
                "prompt_text": "Test.",
                "status": "pending",
                "reference_images": [
                    {"role": "planet_a", "path": str(refs["pa"])},
                    {"role": "planet_b", "path": str(refs["pb"])},
                    {"role": "arena", "path": str(refs["arena"])},
                    {"role": "pair_style", "path": str(refs["pair"])},
                ],
            }
        ],
    }
    mp = tmp_path / "image_generation_jobs.json"
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    out = tmp_path / "out"
    res = execute_catstyle_image_jobs(mp, provider_name="stub", output_dir=out, overwrite=False)
    assert res.execution_manifest_path is not None
    exec_manifest = json.loads(Path(res.execution_manifest_path).read_text(encoding="utf-8"))
    lines = exec_manifest.get("reference_log_lines") or []
    assert any("planet_a" in line and str(refs["pa"]) in line for line in lines)
    assert any("planet_b" in line and str(refs["pb"]) in line for line in lines)
    assert any("arena" in line and str(refs["arena"]) in line for line in lines)
    assert any("pair_style" in line and str(refs["pair"]) in line for line in lines)


def test_list_resolved_winners_by_planet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
        list_resolved_winners_by_planet,
    )

    reg = tmp_path / "approved_planet_references.json"
    venus_png = tmp_path / "venus.png"
    venus_png.write_bytes(b"v")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="venus_v1",
                planet="Venus",
                image_path=str(venus_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    winners = list_resolved_winners_by_planet()
    assert "Venus" in winners
    assert winners["Venus"] is not None
    assert winners["Venus"].registry_key == "venus_v1"


def test_all_registered_planets_resolve_with_active_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reg = tmp_path / "approved_planet_references.json"
    entries: list[ApprovedPlanetReferenceEntry] = []
    for planet in _REGISTERED_PLANETS:
        p = tmp_path / f"{planet.lower()}.png"
        p.write_bytes(b"x")
        entries.append(
            ApprovedPlanetReferenceEntry(
                registry_key=f"{planet.lower()}_v1",
                planet=planet,
                image_path=str(p),
                priority=100,
                active=True,
            )
        )
    write_planet_registry_entries(reg, entries)
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    for planet in _REGISTERED_PLANETS:
        row = resolve_planet_reference(planet)
        assert row.used is True
        assert row.image_path


def test_saturn_venus_prompt_omits_old_visual_cliches_when_planet_refs_active(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest
    from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack

    reg = tmp_path / "approved_planet_references.json"
    saturn_png = tmp_path / "saturn.png"
    venus_png = tmp_path / "venus.png"
    saturn_png.write_bytes(b"s")
    venus_png.write_bytes(b"v")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="saturn_v1",
                planet="Saturn",
                image_path=str(saturn_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="venus_v1",
                planet="Venus",
                image_path=str(venus_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Saturn",
            planet_b="Venus",
            aspect_type="square",
            mode="tension",
            use_planet_reference_auto=True,
            render_style_profile_key="premium_cg_keyart_v1",
        )
    )
    blob = " ".join(pack.image_prompts)
    low = blob.lower()
    assert APPROVED_PLANET_REFERENCE_LOCK_MARKER in blob
    assert "[CG MATERIAL FINISH HARDLOCK v2]" in blob
    assert "Old planet canon is symbolic only" in blob
    assert "SYMBOLIC CANON ONLY" in blob
    assert "Stoic pinstripe round cat" not in blob
    assert "Plush rose-cheek round cat" not in blob
    assert "pinstripe and hat slides a blank contract" not in low
    assert "venus cat with single rose and moodboard" not in low
    assert "business meeting" not in low
    assert "fashion sketches" not in low
    assert "jewelry or watch layout" not in low
    assert "preserve [CANON v1 base]" not in blob
    assert "preserve approved planet reference identity" in blob
    assert "[CATSTYLE PLANET REFERENCE IDENTITY HARDLOCK v1]" in blob
    assert "[PLANET A IDENTITY HARDLOCK — Saturn]" in blob
    assert "[PLANET B IDENTITY HARDLOCK — Venus]" in blob
    assert blob.rfind(APPROVED_PLANET_REFERENCE_LOCK_MARKER) > blob.lower().find("scene beat:")


def test_missing_registered_planet_reference_is_abnormal_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reg = tmp_path / "approved_planet_references.json"
    broken = tmp_path / "missing_venus.png"
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="venus_v1",
                planet="Venus",
                image_path=str(broken),
                priority=100,
                active=True,
            )
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    r = build_catstyle_image_generation_jobs(
        date(2026, 5, 20),
        planet_a_override="Venus",
        planet_b_override="Saturn",
        aspect_type_override="square",
        mode_override="tension",
        disable_approved_reference_auto=True,
        disable_arena_reference_auto=True,
        output_dir=tmp_path / "jobs",
        jobs_count=1,
    )
    assert "WARNING: missing approved planet reference for registered planet Venus" in (r.message or "")



