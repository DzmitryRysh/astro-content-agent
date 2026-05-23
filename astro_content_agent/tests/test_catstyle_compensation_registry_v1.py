"""Structured Catstyle compensation registry and post copy integration."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astro_content_agent.content.catstyle.compensation_registry_v1 import (
    CAPTION_COMPENSATION_MARKER,
    resolve_catstyle_compensation,
)
from astro_content_agent.services.content.catstyle_compensation_copy import (
    apply_structured_compensation_to_post_copy,
    format_caption_compensation_lines,
)
from astro_content_agent.services.content.catstyle_post_package import build_catstyle_post_package
from astro_content_agent.services.content.catstyle_publish_handoff import build_catstyle_publish_handoff


def test_resolve_mercury_jupiter_sextile_flow() -> None:
    hit = resolve_catstyle_compensation("Jupiter", "Mercury", "sextile", "flow")
    assert hit is not None
    assert hit.registry_key == "mercury_jupiter_sextile_flow_v1"
    assert "20" in hit.primary_action or "20 минут" in hit.primary_action


def test_resolve_sun_uranus_conjunction_tension_order_insensitive() -> None:
    hit = resolve_catstyle_compensation("Uranus", "Sun", "conjunction", "tension")
    assert hit is not None
    assert hit.registry_key == "sun_uranus_conjunction_tension_v1"


def test_resolve_unknown_pair_returns_none() -> None:
    assert resolve_catstyle_compensation("Venus", "Neptune", "trine", "flow") is None


def test_registry_preferred_over_generic_compensation_block() -> None:
    hook, cap, car, comp, chk = apply_structured_compensation_to_post_copy(
        "Mars",
        "Pluto",
        "square",
        "tension",
        hook="Хук",
        caption="Описание аспекта.",
        carousel="Карусель",
        compensation="Компенсация:\n• одно действие;",
        checklist="Чек",
    )
    assert CAPTION_COMPENSATION_MARKER in cap
    assert "Зачем это работает:" in cap
    assert "Как снять давление аспекта:" in comp
    assert "• одно действие" not in comp
    assert "измеримое действие" in comp.lower() or "контролируем" in comp.lower()


def test_fallback_constructive_channel_for_deep_library_pair(tmp_path: Path) -> None:
    """Pluto–Venus has aspect-library constructive channel but no registry row."""
    hook, cap, car, comp, chk = apply_structured_compensation_to_post_copy(
        "Pluto",
        "Venus",
        "conjunction",
        "tension",
        hook="Хук",
        caption="Коротко про аспект.",
        carousel="Карусель",
        compensation="Компенсация:\n• одно действие;",
        checklist="Чек",
    )
    assert CAPTION_COMPENSATION_MARKER in cap
    assert "boundary" in comp.lower() or "границ" in comp.lower() or "cauldron" in comp.lower() or "ковш" in comp.lower()


def test_format_caption_compensation_lines_compact() -> None:
    entry = resolve_catstyle_compensation("Moon", "Saturn", "square", "tension")
    assert entry is not None
    lines = format_caption_compensation_lines(entry)
    assert lines.count("\n") <= 2
    assert CAPTION_COMPENSATION_MARKER in lines
    assert "Зачем это работает:" in lines


def _manifest(
    tmp_path: Path,
    *,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
) -> Path:
    data = {
        "date": "2026-06-01",
        "editorial_profile": "charged",
        "selected_candidate": {
            "planet_a": planet_a,
            "planet_b": planet_b,
            "aspect_type": aspect_type,
            "mode_recommendation": mode,
            "total_score": 1,
        },
        "jobs": [
            {
                "job_id": "j1",
                "planet_a": planet_a,
                "planet_b": planet_b,
                "aspect_type": aspect_type,
                "mode": mode,
                "prompt_index": 1,
                "variant_index": 0,
                "suggested_output_name": "out.png",
                "status": "pending",
            },
        ],
    }
    mp = tmp_path / "jobs.json"
    mp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return mp


def test_post_package_moon_saturn_includes_practical_compensation(tmp_path: Path) -> None:
    pkg = build_catstyle_post_package(
        _manifest(tmp_path, planet_a="Moon", planet_b="Saturn", aspect_type="square", mode="tension")
    )
    assert CAPTION_COMPENSATION_MARKER in pkg.caption
    assert "потребность" in pkg.caption.lower() or "потребность" in pkg.compensation.lower()
    assert "Пакет Catstyle для ручной сборки" not in pkg.caption


def test_post_package_neptune_moon_conjunction_registry(tmp_path: Path) -> None:
    pkg = build_catstyle_post_package(
        _manifest(tmp_path, planet_a="Neptune", planet_b="Moon", aspect_type="conjunction", mode="tension")
    )
    assert CAPTION_COMPENSATION_MARKER in pkg.caption
    assert "границ" in pkg.caption.lower() or "границ" in pkg.compensation.lower()


def test_publish_handoff_caption_inherits_compensation_line(tmp_path: Path) -> None:
    from astro_content_agent.services.content.catstyle_manual_review import (
        approve_catstyle_manual_review,
        build_catstyle_manual_review,
        write_catstyle_manual_review,
    )
    from astro_content_agent.services.content.catstyle_post_package import write_catstyle_post_package

    mp = _manifest(tmp_path, planet_a="Sun", planet_b="Uranus", aspect_type="conjunction", mode="tension")
    gen = tmp_path / "gen"
    gen.mkdir()
    (gen / "out.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    pkg = build_catstyle_post_package(mp, generated_images_dir=gen)
    pkg_dir = tmp_path / "pkg"
    write_catstyle_post_package(pkg, pkg_dir, overwrite=False)
    mr = build_catstyle_manual_review(pkg_dir)
    write_catstyle_manual_review(mr, pkg_dir, overwrite=False)
    approve_catstyle_manual_review(pkg_dir, "approve", "ok")
    h = build_catstyle_publish_handoff(pkg_dir)
    assert CAPTION_COMPENSATION_MARKER in h.caption_final
    assert h.compensation.strip()
    assert "Пакет Catstyle" not in h.caption_final
