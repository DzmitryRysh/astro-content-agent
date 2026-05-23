"""Catstyle LLM caption prompt builder, context, and fallback generation."""
from __future__ import annotations

import json
from pathlib import Path

from astro_content_agent.content.catstyle.compensation_registry_v1 import CAPTION_COMPENSATION_MARKER
from astro_content_agent.services.content.catstyle_caption_context import (
    build_catstyle_caption_context,
    context_to_llm_payload,
)
from astro_content_agent.services.content.catstyle_caption_generator import (
    build_fallback_caption,
    generate_catstyle_caption,
)
from astro_content_agent.services.content.catstyle_caption_polish import (
    append_timing_once,
    polish_caption_for_package,
    strip_caption_timing_blocks,
)
from astro_content_agent.services.content.catstyle_post_package import build_catstyle_post_package


def _sun_uranus_manifest() -> dict:
    return {
        "date": "2026-05-22",
        "selected_candidate": {
            "planet_a": "Sun",
            "planet_b": "Uranus",
            "aspect_type": "conjunction",
            "mode_recommendation": "tension",
            "closest_hour_utc": 12,
        },
    }


def test_caption_prompt_payload_includes_planet_meanings_and_compensation() -> None:
    ctx = build_catstyle_caption_context(_sun_uranus_manifest())
    payload = context_to_llm_payload(ctx)
    assert "Солнце" in payload["planet_a_meaning"]
    assert "Уран" in payload["planet_b_meaning"]
    assert payload["compensation_primary_action"]
    assert payload["compensation_guidance"]
    assert payload["package_appends_timing_block"] is True
    assert "timing_note" not in payload
    assert "Uranus" in payload["sign_interpretation_rules"]
    assert "Neptune" in payload["sign_interpretation_rules"]
    assert "Pluto" in payload["sign_interpretation_rules"]


def test_sun_uranus_prompt_does_not_send_uranus_sign_context() -> None:
    ctx = build_catstyle_caption_context(_sun_uranus_manifest())
    payload = context_to_llm_payload(ctx)
    if ctx.planet_a_sign:
        assert payload["planet_a_sign_context"]
        assert "Близнец" in (payload["planet_a_sign_context"] or "") or payload["planet_a_sign"]
    assert payload["planet_b_sign"] is None
    assert payload["planet_b_sign_context"] is None
    rules = payload["sign_interpretation_rules"].lower()
    assert "uranus" in rules or "уран" in rules
    assert "не используй" in rules or "нельзя" in rules.lower()


def test_sun_uranus_fallback_caption_no_uranus_sign_phrase() -> None:
    ctx = build_catstyle_caption_context(_sun_uranus_manifest())
    result = build_fallback_caption(ctx)
    low = result.caption.lower()
    assert "уран в" not in low
    assert "уран," not in low or "близнец" not in low.split("уран", 1)[-1][:40]
    assert "солнце" in low or "близнец" in low


def test_polish_strips_duplicate_timing_and_outer_sign_lines() -> None:
    raw = (
        "Солнце в Близнецах — слова и контакт.\n\n"
        "Уран, тоже в Близнецах, приносит внезапность.\n\n"
        "Окно аспекта короткое: примерно на 1–2 дня вокруг пика. Не упусти шанс.\n\n"
        "**Про сроки:** дубль."
    )
    polished = polish_caption_for_package(raw)
    assert "уран" not in polished.lower() or "близнец" not in polished.lower()
    assert "**про сроки:**" not in polished.lower()
    assert "1–2 дня" not in polished.lower()


def test_post_package_sun_uranus_single_timing_and_compensation(tmp_path: Path) -> None:
    manifest = {
        **_sun_uranus_manifest(),
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
    mp = tmp_path / "jobs.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    pkg = build_catstyle_post_package(mp, use_llm_caption=False)
    assert pkg.caption.count("**Про сроки:**") == 1
    assert "уран в близнец" not in pkg.caption.lower()
    assert CAPTION_COMPENSATION_MARKER.lower() in pkg.caption.lower()
    assert "метафора ритма" not in pkg.caption.lower()
    assert "лови пару" not in pkg.caption.lower()


def test_append_timing_once_replaces_inline_timing() -> None:
    from astro_content_agent.services.content.catstyle_aspect_timing import (
        build_aspect_timing_from_manifest,
    )

    meta = build_aspect_timing_from_manifest(_sun_uranus_manifest())
    assert meta is not None
    body = (
        "Текст подписи.\n\n"
        "Окно аспекта короткое: 1–2 дня вокруг пика. Не растягивай на месяц."
    )
    out = append_timing_once(body, meta, __import__("datetime").date(2026, 5, 22), "Sun")
    assert out.count("**Про сроки:**") == 1
    assert strip_caption_timing_blocks(out).count("1–2 дня") == 0 or "1–2 дня" in out.split("**Про сроки:**")[1]


def test_fallback_caption_has_compensation_and_no_placeholder_phrases() -> None:
    ctx = build_catstyle_caption_context(
        {
            "date": "2026-06-01",
            "selected_candidate": {
                "planet_a": "Moon",
                "planet_b": "Saturn",
                "aspect_type": "square",
                "mode_recommendation": "tension",
            },
        }
    )
    result = build_fallback_caption(ctx)
    low = (result.caption + result.hook + result.compensation).lower()
    assert "практический шаг" in low
    assert "зачем это работает" in low
    assert "метафора ритма" not in low
    assert "лови пару" not in low
    assert "луна" in low or "moon" in low
    assert result.compensation.strip()


def test_post_package_uses_fallback_caption_without_llm(tmp_path: Path) -> None:
    manifest = {
        "date": "2026-05-20",
        "selected_candidate": {
            "planet_a": "Sun",
            "planet_b": "Uranus",
            "aspect_type": "conjunction",
            "mode_recommendation": "tension",
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
    mp = tmp_path / "jobs.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    pkg = build_catstyle_post_package(mp, use_llm_caption=False)
    assert "метафора ритма" not in pkg.caption.lower()
    assert "лови пару" not in pkg.caption.lower()
    assert "Солнце" in pkg.caption or "солнце" in pkg.caption.lower()
    assert "Уран" in pkg.caption or "уран" in pkg.caption.lower()
    assert "практический шаг" in pkg.caption.lower()
    assert pkg.caption.count("**Про сроки:**") == 1


def test_llm_prompt_builder_instructions_file_exists() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "services"
        / "ai"
        / "prompts"
        / "ru"
        / "catstyle_caption_writer.md"
    )
    text = path.read_text(encoding="utf-8")
    assert "caption_context" in text
    assert "900" in text
    assert "Лови пару" in text
    assert "package_appends_timing_block" in text
    assert "Уран" in text
    assert "Нептун" in text
    assert "Плутон" in text
