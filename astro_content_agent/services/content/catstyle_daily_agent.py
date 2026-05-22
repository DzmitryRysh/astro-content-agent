"""Catstyle daily agent — orchestrate jobs → images → package → review → handoff → optional publish."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import base64
import shutil
from pathlib import Path
from typing import Any

from astro_content_agent.core.config import get_settings
from astro_content_agent.core.repo_env import load_repo_dotenv_if_present
from astro_content_agent.services.content.catstyle_image_generation_executor import execute_catstyle_image_jobs
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    CatstyleImageGenerationJobsResult,
    build_catstyle_image_generation_jobs,
)
from astro_content_agent.services.content.catstyle_post_pipeline import run_catstyle_post_pipeline
from astro_content_agent.services.content.catstyle_creative_publish_stability import (
    CREATIVE_PUBLISH_BLOCKED_MESSAGE,
    evaluate_creative_publish_stability,
)
from astro_content_agent.services.content.catstyle_real_publish import run_catstyle_handoff_publish_workflow
from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root
from astro_content_agent.services.content.catstyle_reference_candidates import (
    collect_candidate_image_paths,
    format_approval_cli_command,
    reference_candidate_dir,
    write_reference_candidate_artifacts,
)

_MIN_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _synthesize_png_placeholders_for_stub_qc(gen_dir: Path, jobs_res: CatstyleImageGenerationJobsResult) -> None:
    """Stub image provider writes JSON placeholders; Catstyle QC expects PNGs at ``suggested_output_name``."""
    gen_resolved = gen_dir.expanduser().resolve()
    refs_dir = (catstyle_repo_root() / "references").resolve()
    if gen_resolved == refs_dir or refs_dir in gen_resolved.parents:
        raise RuntimeError(
            f"Refusing to write stub QC PNGs under production references directory: {gen_resolved}"
        )
    gen_dir.mkdir(parents=True, exist_ok=True)
    for j in jobs_res.jobs:
        name = str(j.suggested_output_name or "").strip()
        if not name.lower().endswith(".png"):
            continue
        dest = gen_dir / Path(name).name
        if not dest.is_file():
            dest.write_bytes(_MIN_PNG)


def _parse_day(s: str) -> date:
    parts = s.strip().split("-")
    if len(parts) != 3:
        raise ValueError("Date must be YYYY-MM-DD")
    try:
        y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as e:
        raise ValueError("Date must be YYYY-MM-DD") from e
    return date(y, m, d)


def _aspect_context(sel: dict[str, Any] | None) -> tuple[str, str, str, str]:
    if not sel:
        return "", "", "", ""
    pa = str(sel.get("planet_a") or "").strip()
    pb = str(sel.get("planet_b") or "").strip()
    asp = str(sel.get("aspect_type") or "").strip()
    mode = str(sel.get("mode_recommendation") or sel.get("mode") or "").strip()
    return pa, pb, asp, mode


def _aspect_label(sel: dict[str, Any] | None) -> str:
    if not sel:
        return "(none)"
    pa = sel.get("planet_a")
    pb = sel.get("planet_b")
    asp = sel.get("aspect_type")
    mode = sel.get("mode_recommendation")
    bits = [str(x) for x in (pa, asp, pb) if x]
    head = " ".join(bits) if bits else "Catstyle"
    if mode:
        return f"{head}  (mode={mode})"
    return head


@dataclass
class CatstyleDailyAgentResult:
    """Structured outcome for ``run_catstyle_daily_agent``."""

    exit_code: int
    date: str
    status: str
    manifest_path: str | None = None
    image_jobs_dir: str | None = None
    generated_images_dir: str | None = None
    primary_image_path: str | None = None
    package_dir: str | None = None
    publish_handoff_dir: str | None = None
    selected_aspect: str = ""
    image_executor_status: str | None = None
    pipeline_status: str | None = None
    publish_exit_code: int | None = None
    publish_status: str | None = None
    publish_result_paths: list[str] = field(default_factory=list)
    reference_candidates_dir: str | None = None
    candidate_image_paths: list[str] = field(default_factory=list)
    visual_review_path: str | None = None
    next_approval_command: str | None = None
    log_lines: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def run_catstyle_daily_agent(
    date_str: str,
    *,
    work_root: Path | None = None,
    provider: str = "stub",
    scan_mode: str = "day-window",
    step_hours: int = 2,
    editorial_profile: str = "charged",
    world_template: str = "cosmic_zodiac_arena",
    render_style_profile: str = "premium_comic_poster_v2",
    shot_mode: str = "epic_arena_showdown",
    jobs_count: int = 1,
    scene_template: str | None = None,
    planet_a_override: str | None = None,
    planet_b_override: str | None = None,
    aspect_type_override: str | None = None,
    mode_override: str | None = None,
    approve: bool = False,
    validate_only: bool = False,
    publish: bool = False,
    overwrite: bool = False,
    approval_notes: str = "",
    brand_profile_id: str | None = None,
    instagram_account_id: str | None = None,
    style_reference_image_path: str | None = None,
    disable_approved_reference_auto: bool = False,
    force_publish_unstable: bool = False,
    reference_candidates: bool = False,
    repo_root_for_dotenv: Path | None = None,
) -> CatstyleDailyAgentResult:
    """
    Run the Catstyle daily pipeline under *work_root* (defaults to ``Path.cwd()``).

    ``approve_effective = approve or validate_only or publish`` — publish/validate paths require an approved handoff.

    Loads repo-root ``.env`` only when *validate_only* or *publish* is requested (same policy as ``publish_catstyle_real``).
    """
    root = (work_root or Path.cwd()).expanduser().resolve()
    day = _parse_day(date_str)
    iso = day.isoformat()
    log: list[str] = []
    errs: list[str] = []
    pub_code: int | None = None
    pub_stat: str | None = None

    def _fail(code: int, status: str, msg: str, **kwargs: Any) -> CatstyleDailyAgentResult:
        errs.append(msg)
        log.append(f"ERROR: {msg}")
        base = CatstyleDailyAgentResult(
            exit_code=code,
            date=iso,
            status=status,
            log_lines=log,
            errors=errs,
            **kwargs,
        )
        return base

    if reference_candidates:
        if publish or validate_only:
            log.append(
                "NOTE: --reference-candidates mode ignores --publish and --validate-only (no Instagram publish)."
            )
        publish = False
        validate_only = False
        approve = False

    approve_effective = bool(approve or validate_only or publish)

    jobs_dir = root / "catstyle_image_jobs" / iso
    jobs_dir.mkdir(parents=True, exist_ok=True)

    log.append(f"[1/5] Build image generation jobs → {jobs_dir}")
    jobs_res = build_catstyle_image_generation_jobs(
        day,
        editorial_profile=editorial_profile,
        top=1,
        scan_mode=scan_mode,
        step_hours=step_hours,
        variants_per_prompt=1,
        output_dir=jobs_dir,
        world_template_key=world_template,
        scene_template_key=scene_template,
        render_style_profile_key=render_style_profile,
        shot_mode=shot_mode,
        jobs_count=jobs_count,
        style_reference_image_path=style_reference_image_path,
        disable_approved_reference_auto=disable_approved_reference_auto,
        planet_a_override=planet_a_override,
        planet_b_override=planet_b_override,
        aspect_type_override=aspect_type_override,
        mode_override=mode_override,
    )
    for ref_line in (jobs_res.style_reference_meta or {}).get("log_lines") or []:
        log.append(f"  {ref_line}")

    if not jobs_res.jobs:
        msg = jobs_res.message or "No image jobs were created for this date/configuration."
        return _fail(1, "jobs_failed", msg, image_jobs_dir=str(jobs_dir))

    mp = Path(jobs_res.manifest_path or (jobs_dir / "image_generation_jobs.json")).resolve()
    if not mp.is_file():
        return _fail(1, "jobs_failed", f"Manifest not found after build: {mp}", image_jobs_dir=str(jobs_dir))

    sel = jobs_res.selected_candidate
    aspect_line = _aspect_label(sel if isinstance(sel, dict) else None)
    log.append(f"  Selected aspect: {aspect_line}")

    pa_ctx, pb_ctx, asp_ctx, mode_ctx = _aspect_context(sel if isinstance(sel, dict) else None)
    exec_output_dir: Path | None = None
    if reference_candidates:
        cand_root = reference_candidate_dir(root, day, pa_ctx, pb_ctx, asp_ctx, mode_ctx)
        exec_output_dir = (cand_root / "images").resolve()
        exec_output_dir.mkdir(parents=True, exist_ok=True)
        log.append(f"[reference-candidates] Output folder: {cand_root}")

    log.append(f"[2/5] Execute image jobs (provider={provider})")
    exec_res = execute_catstyle_image_jobs(
        mp, provider_name=provider, output_dir=exec_output_dir, overwrite=overwrite
    )
    gen_dir = Path(exec_res.outputs_dir).resolve()
    log.append(f"  output_dir: {gen_dir}")
    log.append(f"  executor status: {exec_res.status}")

    if provider.strip().lower() == "stub":
        _synthesize_png_placeholders_for_stub_qc(gen_dir, jobs_res)

    if exec_res.jobs_processed and any(o.status == "failed" for o in exec_res.outputs):
        return _fail(
            1,
            "image_failed",
            "One or more image jobs failed (see execution manifest in output dir).",
            manifest_path=str(mp),
            image_jobs_dir=str(jobs_dir),
            generated_images_dir=str(gen_dir),
            selected_aspect=aspect_line,
            image_executor_status=exec_res.status,
        )

    written = sum(1 for o in exec_res.outputs if o.status in ("generated_stub", "generated"))
    if exec_res.jobs_processed > 0 and written == 0:
        return _fail(
            1,
            "image_missing",
            "Image generation produced no successful outputs.",
            manifest_path=str(mp),
            image_jobs_dir=str(jobs_dir),
            generated_images_dir=str(gen_dir),
            selected_aspect=aspect_line,
            image_executor_status=exec_res.status,
        )

    if reference_candidates:
        cand_root = reference_candidate_dir(root, day, pa_ctx, pb_ctx, asp_ctx, mode_ctx)
        images_dir = gen_dir
        shutil.copy2(mp, cand_root / "image_generation_jobs.json")
        cand_paths = collect_candidate_image_paths(images_dir, jobs_res.jobs)
        review_path, _meta_path = write_reference_candidate_artifacts(
            cand_root,
            date_iso=iso,
            planet_a=pa_ctx,
            planet_b=pb_ctx,
            aspect_type=asp_ctx,
            mode=mode_ctx,
            candidate_image_paths=cand_paths,
            manifest_path=cand_root / "image_generation_jobs.json",
            jobs_count=jobs_count,
            provider=provider,
        )
        next_cmd = format_approval_cli_command(
            image_path=cand_paths[0] if cand_paths else images_dir / "SELECTED.png",
            planet_a=pa_ctx,
            planet_b=pb_ctx,
            aspect_type=asp_ctx,
            mode=mode_ctx,
        )
        log.append(f"[reference-candidates] Folder: {cand_root}")
        log.append(f"[reference-candidates] Jobs: {len(jobs_res.jobs)}  images: {len(cand_paths)}")
        for cp in cand_paths:
            log.append(f"  candidate: {cp}")
        log.append(f"[reference-candidates] Review: {review_path}")
        log.append(f"[reference-candidates] Next: {next_cmd}")
        return CatstyleDailyAgentResult(
            exit_code=0,
            date=iso,
            status="reference_candidates_ok",
            manifest_path=str(mp),
            image_jobs_dir=str(jobs_dir),
            generated_images_dir=str(images_dir),
            selected_aspect=aspect_line,
            image_executor_status=exec_res.status,
            reference_candidates_dir=str(cand_root),
            candidate_image_paths=[str(p) for p in cand_paths],
            visual_review_path=str(review_path),
            next_approval_command=next_cmd,
            log_lines=log,
            errors=errs,
        )

    pkg_root = root / "catstyle_post_packages" / iso
    handoff_root = root / "catstyle_publish_handoffs" / iso

    log.append("[3/5] Build post package + manual review")
    pipe = run_catstyle_post_pipeline(
        mp,
        generated_images_dir=gen_dir,
        post_package_dir=pkg_root,
        publish_handoff_dir=handoff_root,
        approve=approve_effective,
        approval_notes=approval_notes,
        overwrite=overwrite,
    )
    log.append(f"  pipeline status: {pipe.status}")
    log.append(f"  package_dir: {pipe.package_dir}")
    log.append(f"  primary_image: {pipe.recommended_primary_image or '(none)'}")

    if pipe.status == "needs_attention":
        msg = "Post pipeline needs attention (QC or approval/handoff gate)."
        if pipe.errors:
            msg += " " + "; ".join(pipe.errors)
        return _fail(
            1,
            "pipeline_needs_attention",
            msg,
            manifest_path=str(mp),
            image_jobs_dir=str(jobs_dir),
            generated_images_dir=str(gen_dir),
            primary_image_path=pipe.recommended_primary_image,
            package_dir=pipe.package_dir,
            selected_aspect=aspect_line,
            image_executor_status=exec_res.status,
            pipeline_status=pipe.status,
        )

    publish_paths: list[str] = []

    if publish and not validate_only:
        stability = evaluate_creative_publish_stability(
            pa_ctx,
            pb_ctx,
            asp_ctx,
            mode_ctx,
            force_publish_unstable=force_publish_unstable,
        )
        if stability.force_publish_unstable:
            log.append(
                "WARNING: --force-publish-unstable — real Instagram publish allowed without approved reference or stable canon."
            )
        if not stability.stable:
            log.append(f"[5/5] Creative publish gate: BLOCKED ({stability.reason})")
            return _fail(
                1,
                "creative_publish_blocked_unstable_pair",
                CREATIVE_PUBLISH_BLOCKED_MESSAGE,
                manifest_path=str(mp),
                image_jobs_dir=str(jobs_dir),
                generated_images_dir=str(gen_dir),
                primary_image_path=pipe.recommended_primary_image,
                package_dir=pipe.package_dir,
                publish_handoff_dir=pipe.publish_handoff_dir,
                selected_aspect=aspect_line,
                image_executor_status=exec_res.status,
                pipeline_status=pipe.status,
            )

    if validate_only or publish:
        rr = repo_root_for_dotenv or root
        while rr != rr.parent and not (rr / ".env").is_file():
            rr = rr.parent
        load_repo_dotenv_if_present(rr)

        if not pipe.publish_handoff_dir:
            return _fail(
                1,
                "handoff_missing",
                "Publish/validate requested but publish handoff was not produced (approval/QC).",
                manifest_path=str(mp),
                image_jobs_dir=str(jobs_dir),
                generated_images_dir=str(gen_dir),
                primary_image_path=pipe.recommended_primary_image,
                package_dir=pipe.package_dir,
                selected_aspect=aspect_line,
                image_executor_status=exec_res.status,
                pipeline_status=pipe.status,
            )

        log.append(f"[4/5] Publish handoff dir: {pipe.publish_handoff_dir}")
        settings = get_settings()

        log.append("[5/5] Publish / validate")
        handoff_p = Path(pipe.publish_handoff_dir).resolve()
        pub_code, pr = run_catstyle_handoff_publish_workflow(
            handoff_p,
            settings=settings,
            validate_only=validate_only,
            do_publish=publish,
            brand_profile_id_cli=brand_profile_id,
            instagram_account_id_cli=instagram_account_id,
        )
        pub_stat = pr.publish_status if pr is not None else None
        log.append(f"  publish workflow exit: {pub_code}  status: {pub_stat}")
        jp = handoff_p / "catstyle_publish_result.json"
        mpth = handoff_p / "catstyle_publish_result.md"
        if jp.is_file():
            publish_paths.append(str(jp))
        if mpth.is_file():
            publish_paths.append(str(mpth))

        if pub_code != 0:
            msg = pr.error_message if pr and pr.error_message else "Publish/validate step failed."
            return _fail(
                pub_code,
                "publish_failed" if publish else "validate_failed",
                msg,
                manifest_path=str(mp),
                image_jobs_dir=str(jobs_dir),
                generated_images_dir=str(gen_dir),
                primary_image_path=pipe.recommended_primary_image,
                package_dir=pipe.package_dir,
                publish_handoff_dir=pipe.publish_handoff_dir,
                selected_aspect=aspect_line,
                image_executor_status=exec_res.status,
                pipeline_status=pipe.status,
                publish_exit_code=pub_code,
                publish_status=pub_stat,
                publish_result_paths=publish_paths,
            )

    final_status = pipe.status
    if validate_only and pub_code == 0:
        final_status = "validate_only_ok"
    elif publish and pub_code == 0:
        final_status = pub_stat or "ok"

    return CatstyleDailyAgentResult(
        exit_code=0,
        date=iso,
        status=final_status,
        manifest_path=str(mp),
        image_jobs_dir=str(jobs_dir),
        generated_images_dir=str(gen_dir),
        primary_image_path=pipe.recommended_primary_image,
        package_dir=pipe.package_dir,
        publish_handoff_dir=pipe.publish_handoff_dir,
        selected_aspect=aspect_line,
        image_executor_status=exec_res.status,
        pipeline_status=pipe.status,
        publish_exit_code=pub_code,
        publish_status=pub_stat,
        publish_result_paths=publish_paths,
        log_lines=log,
        errors=errs,
    )


__all__ = ["CatstyleDailyAgentResult", "run_catstyle_daily_agent"]
