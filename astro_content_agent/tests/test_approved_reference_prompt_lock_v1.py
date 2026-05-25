"""Approved-reference prompt fidelity lock (primary visual anchor)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from astro_content_agent.content.catstyle.approved_reference_registry import (
    ResolvedApprovedReference,
    resolve_approved_reference,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_image_generation_jobs import build_catstyle_image_generation_jobs
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _sun_uranus_req(*, disable_lock: bool = False) -> CatstylePromptRequest:
    return CatstylePromptRequest(
        planet_a="Sun",
        planet_b="Uranus",
        aspect_type="conjunction",
        mode="tension",
        variants_count=1,
        premium_art_direction=True,
        world_template_key="cosmic_zodiac_arena",
        render_style_profile_key="premium_comic_poster_v2",
        shot_mode="epic_arena_showdown",
        disable_approved_reference_prompt_lock=disable_lock,
    )


def test_prompt_includes_approved_reference_lock_when_registry_hit() -> None:
    hit = resolve_approved_reference("Sun", "Uranus", "conjunction", "tension")
    assert hit is not None
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts)
    low = joined.lower()
    assert "[APPROVED CATSTYLE REFERENCE LOCK v1]" in joined
    assert "sibling image from the same campaign" in low
    assert "visual dna" in low or "strict visual dna" in low
    assert "render density" in low
    assert "premium comic-poster finish" in low
    assert "85–95%" in joined or "85-95%" in low
    assert "[REFERENCE FIDELITY GRADING v1]" in joined


def test_lock_appears_after_style_opener_not_before() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    p0 = pack.image_prompts[0]
    assert p0.lower().startswith("premium cinematic comic-poster illustration")
    lock_idx = p0.find("[APPROVED CATSTYLE REFERENCE LOCK v1]")
    aspect_idx = p0.find("Aspect type:")
    assert lock_idx > 0 and aspect_idx > 0
    assert lock_idx < aspect_idx


def test_premium_art_direction_false_keeps_art_direction_profile_none() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            premium_art_direction=False,
        )
    )
    assert pack.art_direction_profile is None
    assert "[APPROVED CATSTYLE REFERENCE LOCK v1]" in pack.image_prompts[0]


def test_sun_uranus_includes_approved_reference_fidelity_language() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    joined = "\n".join(pack.image_prompts)
    low = joined.lower()
    assert "[SUN-URANUS REF FIDELITY]" in joined
    assert "visual target" in low or "approved reference" in low
    assert "solar-core" in low or "solar core" in low or "molten solar-core" in low
    assert "staff" in low
    assert "ice-gas" in low or "bright cyan" in low
    assert "lightning" in low or "electric rings" in low or "electric orbit" in low
    assert "colorful milky way" in low or "galaxy band" in low
    assert "wrist cuff" in low or "wrist cuffs" in low
    assert "collar" in low and "harness" in low
    assert "accessory richness" in low or "hardware silhouette" in low
    assert "do not" in low and "copy reference" in low or "do not" in low and "body glyph" in low
    assert "\u2609" in joined
    assert "\u2645" in joined
    assert "red flag left" in low or "flag left" in low


def test_negative_prompt_anti_drift_when_approved() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req())
    neg = pack.negative_prompt.lower()
    assert len(pack.negative_prompt) <= 1200
    parts = [p.strip() for p in pack.negative_prompt.split(",") if p.strip()]
    norm = [" ".join(p.lower().split()) for p in parts]
    assert len(parts) == len(set(norm))
    assert "reference-lite reinterpretation" in neg
    assert "simplified mascot redraw" in neg
    assert "ordinary fur cats" in neg
    assert "losing approved reference visual dna" in neg
    assert "watercolor" in neg or "storybook" in neg


def test_disable_approved_reference_prompt_lock_skips_block() -> None:
    pack = generate_catstyle_prompt_pack(_sun_uranus_req(disable_lock=True))
    joined = "\n".join(pack.image_prompts)
    assert "[APPROVED CATSTYLE REFERENCE LOCK v1]" not in joined


def test_unstable_pair_without_approved_reference_has_no_lock() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Neptune",
            planet_b="Moon",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
        )
    )
    joined = "\n".join(pack.image_prompts)
    assert "[APPROVED CATSTYLE REFERENCE LOCK v1]" not in joined


def test_build_jobs_manifest_keeps_style_reference_path_for_sun_uranus(tmp_path: Path) -> None:
    r = build_catstyle_image_generation_jobs(
        date(2099, 9, 1),
        output_dir=tmp_path / "jobs",
        scan_mode="noon",
        planet_a_override="Sun",
        planet_b_override="Uranus",
        aspect_type_override="conjunction",
        mode_override="tension",
        jobs_count=1,
    )
    assert r.jobs
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "approved_registry"
    assert r.jobs[0].style_reference_image_path
    assert "sun_uranus" in (r.jobs[0].style_reference_image_path or "").replace("\\", "/").lower()
    assert "[APPROVED CATSTYLE REFERENCE LOCK v1]" in r.jobs[0].prompt_text
    manifest = json.loads((tmp_path / "jobs" / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["style_reference"]["registry_key"] == "sun_uranus_conjunction_tension_v1"


def test_reference_candidates_workflow_unaffected_by_prompt_lock(tmp_path: Path) -> None:
    from astro_content_agent.services.content.catstyle_daily_agent import run_catstyle_daily_agent

    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs"
    ) as m_build:
        from astro_content_agent.tests.test_catstyle_reference_candidates import _fake_unstable_jobs

        m_build.return_value = _fake_unstable_jobs(tmp_path, date(2099, 9, 2), 2)
        r = run_catstyle_daily_agent(
            "2099-09-02",
            work_root=tmp_path,
            provider="stub",
            reference_candidates=True,
            planet_a_override="Sun",
            planet_b_override="Uranus",
            aspect_type_override="conjunction",
            mode_override="tension",
            scan_mode="noon",
            overwrite=True,
        )
    assert r.status == "reference_candidates_ok"
    assert len(r.candidate_image_paths) == 2
