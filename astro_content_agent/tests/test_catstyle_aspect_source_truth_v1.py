"""Truth-layer guards for Catstyle aspect_source (sky vs editorial vs natal vs educational)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_aspect_source_truth_v1 import (
    apply_aspect_source_caption_guard,
    infer_aspect_source_from_manifest,
    normalize_aspect_source,
    strip_forbidden_current_sky_phrases,
)
from astro_content_agent.services.content.catstyle_caption_context import (
    build_catstyle_caption_context,
    context_to_llm_payload,
)
from astro_content_agent.services.content.catstyle_caption_polish import polish_caption_for_package
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    build_catstyle_image_generation_jobs,
)
from astro_content_agent.services.content.catstyle_post_package import build_catstyle_post_package


_FORBIDDEN_SAMPLES = (
    "Today on the sky Mercury meets Uranus.",
    "Сегодня на небе Меркурий встречает Уран.",
    "Current sky weather is tense.",
    "Сейчас идёт аспект напряжения.",
    "This transit is active now.",
    "Этот транзит сейчас активен.",
    "The sky is bringing surprises.",
    "Небо включает режим хаоса.",
    "Today this aspect is happening.",
    "Сегодняшний аспект давит на нервы.",
)


def _sky_manifest(*, stack: bool = False) -> dict:
    manifest = {
        "date": "2026-05-22",
        "sky_scan_mode": "day-window",
        "aspect_source": "sky_current",
        "selected_candidate": {
            "planet_a": "Sun",
            "planet_b": "Uranus",
            "aspect_type": "conjunction",
            "mode_recommendation": "tension",
            "closest_hour_utc": 12,
            "aspect_source": "sky_current",
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Sun",
                "planet_b": "Uranus",
                "aspect_type": "conjunction",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "out.png",
            }
        ],
    }
    if stack:
        manifest["sky_weather_stack"] = {
            "combined_weather_label": "Суета",
            "background_aspects": [{"planet_a": "Mars", "planet_b": "Pluto", "aspect_type": "square"}],
        }
    return manifest


def _manual_manifest(*, aspect_source: str | None = None) -> dict:
    mo = {
        "enabled": True,
        "planet_a": "Mercury",
        "planet_b": "Uranus",
        "aspect_type": "opposition",
        "mode": "tension",
    }
    if aspect_source:
        mo["aspect_source"] = aspect_source
    manifest = {
        "date": "2026-05-22",
        "sky_scan_mode": "manual_override",
        "manual_aspect_override": mo,
        "selected_candidate": {
            "planet_a": "Mercury",
            "planet_b": "Uranus",
            "aspect_type": "opposition",
            "mode_recommendation": "tension",
            "source": "manual_override",
            "manual_aspect_override": True,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": "Mercury",
                "planet_b": "Uranus",
                "aspect_type": "opposition",
                "mode": "tension",
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "out.png",
            }
        ],
    }
    if aspect_source:
        manifest["aspect_source"] = aspect_source
        manifest["selected_candidate"]["aspect_source"] = aspect_source
    return manifest


@pytest.mark.parametrize("source", ["sky_current", "manual_editorial", "natal_case", "educational"])
def test_normalize_aspect_source_accepts_allowed_values(source: str) -> None:
    assert normalize_aspect_source(source) == source


def test_normalize_aspect_source_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="aspect_source must be one of"):
        normalize_aspect_source("live_sky")


@pytest.mark.parametrize("sample", _FORBIDDEN_SAMPLES)
def test_strip_forbidden_phrases_removes_current_sky_copy(sample: str) -> None:
    cleaned = strip_forbidden_current_sky_phrases(sample)
    assert not re.search(r"today on the sky|сегодня на небе|current sky weather|сейчас ид", cleaned, re.I)


@pytest.mark.parametrize("source", ["manual_editorial", "natal_case", "educational"])
def test_guard_strips_current_sky_phrases_for_non_sky_sources(source: str) -> None:
    raw = "Сегодня на небе Mercury-Uranus. Current sky weather is loud."
    out = apply_aspect_source_caption_guard(raw, source)
    assert "сегодня на небе" not in out.lower()
    assert "current sky weather" not in out.lower()


def test_guard_preserves_current_sky_phrases_for_sky_current() -> None:
    raw = "Сегодня на небе Sun-Uranus. Current sky weather is electric."
    out = apply_aspect_source_caption_guard(raw, "sky_current")
    assert "сегодня на небе" in out.lower()
    assert "current sky weather" in out.lower()


def test_sky_current_context_allows_timing_and_stack() -> None:
    ctx = build_catstyle_caption_context(_sky_manifest(stack=True))
    payload = context_to_llm_payload(ctx)
    assert ctx.aspect_source == "sky_current"
    assert payload["allows_current_sky_language"] is True
    assert payload["package_appends_timing_block"] is True
    assert ctx.sky_weather_stack is not None


@pytest.mark.parametrize("source", ["manual_editorial", "natal_case", "educational"])
def test_non_sky_context_blocks_timing_and_stack(source: str) -> None:
    manifest = _manual_manifest(aspect_source=source)
    manifest["sky_weather_stack"] = {"combined_weather_label": "should be ignored"}
    ctx = build_catstyle_caption_context(manifest)
    payload = context_to_llm_payload(ctx)
    assert ctx.aspect_source == source
    assert payload["allows_current_sky_language"] is False
    assert payload["package_appends_timing_block"] is False
    assert ctx.sky_weather_stack is None
    assert ctx.aspect_timing is None


def test_polish_applies_guard_for_manual_editorial() -> None:
    ctx = build_catstyle_caption_context(_manual_manifest())
    raw = "Тема дня.\n\nСегодня на небе Меркурий и Уран."
    out = polish_caption_for_package(raw, ctx)
    assert "сегодня на небе" not in out.lower()


def test_post_package_sky_current_appends_timing(tmp_path: Path) -> None:
    mp = tmp_path / "jobs.json"
    mp.write_text(json.dumps(_sky_manifest(), ensure_ascii=False), encoding="utf-8")
    pkg = build_catstyle_post_package(mp, use_llm_caption=False)
    assert pkg.aspect_source == "sky_current"
    assert pkg.caption.count("**Про сроки:**") == 1


def test_post_package_manual_editorial_skips_timing(tmp_path: Path) -> None:
    mp = tmp_path / "jobs.json"
    mp.write_text(json.dumps(_manual_manifest(), ensure_ascii=False), encoding="utf-8")
    pkg = build_catstyle_post_package(mp, use_llm_caption=False)
    assert pkg.aspect_source == "manual_editorial"
    assert "**Про сроки:**" not in pkg.caption
    assert pkg.aspect_timing is None


def test_forced_mercury_uranus_opposition_defaults_manual_editorial(tmp_path: Path) -> None:
    from astro_content_agent.content.catstyle.models import CatstylePromptPack

    fake = CatstylePromptPack(
        image_prompts=["one"],
        image_prompt_shot_roles=["hero_poster"],
        animation_prompt="anim",
        negative_prompt="neg",
        carousel_idea="car",
    )
    from unittest.mock import patch

    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_prompt_pack",
        return_value=fake,
    ):
        r = build_catstyle_image_generation_jobs(
            __import__("datetime").date(2026, 5, 22),
            editorial_profile="charged",
            output_dir=tmp_path / "mu",
            planet_a_override="Mercury",
            planet_b_override="Uranus",
            aspect_type_override="opposition",
            mode_override="tension",
            scan_mode="noon",
            jobs_count=1,
        )
    assert r.selected_candidate is not None
    assert r.selected_candidate.get("aspect_source") == "manual_editorial"
    manifest = json.loads((tmp_path / "mu" / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert infer_aspect_source_from_manifest(manifest) == "manual_editorial"
    assert manifest.get("sky_weather_stack") is None
    ctx = build_catstyle_caption_context(manifest)
    assert ctx.aspect_source == "manual_editorial"
    assert ctx.sky_weather_stack is None


def test_infer_natal_case_from_explicit_manifest_field() -> None:
    manifest = _manual_manifest(aspect_source="natal_case")
    assert infer_aspect_source_from_manifest(manifest) == "natal_case"


def test_infer_educational_from_explicit_manifest_field() -> None:
    manifest = _sky_manifest()
    manifest["aspect_source"] = "educational"
    manifest["selected_candidate"]["aspect_source"] = "educational"
    assert infer_aspect_source_from_manifest(manifest) == "educational"
