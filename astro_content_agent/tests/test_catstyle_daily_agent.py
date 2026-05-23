"""Tests for Catstyle daily agent orchestration."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from astro_content_agent.services.content.catstyle_daily_agent import run_catstyle_daily_agent
from astro_content_agent.services.content.catstyle_real_publish import CatstyleRealPublishResult


def test_stub_e2e_writes_package_and_handoff(tmp_path: Path) -> None:
    r = run_catstyle_daily_agent(
        "2099-06-01",
        work_root=tmp_path,
        provider="stub",
        approve=True,
        planet_a_override="Mercury",
        planet_b_override="Jupiter",
        aspect_type_override="sextile",
        mode_override="flow",
        scan_mode="noon",
        overwrite=True,
    )
    assert r.exit_code == 0, r.errors
    assert r.manifest_path and Path(r.manifest_path).is_file()
    pkg = Path(r.package_dir or "")
    assert (pkg / "post_package.json").is_file()
    assert (pkg / "manual_review.json").is_file()
    ho = Path(r.publish_handoff_dir or "")
    assert (ho / "publish_handoff.json").is_file()
    assert (ho / "caption_final.txt").is_file()
    gen = Path(r.generated_images_dir or "")
    assert gen.is_dir()
    assert list(gen.glob("*.png"))
    summary_md = tmp_path / "catstyle_daily_runs" / "2099-06-01" / "daily_agent_summary.md"
    assert summary_md.is_file()
    text = summary_md.read_text(encoding="utf-8")
    assert "Mercury" in text
    assert "Jupiter" in text
    assert "sextile" in text.lower()
    assert "caption" in text.lower() and "mode" in text.lower()
    assert "compensation_used" in (tmp_path / "catstyle_daily_runs" / "2099-06-01" / "daily_agent_summary.json").read_text(encoding="utf-8")


def test_validate_only_invokes_publish_workflow_validate(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
    ) as m_pub:
        m_pub.return_value = (0, CatstyleRealPublishResult(publish_status="validate_only_ok", validate_only=True))
        r = run_catstyle_daily_agent(
            "2099-06-02",
            work_root=tmp_path,
            provider="stub",
            validate_only=True,
            planet_a_override="Mercury",
            planet_b_override="Jupiter",
            aspect_type_override="sextile",
            mode_override="flow",
            scan_mode="noon",
            overwrite=True,
        )
    assert r.exit_code == 0
    m_pub.assert_called_once()
    kw = m_pub.call_args.kwargs
    assert kw.get("validate_only") is True
    assert kw.get("do_publish") is False
    summary_md = tmp_path / "catstyle_daily_runs" / "2099-06-02" / "daily_agent_summary.md"
    assert summary_md.is_file()
    body = summary_md.read_text(encoding="utf-8")
    assert "Mercury" in body and "Jupiter" in body
    assert "validate_only" in body.lower()


def _fake_jobs_result(tmp_path: Path, d: date, candidate: dict, job_fields: dict) -> object:
    from astro_content_agent.services.content.catstyle_image_generation_jobs import (
        CatstyleImageGenJob,
        CatstyleImageGenerationJobsResult,
    )

    out = tmp_path / "jobs"
    out.mkdir(parents=True, exist_ok=True)
    mp = out / "image_generation_jobs.json"
    manifest = {
        "version": "catstyle-image-generation-jobs-v0",
        "date": d.isoformat(),
        "editorial_profile": "charged",
        "selected_candidate": candidate,
        "jobs": [job_fields],
    }
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    job = CatstyleImageGenJob.model_validate({**job_fields, "date": d.isoformat()})
    return CatstyleImageGenerationJobsResult(
        date=d.isoformat(),
        editorial_profile="charged",
        selected_candidate=candidate,
        jobs=[job],
        output_dir=str(out),
        manifest_path=str(mp),
    )


def test_unstable_pair_blocks_real_publish(tmp_path: Path) -> None:
    d = date(2099, 7, 1)
    cand = {
        "planet_a": "Jupiter",
        "planet_b": "Moon",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 0,
        "source": "manual_override",
    }
    job = {
        "job_id": "catstyle-2099-07-01-001",
        "planet_a": "Jupiter",
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
        "suggested_output_name": "catstyle_2099-07-01_001_jupiter_moon_square_tension.png",
        "status": "pending",
    }

    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs",
        return_value=_fake_jobs_result(tmp_path, d, cand, job),
    ):
        with patch(
            "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
        ) as m_pub:
            r = run_catstyle_daily_agent(
                "2099-07-01",
                work_root=tmp_path,
                provider="stub",
                publish=True,
                planet_a_override="Jupiter",
                planet_b_override="Moon",
                aspect_type_override="square",
                mode_override="tension",
                scan_mode="noon",
                overwrite=True,
            )
    assert r.exit_code == 1
    assert r.status == "creative_publish_blocked_unstable_pair"
    assert r.publish_handoff_dir
    m_pub.assert_not_called()


def test_unstable_pair_validate_only_still_runs(tmp_path: Path) -> None:
    d = date(2099, 7, 2)
    cand = {
        "planet_a": "Jupiter",
        "planet_b": "Moon",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 0,
        "source": "manual_override",
    }
    job = {
        "job_id": "catstyle-2099-07-02-001",
        "planet_a": "Jupiter",
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
        "suggested_output_name": "catstyle_2099-07-02_001_jupiter_moon_square_tension.png",
        "status": "pending",
    }

    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs",
        return_value=_fake_jobs_result(tmp_path, d, cand, job),
    ):
        with patch(
            "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
        ) as m_pub:
            m_pub.return_value = (0, CatstyleRealPublishResult(publish_status="validate_only_ok", validate_only=True))
            r = run_catstyle_daily_agent(
                "2099-07-02",
                work_root=tmp_path,
                provider="stub",
                validate_only=True,
                planet_a_override="Jupiter",
                planet_b_override="Moon",
                aspect_type_override="square",
                mode_override="tension",
                scan_mode="noon",
                overwrite=True,
            )
    assert r.exit_code == 0
    m_pub.assert_called_once()
    assert m_pub.call_args.kwargs.get("validate_only") is True


def test_force_publish_unstable_logs_and_publishes(tmp_path: Path) -> None:
    d = date(2099, 7, 3)
    cand = {
        "planet_a": "Jupiter",
        "planet_b": "Moon",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 0,
        "source": "manual_override",
    }
    job = {
        "job_id": "catstyle-2099-07-03-001",
        "planet_a": "Jupiter",
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
        "suggested_output_name": "catstyle_2099-07-03_001_jupiter_moon_square_tension.png",
        "status": "pending",
    }

    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs",
        return_value=_fake_jobs_result(tmp_path, d, cand, job),
    ):
        with patch(
            "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
        ) as m_pub:
            m_pub.return_value = (0, CatstyleRealPublishResult(publish_status="published", validate_only=False))
            r = run_catstyle_daily_agent(
                "2099-07-03",
                work_root=tmp_path,
                provider="stub",
                publish=True,
                force_publish_unstable=True,
                planet_a_override="Jupiter",
                planet_b_override="Moon",
                aspect_type_override="square",
                mode_override="tension",
                scan_mode="noon",
                overwrite=True,
            )
    assert r.exit_code == 0
    m_pub.assert_called_once()
    assert any("force-publish-unstable" in ln.lower() for ln in r.log_lines)


def test_mars_pluto_stable_canon_allows_publish(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
    ) as m_pub:
        m_pub.return_value = (0, CatstyleRealPublishResult(publish_status="published", validate_only=False))
        r = run_catstyle_daily_agent(
            "2099-07-04",
            work_root=tmp_path,
            provider="stub",
            publish=True,
            planet_a_override="Mars",
            planet_b_override="Pluto",
            aspect_type_override="square",
            mode_override="tension",
            scan_mode="noon",
            overwrite=True,
        )
    assert r.exit_code == 0
    m_pub.assert_called_once()


def test_publish_invokes_real_publish_path(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
    ) as m_pub:
        m_pub.return_value = (0, CatstyleRealPublishResult(publish_status="published", validate_only=False))
        r = run_catstyle_daily_agent(
            "2099-06-03",
            work_root=tmp_path,
            provider="stub",
            publish=True,
            planet_a_override="Mercury",
            planet_b_override="Jupiter",
            aspect_type_override="sextile",
            mode_override="flow",
            scan_mode="noon",
            overwrite=True,
        )
    assert r.exit_code == 0
    kw = m_pub.call_args.kwargs
    assert kw.get("validate_only") is False
    assert kw.get("do_publish") is True
    summary_md = tmp_path / "catstyle_daily_runs" / "2099-06-03" / "daily_agent_summary.md"
    assert summary_md.is_file()
    body = summary_md.read_text(encoding="utf-8")
    assert "Mercury" in body and "Jupiter" in body
    assert "publish_handoff_dir" in body or (r.publish_handoff_dir or "") in body
    assert "stub" in body.lower()


def test_daily_summary_excludes_raw_token_secrets(tmp_path: Path) -> None:
    secret = "IGA" + ("Z" * 40)
    with patch(
        "astro_content_agent.services.content.catstyle_daily_agent.run_catstyle_handoff_publish_workflow"
    ) as m_pub:
        m_pub.return_value = (
            1,
            CatstyleRealPublishResult(
                publish_status="publish_failed",
                error_message=f"Meta rejected {secret}",
                validate_only=False,
            ),
        )
        r = run_catstyle_daily_agent(
            "2099-06-20",
            work_root=tmp_path,
            provider="stub",
            publish=True,
            force_publish_unstable=True,
            planet_a_override="Mars",
            planet_b_override="Pluto",
            aspect_type_override="square",
            mode_override="tension",
            scan_mode="noon",
            overwrite=True,
        )
    jp = tmp_path / "catstyle_daily_runs" / "2099-06-20" / "daily_agent_summary.json"
    assert jp.is_file()
    raw = jp.read_text(encoding="utf-8")
    assert secret not in raw
    assert "REDACTED" in raw or "Meta rejected" in raw


def test_manual_override_passed_to_job_builder(tmp_path: Path) -> None:
    from astro_content_agent.services.content.catstyle_image_generation_jobs import (
        CatstyleImageGenJob,
        CatstyleImageGenerationJobsResult,
    )

    def fake_build(d: date, **kwargs: object) -> CatstyleImageGenerationJobsResult:
        assert kwargs.get("planet_a_override") == "Mercury"
        assert kwargs.get("planet_b_override") == "Jupiter"
        assert kwargs.get("aspect_type_override") == "sextile"
        assert kwargs.get("mode_override") == "flow"
        out = Path(kwargs["output_dir"])  # type: ignore[arg-type]
        out.mkdir(parents=True, exist_ok=True)
        mp = out / "image_generation_jobs.json"
        manifest = {
            "version": "catstyle-image-generation-jobs-v0",
            "date": d.isoformat(),
            "editorial_profile": "charged",
            "selected_candidate": {
                "planet_a": "Mercury",
                "planet_b": "Jupiter",
                "aspect_type": "sextile",
                "mode_recommendation": "flow",
                "total_score": 0,
                "source": "manual_override",
            },
            "jobs": [
                {
                    "job_id": "catstyle-2099-06-04-001",
                    "date": d.isoformat(),
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
                    "suggested_output_name": "catstyle_2099-06-04_001_mercury_jupiter_sextile_flow.png",
                    "status": "pending",
                }
            ],
        }
        mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        job = CatstyleImageGenJob(
            job_id="catstyle-2099-06-04-001",
            date=d.isoformat(),
            planet_a="Mercury",
            planet_b="Jupiter",
            aspect_type="sextile",
            editorial_profile="charged",
            mode="flow",
            source="manual_override",
            total_score=0,
            prompt_index=1,
            variant_index=0,
            prompt_text="p",
            negative_prompt="n",
            animation_prompt="a",
            carousel_idea="c",
            suggested_output_name="catstyle_2099-06-04_001_mercury_jupiter_sextile_flow.png",
        )
        return CatstyleImageGenerationJobsResult(
            date=d.isoformat(),
            editorial_profile="charged",
            selected_candidate=manifest["selected_candidate"],
            jobs=[job],
            output_dir=str(out),
            manifest_path=str(mp),
        )

    with patch("astro_content_agent.services.content.catstyle_daily_agent.build_catstyle_image_generation_jobs", side_effect=fake_build):
        r = run_catstyle_daily_agent(
            "2099-06-04",
            work_root=tmp_path,
            provider="stub",
            approve=True,
            planet_a_override="Mercury",
            planet_b_override="Jupiter",
            aspect_type_override="sextile",
            mode_override="flow",
            scan_mode="noon",
            overwrite=True,
        )
    assert r.exit_code == 0


def test_stops_when_image_execution_fails(tmp_path: Path) -> None:
    with patch("astro_content_agent.services.content.catstyle_daily_agent.execute_catstyle_image_jobs") as m_ex:
        fake = MagicMock()
        fake.outputs_dir = str(tmp_path / "gen")
        fake.jobs_processed = 1
        fake.status = "completed_stub"
        out = MagicMock()
        out.status = "failed"
        fake.outputs = [out]
        m_ex.return_value = fake
        r = run_catstyle_daily_agent(
            "2099-06-05",
            work_root=tmp_path,
            provider="stub",
            approve=True,
            planet_a_override="Mercury",
            planet_b_override="Jupiter",
            aspect_type_override="sextile",
            mode_override="flow",
            scan_mode="noon",
            overwrite=True,
        )
    assert r.exit_code == 1
    assert r.status == "image_failed"


def test_publish_artifacts_redact_no_raw_long_token_in_json(tmp_path: Path) -> None:
    """Persisted publish result JSON must not contain a fake Instagram token pattern."""
    secret = "IGA" + ("A" * 40)
    r_fail = CatstyleRealPublishResult(
        publish_status="publish_failed",
        error_message=f"Meta said no {secret}",
        error_type="meta_error",
        validate_only=False,
    )
    from astro_content_agent.services.content.catstyle_real_publish import persist_catstyle_publish_artifacts

    d = tmp_path / "ho"
    d.mkdir(parents=True, exist_ok=True)
    persist_catstyle_publish_artifacts(d, r_fail)
    blob = json.loads((d / "catstyle_publish_result.json").read_text(encoding="utf-8"))
    raw = json.dumps(blob, ensure_ascii=False)
    assert secret not in raw
