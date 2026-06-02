"""Catstyle arena pool registry and deterministic selection."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root
from astro_content_agent.content.catstyle.arena_pool_registry_v1 import (
    DEFAULT_ARENA_POOL_KEY,
    list_active_arena_pool_candidates,
    read_arena_pool_entries,
)
from astro_content_agent.content.catstyle.arena_pool_selector_v1 import (
    select_arena_pool_candidate,
    stable_pair_pool_index,
)
from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
    APPROVED_PLANET_REFERENCE_LOCK_MARKER,
    ApprovedPlanetReferenceEntry,
    write_planet_registry_entries,
)
from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import CLEAN_PROMPT_MAX_CHARS
from astro_content_agent.services.content.catstyle_arena_reference_resolver import resolve_arena_reference
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    build_catstyle_image_generation_jobs,
)


def test_arena_pool_registry_resolves_four_candidates() -> None:
    rows = list_active_arena_pool_candidates(DEFAULT_ARENA_POOL_KEY)
    assert len(rows) == 4
    keys = {r.candidate_key for r in rows}
    assert keys == {
        "premium_cosmic_zodiac_arena_v2_01",
        "premium_cosmic_zodiac_arena_v2_02",
        "premium_cosmic_zodiac_arena_v2_03",
        "premium_cosmic_zodiac_arena_v2_04",
    }
    for row in rows:
        path = (catstyle_repo_root() / row.image_path).resolve()
        assert path.is_file(), f"missing pool image: {row.image_path}"


def test_stable_by_pair_selector_is_deterministic() -> None:
    a = select_arena_pool_candidate(
        DEFAULT_ARENA_POOL_KEY,
        "Mercury",
        "Neptune",
        "square",
        "tension",
    )
    b = select_arena_pool_candidate(
        DEFAULT_ARENA_POOL_KEY,
        "Mercury",
        "Neptune",
        "square",
        "tension",
    )
    assert a.candidate_key == b.candidate_key
    assert a.image_path == b.image_path


def test_different_aspect_pairs_may_select_different_candidates() -> None:
    rows = list_active_arena_pool_candidates(DEFAULT_ARENA_POOL_KEY)
    assert len(rows) >= 2
    picks: set[str] = set()
    pairs = [
        ("Mercury", "Neptune", "square", "tension"),
        ("Mars", "Jupiter", "opposition", "tension"),
        ("Venus", "Saturn", "trine", "flow"),
        ("Sun", "Moon", "conjunction", "mixed"),
    ]
    for pa, pb, asp, mode in pairs:
        hit = select_arena_pool_candidate(DEFAULT_ARENA_POOL_KEY, pa, pb, asp, mode)
        picks.add(hit.candidate_key)
    assert len(picks) >= 2


def test_explicit_arena_reference_overrides_arena_pool(tmp_path: Path) -> None:
    explicit = tmp_path / "my_arena.png"
    explicit.write_bytes(b"a")
    path, meta = resolve_arena_reference(
        explicit_path=str(explicit),
        arena_pool_key=DEFAULT_ARENA_POOL_KEY,
        planet_a="Mercury",
        planet_b="Neptune",
        aspect_type="square",
        mode="tension",
    )
    assert path == str(explicit.resolve())
    assert meta.get("source") == "explicit"
    assert meta.get("arena_pool_key") is None


def test_build_jobs_with_arena_pool_key_writes_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    reg = tmp_path / "approved_planet_references.json"
    mercury_png = tmp_path / "mercury.png"
    neptune_png = tmp_path / "neptune.png"
    mercury_png.write_bytes(b"m")
    neptune_png.write_bytes(b"n")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="mercury_v1",
                planet="Mercury",
                image_path=str(mercury_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="neptune_v1",
                planet="Neptune",
                image_path=str(neptune_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    out = tmp_path / "jobs_pool"
    r = build_catstyle_image_generation_jobs(
        date(2026, 6, 2),
        output_dir=out,
        planet_a_override="Mercury",
        planet_b_override="Neptune",
        aspect_type_override="square",
        mode_override="tension",
        clean_refs_mode=True,
        arena_pool_key=DEFAULT_ARENA_POOL_KEY,
        use_planet_reference_auto=True,
        jobs_count=1,
    )
    job = r.jobs[0]
    assert r.arena_reference_meta is not None
    assert r.arena_reference_meta.get("arena_pool_key") == DEFAULT_ARENA_POOL_KEY
    assert r.arena_reference_meta.get("selected_arena_pool_candidate_key")
    assert r.arena_reference_meta.get("arena_selection_mode") == "stable_by_pair"
    assert r.arena_reference_meta.get("selected_arena_reference_path")
    assert [row["role"] for row in job.reference_images] == ["planet_a", "planet_b", "arena"]
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    arena = manifest["arena_reference"]
    assert arena["arena_pool_key"] == DEFAULT_ARENA_POOL_KEY
    assert arena["selected_arena_pool_candidate_key"]
    summary = (out / "manifest_summary.txt").read_text(encoding="utf-8")
    assert "arena_pool_key:" in summary
    assert "selected_arena_pool_candidate:" in summary


def test_clean_refs_with_arena_pool_stays_compact_without_legacy_stack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reg = tmp_path / "approved_planet_references.json"
    mercury_png = tmp_path / "mercury.png"
    neptune_png = tmp_path / "neptune.png"
    mercury_png.write_bytes(b"m")
    neptune_png.write_bytes(b"n")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="mercury_v1",
                planet="Mercury",
                image_path=str(mercury_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="neptune_v1",
                planet="Neptune",
                image_path=str(neptune_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    r = build_catstyle_image_generation_jobs(
        date(2026, 6, 2),
        output_dir=tmp_path / "jobs_clean_pool",
        planet_a_override="Mercury",
        planet_b_override="Neptune",
        aspect_type_override="square",
        mode_override="tension",
        clean_refs_mode=True,
        arena_pool_key=DEFAULT_ARENA_POOL_KEY,
        use_planet_reference_auto=True,
        jobs_count=1,
    )
    prompt = r.jobs[0].prompt_text
    low = prompt.lower()
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
    assert "[banners safety lock v1]" in low
    assert "[arena opulence hardlock v1]" in low
    assert "[arena lighting richness v1]" in low
    assert "golden" in low or "amber" in low
    assert "warm golden torchlight" in low
    assert "without crushing blacks" in low
    neg = r.jobs[0].negative_prompt.lower()
    assert "underexposed arena" in neg
    assert "crushed black shadows" in neg
    assert "shadow-swallowed coliseum" in neg
    assert APPROVED_PLANET_REFERENCE_LOCK_MARKER.lower() not in low
    assert "catstyle visual composition hardlock" not in low


def test_default_arena_behavior_without_pool_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from astro_content_agent.content.catstyle.approved_arena_reference_registry import (
        ApprovedArenaReferenceEntry,
        write_arena_registry_entries,
    )

    arena_png = tmp_path / "default_arena.png"
    arena_png.write_bytes(b"a")
    arena_reg = tmp_path / "arena_reg.json"
    write_arena_registry_entries(
        arena_reg,
        [
            ApprovedArenaReferenceEntry(
                registry_key="test_arena_v1",
                image_path=str(arena_png),
                priority=100,
                active=True,
            )
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.approved_arena_reference_registry.approved_arena_references_json_path",
        lambda: arena_reg,
    )
    path, meta = resolve_arena_reference(
        explicit_path=None,
        arena_pool_key=None,
        planet_a="Mars",
        planet_b="Jupiter",
        aspect_type="square",
        mode="tension",
    )
    assert path == str(arena_png.resolve())
    assert meta.get("source") == "arena_registry"


def test_clean_refs_arena_lighting_hardlock_when_arena_reference_attached() -> None:
    from astro_content_agent.content.catstyle.arena_pool_registry_v1 import DEFAULT_ARENA_POOL_KEY
    from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
        CLEAN_PROMPT_MAX_CHARS,
        build_clean_refs_image_prompt,
        generate_catstyle_clean_refs_prompt_pack,
    )
    from astro_content_agent.content.catstyle.models import CatstylePromptRequest

    with_pool = build_clean_refs_image_prompt(
        "Mars",
        "Uranus",
        "square",
        "tension",
        arena_environment_reference_attached=True,
        arena_pool_key=DEFAULT_ARENA_POOL_KEY,
    )
    low_pool = with_pool.lower()
    assert "[arena opulence hardlock v1]" in low_pool
    assert "[arena lighting richness v1]" in low_pool
    assert "[arena scale dominance v3]" in low_pool
    assert "warm golden torchlight" in low_pool
    assert "without crushing blacks" in low_pool
    assert len(with_pool) <= CLEAN_PROMPT_MAX_CHARS

    explicit_arena = build_clean_refs_image_prompt(
        "Mars",
        "Uranus",
        "square",
        "tension",
        arena_environment_reference_attached=True,
        arena_pool_key=None,
    )
    assert "[arena opulence hardlock v1]" in explicit_arena.lower()

    text_only = build_clean_refs_image_prompt("Mars", "Uranus", "square", "tension")
    assert "[arena opulence hardlock v1]" in text_only.lower()

    pack = generate_catstyle_clean_refs_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Uranus",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            clean_refs_mode=True,
            arena_environment_reference_attached=True,
            arena_pool_key=DEFAULT_ARENA_POOL_KEY,
        )
    )
    neg = pack.negative_prompt.lower()
    assert "underexposed arena" in neg
    assert "crushed black shadows" in neg
    assert "catstyle visual composition hardlock" not in pack.image_prompts[0].lower()


def test_read_arena_pool_entries_from_repo_json() -> None:
    entries = read_arena_pool_entries()
    assert len(entries) >= 4
    pool_rows = [e for e in entries if e.pool_key == DEFAULT_ARENA_POOL_KEY]
    assert len(pool_rows) == 4


def test_stable_pair_pool_index_in_range() -> None:
    idx = stable_pair_pool_index(
        planet_a="Mercury",
        planet_b="Neptune",
        aspect_type="square",
        mode="tension",
        pool_key=DEFAULT_ARENA_POOL_KEY,
        candidate_count=4,
    )
    assert 0 <= idx < 4
