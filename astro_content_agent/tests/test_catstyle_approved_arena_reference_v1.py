"""Tests for Catstyle approved arena/environment reference workflow (v1)."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from astro_content_agent.content.catstyle.approved_arena_reference_registry import (
    ApprovedArenaReferenceEntry,
    resolve_approved_arena_reference,
)
from astro_content_agent.content.catstyle.catstyle_approved_arena_reference_v1 import (
    CATSTYLE_APPROVED_ARENA_REFERENCE_BLOCK,
    apply_approved_arena_reference_to_prompt_pack,
    build_approved_arena_reference_prompt_block,
    format_arena_reference_image_roles_prefix,
    format_dual_reference_provider_priority_preamble,
)
from astro_content_agent.services.content import catstyle_image_providers as cap
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_image_generation_jobs import build_catstyle_image_generation_jobs
from astro_content_agent.services.content.catstyle_image_providers import OpenAICatstyleImageProvider
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack
from astro_content_agent.core.config import get_settings

_MINI_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _mars_pluto_req(**kwargs) -> CatstylePromptRequest:
    base = dict(
        planet_a="Mars",
        planet_b="Pluto",
        aspect_type="square",
        mode="tension",
        variants_count=1,
        disable_approved_reference_prompt_lock=True,
        use_arena_reference_auto=False,
    )
    base.update(kwargs)
    return CatstylePromptRequest(**base)


def test_arena_prompt_block_marker_and_environment_only_language() -> None:
    hit = resolve_approved_arena_reference(
        registry=[
            ApprovedArenaReferenceEntry(
                registry_key="test_arena",
                image_path="references/catstyle_moon_saturn_square_tension_approved.png",
                label="test",
                priority=1,
                active=True,
            )
        ]
    )
    assert hit is not None
    block = build_approved_arena_reference_prompt_block(hit)
    assert "[CATSTYLE APPROVED ARENA REFERENCE v1]" in block
    assert "environment richness" in block.lower() or "environment" in block.lower()
    assert "coliseum" in block.lower()
    assert "Milky Way" in block or "starfield" in block.lower()
    assert "Do NOT copy" in block or "do not copy" in block.lower()
    assert "character" in block.lower()
    assert "glyph" in block.lower()


def test_generate_prompt_pack_includes_arena_block_when_auto_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pack = generate_catstyle_prompt_pack(
        _mars_pluto_req(use_arena_reference_auto=True, disable_arena_reference_auto=False)
    )
    prompt = (pack.image_prompts or [""])[0]
    assert "[CATSTYLE APPROVED ARENA REFERENCE v1]" in prompt
    assert pack.arena_reference_assist is not None
    assert "environment richness" in prompt.lower() or "environment" in prompt.lower()
    assert "not" in prompt.lower() and "character" in prompt.lower()
    assert "glyph discipline" in prompt.lower() or "banner-only" in prompt.lower() or "glyph" in prompt.lower()


def test_arena_block_does_not_remove_glyph_or_character_locks() -> None:
    pack = generate_catstyle_prompt_pack(
        _mars_pluto_req(use_arena_reference_auto=True, disable_arena_reference_auto=False)
    )
    prompt = (pack.image_prompts or [""])[0]
    assert "BANNER" in prompt.upper() or "banner-only" in prompt.lower()
    assert "Mars" in prompt or "mars" in prompt.lower()
    assert "Pluto" in prompt or "pluto" in prompt.lower()


def test_disable_arena_reference_auto_skips_block() -> None:
    pack = generate_catstyle_prompt_pack(
        _mars_pluto_req(use_arena_reference_auto=False, disable_arena_reference_auto=True)
    )
    prompt = (pack.image_prompts or [""])[0]
    assert "[CATSTYLE APPROVED ARENA REFERENCE v1]" not in prompt
    assert pack.arena_reference_assist is None


def test_build_jobs_manifest_includes_arena_reference_metadata(tmp_path: Path) -> None:
    r = build_catstyle_image_generation_jobs(
        __import__("datetime").date(2026, 5, 20),
        planet_a_override="Mars",
        planet_b_override="Pluto",
        aspect_type_override="square",
        mode_override="tension",
        disable_approved_reference_auto=True,
        use_arena_reference_auto=True,
        output_dir=tmp_path / "jobs",
        jobs_count=1,
    )
    assert r.jobs
    assert r.jobs[0].arena_reference_image_path
    assert r.arena_reference_meta is not None
    assert r.arena_reference_meta.get("arena_reference_used") is True
    manifest = json.loads((tmp_path / "jobs" / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest.get("arena_reference") is not None
    assert manifest["arena_reference"].get("arena_reference_used") is True
    assert manifest["jobs"][0].get("arena_reference_image_path")
    prompt = r.jobs[0].prompt_text
    assert "[CATSTYLE APPROVED ARENA REFERENCE v1]" in prompt


def test_openai_provider_passes_style_and_arena_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-unit-test")
    get_settings.cache_clear()
    mock_client = MagicMock()
    mock_client.images.edit.return_value = SimpleNamespace(
        data=[SimpleNamespace(b64_json=_MINI_PNG_B64, url=None)]
    )
    style_ref = tmp_path / "style_ref.png"
    arena_ref = tmp_path / "arena_ref.png"
    style_ref.write_bytes(b"x")
    arena_ref.write_bytes(b"y")
    p = OpenAICatstyleImageProvider(client=mock_client)
    out = tmp_path / "out"
    out.mkdir()
    job = {
        "job_id": "j-1",
        "suggested_output_name": "out1.png",
        "prompt_index": 1,
        "prompt_text": "A test prompt.",
        "negative_prompt": "",
        "style_reference_image_path": str(style_ref),
        "arena_reference_image_path": str(arena_ref),
        "_stub_output_seq": 1,
    }
    r = p.generate(job, out, overwrite=False)
    assert r.status == "generated"
    assert r.metadata.get("reference_used") is True
    assert r.metadata.get("arena_reference_image_path") == str(arena_ref.resolve())
    assert r.metadata.get("style_reference_image_path") == str(style_ref.resolve())
    roles = r.metadata.get("reference_image_roles") or []
    assert roles == ["arena", "pair_style"]
    call_kw = mock_client.images.edit.call_args.kwargs
    img_arg = call_kw.get("image")
    assert img_arg is not None
    if isinstance(img_arg, list):
        assert len(img_arg) == 2
        assert img_arg[0].name == str(arena_ref.resolve())
        assert img_arg[1].name == str(style_ref.resolve())
    prompt = call_kw.get("prompt", "")
    assert "[CATSTYLE REFERENCE IMAGE ROLES v3]" in prompt
    assert "**Image A**" in prompt and "environment reference ONLY" in prompt
    assert "**Image B**" in prompt and "optional pair/aspect" in prompt.lower()
    assert "Modular priority lock" in prompt
    assert "Image A (arena)" in prompt or "arena" in prompt.lower()


def test_ordered_reference_paths_arena_before_style(tmp_path: Path) -> None:
    arena = tmp_path / "arena.png"
    style = tmp_path / "style.png"
    arena.write_bytes(b"a")
    style.write_bytes(b"s")
    job = {
        "arena_reference_image_path": str(arena),
        "style_reference_image_path": str(style),
    }
    ordered = cap._ordered_reference_paths_from_job(job)
    assert [role for role, _ in ordered] == ["arena", "pair_style"]
    assert ordered[0][1] == arena.resolve()
    assert ordered[1][1] == style.resolve()


def test_format_arena_roles_prefix_image_a_arena_image_b_style() -> None:
    prefix = format_arena_reference_image_roles_prefix(
        style_reference_present=True,
        arena_reference_present=True,
        banner_glyph_a=False,
        banner_glyph_b=False,
    )
    assert "[CATSTYLE REFERENCE IMAGE ROLES v3]" in prefix
    assert "**Image A**" in prefix and "environment reference ONLY" in prefix
    assert "**Image B**" in prefix and "optional pair/aspect" in prefix.lower()
    assert "Modular priority lock" in prefix


def test_dual_reference_preamble_arena_wins_environment() -> None:
    preamble = format_dual_reference_provider_priority_preamble(
        arena_present=True, style_present=True
    )
    assert "Image A (arena)" in preamble and "authoritative" in preamble.lower()
    assert "optional pair/aspect reference" in preamble.lower()


def test_format_arena_roles_prefix_environment_not_character() -> None:
    prefix = format_arena_reference_image_roles_prefix(
        style_reference_present=True,
        arena_reference_present=True,
        banner_glyph_a=False,
        banner_glyph_b=False,
    )
    assert "arena/environment" in prefix.lower()
    assert "Modular priority lock" in prefix or "override" in prefix.lower()
    assert "character/aspect" in prefix.lower() or "character" in prefix.lower()


def test_apply_arena_to_pack_sets_assist() -> None:
    hit = resolve_approved_arena_reference(
        registry=[
            ApprovedArenaReferenceEntry(
                registry_key="k",
                image_path="references/catstyle_moon_saturn_square_tension_approved.png",
                active=True,
            )
        ]
    )
    assert hit is not None
    pack = generate_catstyle_prompt_pack(_mars_pluto_req())
    updated = apply_approved_arena_reference_to_prompt_pack(pack, hit)
    assert updated.arena_reference_assist is not None
    assert CATSTYLE_APPROVED_ARENA_REFERENCE_BLOCK.split("]")[0] + "]" in (updated.image_prompts or [""])[0]
