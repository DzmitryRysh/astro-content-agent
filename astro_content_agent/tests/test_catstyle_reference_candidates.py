"""Catstyle reference candidate workflow and approval CLI."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.approved_reference_registry import (
    read_registry_entries,
    resolve_approved_reference,
)
from astro_content_agent.services.content.catstyle_creative_publish_stability import (
    evaluate_creative_publish_stability,
)
from astro_content_agent.services.content.catstyle_daily_agent import run_catstyle_daily_agent
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    CatstyleImageGenJob,
    CatstyleImageGenerationJobsResult,
)
from astro_content_agent.services.content.catstyle_reference_candidates import (
    REFERENCE_REVIEW_CHECKLIST_ITEMS,
    build_visual_review_checklist_markdown,
    pair_folder_slug,
    reference_candidate_dir,
)
from astro_content_agent.services.content import catstyle_reference_approval as approval_service


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


def _fake_unstable_jobs(tmp_path: Path, d: date, jobs_count: int) -> CatstyleImageGenerationJobsResult:
    out = tmp_path / "jobs"
    out.mkdir(parents=True, exist_ok=True)
    cand = {
        "planet_a": "Sun",
        "planet_b": "Uranus",
        "aspect_type": "conjunction",
        "mode_recommendation": "tension",
        "total_score": 0,
        "source": "manual_override",
    }
    jobs_data = []
    job_models = []
    for i in range(1, jobs_count + 1):
        suggested = f"catstyle_{d.isoformat()}_{i:03d}_sun_uranus_conjunction_tension.png"
        row = {
            "job_id": f"catstyle-{d.isoformat()}-{i:03d}",
            "planet_a": "Sun",
            "planet_b": "Uranus",
            "aspect_type": "conjunction",
            "editorial_profile": "charged",
            "mode": "tension",
            "source": "manual_override",
            "total_score": 0,
            "prompt_index": i,
            "variant_index": 0,
            "prompt_text": "p",
            "negative_prompt": "n",
            "animation_prompt": "a",
            "carousel_idea": "c",
            "suggested_output_name": suggested,
            "status": "pending",
        }
        jobs_data.append(row)
        job_models.append(CatstyleImageGenJob.model_validate({**row, "date": d.isoformat()}))
    mp = out / "image_generation_jobs.json"
    mp.write_text(
        json.dumps(
            {
                "version": "catstyle-image-generation-jobs-v0",
                "date": d.isoformat(),
                "editorial_profile": "charged",
                "selected_candidate": cand,
                "jobs": jobs_data,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return CatstyleImageGenerationJobsResult(
        date=d.isoformat(),
        editorial_profile="charged",
        selected_candidate=cand,
        jobs=job_models,
        output_dir=str(out),
        manifest_path=str(mp),
    )


def test_unstable_pair_reference_candidates_generates_two_jobs(tmp_path: Path) -> None:
    captured: dict = {}

    def fake_build(d: date, **kwargs: object) -> CatstyleImageGenerationJobsResult:
        captured["jobs_count"] = kwargs.get("jobs_count")
        return _fake_unstable_jobs(tmp_path, d, int(kwargs.get("jobs_count") or 2))

    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs",
        side_effect=fake_build,
    ):
        with patch(
            "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
        ) as m_pub:
            r = run_catstyle_daily_agent(
                "2099-08-01",
                work_root=tmp_path,
                provider="stub",
                reference_candidates=True,
                jobs_count=2,
                planet_a_override="Sun",
                planet_b_override="Uranus",
                aspect_type_override="conjunction",
                mode_override="tension",
                scan_mode="noon",
                overwrite=True,
            )
    assert r.exit_code == 0
    assert r.status == "reference_candidates_ok"
    assert captured["jobs_count"] == 2
    assert len(r.candidate_image_paths) == 2
    assert r.reference_candidates_dir
    review = Path(r.visual_review_path or "")
    assert review.is_file()
    text = review.read_text(encoding="utf-8")
    assert any(item.split("?")[0] in text for item in REFERENCE_REVIEW_CHECKLIST_ITEMS[:2])
    m_pub.assert_not_called()


def test_reference_candidates_no_publish_even_if_publish_flag(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs",
        return_value=_fake_unstable_jobs(tmp_path, date(2099, 8, 2), 2),
    ):
        with patch(
            "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
        ) as m_pub:
            r = run_catstyle_daily_agent(
                "2099-08-02",
                work_root=tmp_path,
                provider="stub",
                reference_candidates=True,
                publish=True,
                planet_a_override="Sun",
                planet_b_override="Uranus",
                aspect_type_override="conjunction",
                mode_override="tension",
                scan_mode="noon",
                overwrite=True,
            )
    assert r.exit_code == 0
    assert not r.publish_handoff_dir
    m_pub.assert_not_called()


def test_stable_pair_normal_run_jobs_count_one(tmp_path: Path) -> None:
    captured: dict = {}

    def fake_build(d: date, **kwargs: object) -> CatstyleImageGenerationJobsResult:
        captured["jobs_count"] = kwargs.get("jobs_count")
        cand = {
            "planet_a": "Mercury",
            "planet_b": "Jupiter",
            "aspect_type": "sextile",
            "mode_recommendation": "flow",
            "total_score": 0,
            "source": "manual_override",
        }
        out = tmp_path / "jobs_mj"
        out.mkdir(parents=True, exist_ok=True)
        mp = out / "image_generation_jobs.json"
        row = {
            "job_id": "catstyle-2099-08-03-001",
            "planet_a": "Mercury",
            "planet_b": "Jupiter",
            "aspect_type": "sextile",
            "editorial_profile": "charged",
            "mode": "flow",
            "source": "manual_override",
            "total_score": 0,
            "prompt_index": 1,
            "variant_index": 0,
            "prompt_text": "p",
            "negative_prompt": "n",
            "animation_prompt": "a",
            "carousel_idea": "c",
            "suggested_output_name": "catstyle_2099-08-03_001_mercury_jupiter_sextile_flow.png",
            "status": "pending",
        }
        mp.write_text(
            json.dumps(
                {
                    "version": "catstyle-image-generation-jobs-v0",
                    "date": d.isoformat(),
                    "selected_candidate": cand,
                    "jobs": [row],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        job = CatstyleImageGenJob.model_validate({**row, "date": d.isoformat()})
        return CatstyleImageGenerationJobsResult(
            date=d.isoformat(),
            editorial_profile="charged",
            selected_candidate=cand,
            jobs=[job],
            output_dir=str(out),
            manifest_path=str(mp),
        )

    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs",
        side_effect=fake_build,
    ):
        r = run_catstyle_daily_agent(
            "2099-08-03",
            work_root=tmp_path,
            provider="stub",
            approve=True,
            jobs_count=1,
            planet_a_override="Mercury",
            planet_b_override="Jupiter",
            aspect_type_override="sextile",
            mode_override="flow",
            scan_mode="noon",
            overwrite=True,
        )
    assert captured["jobs_count"] == 1
    assert r.status != "reference_candidates_ok"


def test_approval_candidate_cli_updates_registry(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    registry_path = repo / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text('{"version":"catstyle-approved-references-v1","entries":[]}\n', encoding="utf-8")
    src = repo / "candidates" / "pick.png"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(b"\x89PNG\r\n\x1a\n" + b"PICK")

    res = approval_service.approve_catstyle_reference(
        source_image=src,
        planet_a="Sun",
        planet_b="Uranus",
        aspect_type="conjunction",
        mode="tension",
        label="Sun Uranus conjunction tension approved",
        repo_root=repo,
        registry_json_path=registry_path,
    )
    assert res.registry_key == "sun_uranus_conjunction_tension_v1"
    rows = read_registry_entries(registry_path)
    hit = resolve_approved_reference("Sun", "Uranus", "conjunction", "tension", registry=rows)
    assert hit is not None

    def _resolve(pa: str, pb: str, asp: str, mo: str, *, registry=None):
        return resolve_approved_reference(pa, pb, asp, mo, registry=rows)

    with patch(
        "astro_content_agent.services.content.catstyle_creative_publish_stability.resolve_approved_reference",
        _resolve,
    ):
        stab = evaluate_creative_publish_stability("Sun", "Uranus", "conjunction", "tension")
    assert stab.stable
    assert stab.has_approved_reference


def test_pair_folder_slug_and_checklist_markdown() -> None:
    slug = pair_folder_slug("Sun", "Uranus", "conjunction", "tension")
    assert "sun" in slug and "uranus" in slug
    d = reference_candidate_dir(Path("/tmp/w"), date(2099, 1, 1), "Sun", "Uranus", "conjunction", "tension")
    assert "catstyle_reference_candidates" in str(d)
    md = build_visual_review_checklist_markdown(
        date_iso="2099-01-01",
        planet_a="Sun",
        planet_b="Uranus",
        aspect_type="conjunction",
        mode="tension",
        candidate_image_paths=[],
        manifest_path=None,
        creatively_stable=False,
        stability_reason="no_approved_reference_or_stable_canon",
    )
    assert "storybook" in md.lower()
    assert "approve_catstyle_reference_candidate" in md


def test_approve_reference_candidate_cli_runs(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    registry_path = repo / "astro_content_agent" / "content" / "catstyle" / "approved_references.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text('{"version":"catstyle-approved-references-v1","entries":[]}\n', encoding="utf-8")
    src = repo / "pick.png"
    src.write_bytes(b"\x89PNG\r\n\x1a\n")

    import astro_content_agent.content.catstyle.approved_reference_registry as reg_mod

    monkeypatch.setattr(reg_mod, "catstyle_repo_root", lambda: repo)
    monkeypatch.setattr(reg_mod, "approved_references_json_path", lambda: registry_path)

    cli = _load_cli("approve_catstyle_reference_candidate.py", "_approve_ref_cand_cli")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "approve_catstyle_reference_candidate.py",
            "--image-path",
            str(src),
            "--planet-a",
            "Sun",
            "--planet-b",
            "Uranus",
            "--aspect-type",
            "conjunction",
            "--mode",
            "tension",
            "--overwrite",
        ],
    )
    assert cli.main() == 0
    assert resolve_approved_reference("Sun", "Uranus", "conjunction", "tension") is not None
