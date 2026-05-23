"""Visual archetype fallback reference resolution and publish gates."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.approved_reference_registry import (
    ApprovedReferenceEntry,
    resolve_approved_reference,
)
from astro_content_agent.content.catstyle.visual_archetype_registry_v1 import (
    VisualArchetypeEntry,
    resolve_archetype_reference,
)
from astro_content_agent.services.content.catstyle_creative_publish_stability import (
    evaluate_creative_publish_stability,
)
from astro_content_agent.services.content.catstyle_daily_agent import run_catstyle_daily_agent
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    build_catstyle_image_generation_jobs,
)
from astro_content_agent.services.content.catstyle_real_publish import CatstyleRealPublishResult
from astro_content_agent.services.content.catstyle_style_reference_resolver import (
    resolve_style_reference,
)
from astro_content_agent.tests.catstyle_reference_test_helpers import write_valid_reference_png


def _tmp_arch_registry(tmp_path: Path) -> tuple[VisualArchetypeEntry, ...]:
    exact_png = tmp_path / "exact.png"
    arch_png = tmp_path / "archetype.png"
    write_valid_reference_png(exact_png)
    write_valid_reference_png(arch_png, color=(90, 40, 120))
    return (
        VisualArchetypeEntry(
            archetype_key="moon_neptune_dream_fog",
            description="test fog",
            planet_pairs=[("Moon", "Neptune")],
            modes=["tension"],
            image_path=str(arch_png),
            prompt_guidance="Archetype test guidance.",
            priority=90,
        ),
    )


def _tmp_exact_registry(tmp_path: Path) -> list[ApprovedReferenceEntry]:
    png = tmp_path / "exact_pair.png"
    write_valid_reference_png(png)
    return [
        ApprovedReferenceEntry(
            registry_key="sun_uranus_conjunction_tension_test",
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            image_path=str(png),
            label="test exact",
            priority=100,
            active=True,
        ),
    ]


def test_exact_reference_wins_over_archetype(tmp_path: Path) -> None:
    arch_reg = _tmp_arch_registry(tmp_path)
    exact_reg = _tmp_exact_registry(tmp_path)
    with (
        patch(
            "astro_content_agent.services.content.catstyle_style_reference_resolver.resolve_approved_reference",
            side_effect=lambda pa, pb, asp, mo, **k: resolve_approved_reference(
                pa, pb, asp, mo, registry=exact_reg
            ),
        ),
        patch(
            "astro_content_agent.services.content.catstyle_style_reference_resolver.resolve_archetype_reference",
            side_effect=lambda pa, pb, asp, mo, **k: resolve_archetype_reference(
                pa, pb, asp, mo, registry=arch_reg
            ),
        ),
    ):
        path, meta = resolve_style_reference(
            explicit_path=None,
            disable_approved_reference_auto=False,
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
        )
    assert meta["reference_tier"] == "exact"
    assert meta["exact_reference_used"] is True
    assert meta["archetype_reference_used"] is False
    assert meta["approved_reference_used"] is True
    assert path


def test_archetype_used_when_exact_missing(tmp_path: Path) -> None:
    arch_reg = _tmp_arch_registry(tmp_path)
    with patch(
        "astro_content_agent.services.content.catstyle_style_reference_resolver.resolve_approved_reference",
        return_value=None,
    ), patch(
        "astro_content_agent.services.content.catstyle_style_reference_resolver.resolve_archetype_reference",
        side_effect=lambda pa, pb, asp, mo, **k: resolve_archetype_reference(
            pa, pb, asp, mo, registry=arch_reg
        ),
    ):
        path, meta = resolve_style_reference(
            explicit_path=None,
            disable_approved_reference_auto=False,
            planet_a="Neptune",
            planet_b="Moon",
            aspect_type="square",
            mode="tension",
        )
    assert meta["reference_tier"] == "archetype"
    assert meta["archetype_reference_used"] is True
    assert meta["archetype_key"] == "moon_neptune_dream_fog"
    assert meta["exact_reference_used"] is False
    assert meta["approved_reference_used"] is False
    assert path


def test_manifest_reports_reference_tier_archetype(tmp_path: Path) -> None:
    arch_reg = _tmp_arch_registry(tmp_path)
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.resolve_style_reference",
        side_effect=lambda **kw: resolve_style_reference(
            **kw,
        ),
    ), patch(
        "astro_content_agent.services.content.catstyle_style_reference_resolver.resolve_approved_reference",
        return_value=None,
    ), patch(
        "astro_content_agent.services.content.catstyle_style_reference_resolver.resolve_archetype_reference",
        side_effect=lambda pa, pb, asp, mo, **k: resolve_archetype_reference(
            pa, pb, asp, mo, registry=arch_reg
        ),
    ):
        r = build_catstyle_image_generation_jobs(
            date(2099, 10, 1),
            output_dir=tmp_path / "jobs",
            planet_a_override="Neptune",
            planet_b_override="Moon",
            aspect_type_override="square",
            mode_override="tension",
            jobs_count=1,
            scan_mode="noon",
        )
    manifest = json.loads((tmp_path / "jobs" / "image_generation_jobs.json").read_text(encoding="utf-8"))
    sr = manifest["style_reference"]
    assert sr["reference_tier"] == "archetype"
    assert sr["archetype_key"] == "moon_neptune_dream_fog"
    assert sr["style_reference_image_path"]


def test_publish_blocked_for_archetype_only_by_default() -> None:
    meta = {
        "reference_tier": "archetype",
        "archetype_reference_used": True,
        "archetype_key": "moon_neptune_dream_fog",
        "exact_reference_used": False,
    }
    r = evaluate_creative_publish_stability(
        "Neptune",
        "Moon",
        "square",
        "tension",
        style_reference_meta=meta,
    )
    assert not r.stable
    assert r.reason == "archetype_reference_validate_only"
    r_ok = evaluate_creative_publish_stability(
        "Neptune",
        "Moon",
        "square",
        "tension",
        allow_archetype_publish=True,
        style_reference_meta=meta,
    )
    assert r_ok.stable
    assert r_ok.has_archetype_reference


def test_daily_agent_blocks_publish_on_archetype_only(tmp_path: Path) -> None:
    d = date(2099, 10, 2)
    arch_png = tmp_path / "arch.png"
    write_valid_reference_png(arch_png)
    meta = {
        "reference_tier": "archetype",
        "archetype_reference_used": True,
        "archetype_key": "moon_neptune_dream_fog",
        "exact_reference_used": False,
        "approved_reference_used": False,
        "style_reference_image_path": str(arch_png.resolve()),
        "source": "archetype_registry",
    }
    cand = {
        "planet_a": "Neptune",
        "planet_b": "Moon",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 0,
        "source": "manual_override",
    }
    job_fields = {
        "job_id": "catstyle-2099-10-02-001",
        "planet_a": "Neptune",
        "planet_b": "Moon",
        "aspect_type": "square",
        "editorial_profile": "charged",
        "mode": "tension",
        "source": "manual_override",
        "total_score": 0,
        "prompt_index": 1,
        "variant_index": 0,
        "prompt_text": "p",
        "negative_prompt": "n",
        "animation_prompt": "a",
        "carousel_idea": "c",
        "suggested_output_name": "catstyle_2099-10-02_001_neptune_moon_square_tension.png",
        "status": "pending",
        "style_reference_image_path": meta["style_reference_image_path"],
    }

    def fake_build(day: date, **kwargs: object):
        from astro_content_agent.services.content.catstyle_image_generation_jobs import (
            CatstyleImageGenJob,
            CatstyleImageGenerationJobsResult,
        )

        out = Path(kwargs["output_dir"])  # type: ignore[arg-type]
        out.mkdir(parents=True, exist_ok=True)
        mp = out / "image_generation_jobs.json"
        manifest = {
            "version": "catstyle-image-generation-jobs-v0",
            "date": day.isoformat(),
            "editorial_profile": "charged",
            "selected_candidate": cand,
            "style_reference": meta,
            "jobs": [job_fields],
        }
        mp.write_text(json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8")
        job = CatstyleImageGenJob.model_validate({**job_fields, "date": day.isoformat()})
        return CatstyleImageGenerationJobsResult(
            date=day.isoformat(),
            editorial_profile="charged",
            selected_candidate=cand,
            jobs=[job],
            output_dir=str(out),
            manifest_path=str(mp),
            style_reference_meta=meta,
        )

    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs",
        side_effect=fake_build,
    ), patch(
        "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
    ) as m_pub:
        r = run_catstyle_daily_agent(
            "2099-10-02",
            work_root=tmp_path,
            provider="stub",
            publish=True,
            approve=True,
            planet_a_override="Neptune",
            planet_b_override="Moon",
            aspect_type_override="square",
            mode_override="tension",
            scan_mode="noon",
            overwrite=True,
        )
    assert r.exit_code == 1
    assert r.status == "creative_publish_blocked_archetype_only"
    m_pub.assert_not_called()


def test_sun_uranus_exact_reference_integration() -> None:
    """Repo registry: Sun/Uranus conjunction tension has exact tier (no test PNG edits)."""
    _, meta = resolve_style_reference(
        explicit_path=None,
        disable_approved_reference_auto=False,
        planet_a="Sun",
        planet_b="Uranus",
        aspect_type="conjunction",
        mode="tension",
    )
    assert meta["reference_tier"] == "exact"
    assert meta["exact_reference_used"] is True
    assert not meta["archetype_reference_used"]


def test_neptune_moon_archetype_fallback_integration() -> None:
    _, meta = resolve_style_reference(
        explicit_path=None,
        disable_approved_reference_auto=False,
        planet_a="Neptune",
        planet_b="Moon",
        aspect_type="square",
        mode="tension",
    )
    assert meta["reference_tier"] == "archetype"
    assert meta["archetype_key"] == "moon_neptune_dream_fog"
    assert meta["style_reference_image_path"]
