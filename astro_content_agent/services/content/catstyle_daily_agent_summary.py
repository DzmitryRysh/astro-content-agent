"""Daily Catstyle agent run summary artifacts (markdown + JSON)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from astro_content_agent.content.catstyle.compensation_registry_v1 import (
    CAPTION_COMPENSATION_MARKER,
    resolve_catstyle_compensation,
)
from astro_content_agent.services.content.catstyle_creative_publish_stability import (
    CreativePublishStabilityResult,
    evaluate_creative_publish_stability,
)


class _DailyAgentResultLike(Protocol):
    exit_code: int
    date: str
    status: str
    manifest_path: str | None
    image_jobs_dir: str | None
    generated_images_dir: str | None
    primary_image_path: str | None
    package_dir: str | None
    publish_handoff_dir: str | None
    selected_aspect: str
    image_executor_status: str | None
    pipeline_status: str | None
    publish_exit_code: int | None
    publish_status: str | None
    publish_result_paths: list[str]
    reference_candidates_dir: str | None
    candidate_image_paths: list[str]
    visual_review_path: str | None
    errors: list[str]
    summary_md_path: str | None
    summary_json_path: str | None
from astro_content_agent.services.content.catstyle_image_generation_executor import (
    CatstyleImageExecutorStubResult,
)
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    CatstyleImageGenerationJobsResult,
)
from astro_content_agent.services.content.catstyle_post_pipeline import CatstylePostPipelineResult
from astro_content_agent.services.content.catstyle_real_publish import CatstyleRealPublishResult

_TOKEN_RE = re.compile(r"\bIG[A-Za-z0-9_\-]{20,}\b")
_SECRET_KEY_RE = re.compile(
    r"(access_token|refresh_token|api_key|client_secret|password|authorization)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


@dataclass
class DailyAgentRunParams:
    """Operator/config inputs for the daily run (for summary header)."""

    provider: str
    render_style_profile: str
    shot_mode: str
    scan_mode: str
    editorial_profile: str
    validate_only: bool = False
    publish: bool = False
    force_publish_unstable: bool = False
    allow_archetype_publish: bool = False
    reference_candidates: bool = False
    disable_approved_reference_auto: bool = False


@dataclass
class DailyAgentSummaryWriteResult:
    md_path: Path
    json_path: Path


def daily_runs_dir(work_root: Path, date_iso: str) -> Path:
    return work_root.expanduser().resolve() / "catstyle_daily_runs" / date_iso


def _redact_string(value: str) -> str:
    out = _TOKEN_RE.sub("[REDACTED]", value)
    out = _SECRET_KEY_RE.sub(r"\1=[REDACTED]", out)
    return out


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _redact_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_value(v) for v in value]
    if type(value).__module__ == "unittest.mock":
        return None
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return str(value)
    return value


def _generation_modes(exec_res: CatstyleImageExecutorStubResult | None, provider: str) -> list[str]:
    if exec_res is None:
        return []
    modes: list[str] = []
    for o in exec_res.outputs:
        raw_gm = o.generation_mode
        gm = raw_gm.strip() if isinstance(raw_gm, str) else ""
        if gm:
            modes.append(gm)
        elif o.status == "generated_stub":
            modes.append("stub")
    if not modes and provider.strip().lower() == "stub":
        return ["stub"]
    return sorted(set(modes))


def _generated_image_paths(
    exec_res: CatstyleImageExecutorStubResult | None,
    result: _DailyAgentResultLike,
) -> list[str]:
    paths: list[str] = []
    if exec_res is not None:
        for o in exec_res.outputs:
            if o.status in ("generated", "generated_stub") and o.stub_filename:
                p = Path(exec_res.outputs_dir) / o.stub_filename
                if p.is_file():
                    paths.append(str(p.resolve()))
    if result.candidate_image_paths:
        paths.extend(result.candidate_image_paths)
    if result.primary_image_path and result.primary_image_path not in paths:
        paths.append(result.primary_image_path)
    return paths


def _read_caption_source(package_dir: str | None) -> str | None:
    if not package_dir:
        return None
    pp = Path(package_dir) / "post_package.json"
    if not pp.is_file():
        return None
    try:
        data = json.loads(pp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    src = data.get("caption_source")
    return str(src).strip() if src else None


def _compensation_used(
    pa: str,
    pb: str,
    asp: str,
    mode: str,
    package_dir: str | None,
) -> bool:
    if resolve_catstyle_compensation(pa, pb, asp, mode) is not None:
        return True
    if not package_dir:
        return False
    root = Path(package_dir)
    marker = CAPTION_COMPENSATION_MARKER.lower()
    for name in ("caption.txt", "compensation.txt"):
        p = root / name
        if p.is_file():
            try:
                if marker in p.read_text(encoding="utf-8-sig").lower():
                    return True
            except OSError:
                continue
    return False


def _stability_block(
    pa: str,
    pb: str,
    asp: str,
    mode: str,
    *,
    force_publish_unstable: bool,
    status: str,
) -> dict[str, Any]:
    ev = evaluate_creative_publish_stability(
        pa, pb, asp, mode, force_publish_unstable=force_publish_unstable
    )
    blocked = status == "creative_publish_blocked_unstable_pair"
    return {
        "stable": ev.stable,
        "reason": ev.reason,
        "has_exact_approved_reference": getattr(ev, "has_exact_approved_reference", ev.has_approved_reference),
        "has_archetype_reference": getattr(ev, "has_archetype_reference", False),
        "has_approved_reference": ev.has_approved_reference,
        "reference_tier": getattr(ev, "reference_tier", "none"),
        "has_stable_visual_canon": ev.has_stable_visual_canon,
        "force_publish_unstable": ev.force_publish_unstable,
        "publish_blocked": blocked,
    }


def build_daily_agent_summary_payload(
    result: _DailyAgentResultLike,
    *,
    run_params: DailyAgentRunParams,
    jobs_res: CatstyleImageGenerationJobsResult | None = None,
    exec_res: CatstyleImageExecutorStubResult | None = None,
    pipe: CatstylePostPipelineResult | None = None,
    publish_result: CatstyleRealPublishResult | None = None,
    planet_a: str = "",
    planet_b: str = "",
    aspect_type: str = "",
    mode: str = "",
    style_reference_meta: dict[str, Any] | None = None,
    stability: CreativePublishStabilityResult | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble summary dict (redacted before write)."""
    ref_meta = style_reference_meta or (jobs_res.style_reference_meta if jobs_res else None) or {}
    pa = planet_a or ""
    pb = planet_b or ""
    asp = aspect_type or ""
    mo = mode or ""

    if not stability and pa and pb and asp and mo:
        stability = evaluate_creative_publish_stability(
            pa, pb, asp, mo, force_publish_unstable=run_params.force_publish_unstable
        )

    stab_dict: dict[str, Any]
    if stability is not None:
        stab_dict = {
            "stable": stability.stable,
            "reason": stability.reason,
            "has_approved_reference": stability.has_approved_reference,
            "has_stable_visual_canon": stability.has_stable_visual_canon,
            "force_publish_unstable": stability.force_publish_unstable,
            "publish_blocked": result.status == "creative_publish_blocked_unstable_pair",
        }
    elif pa and pb and asp and mo:
        stab_dict = _stability_block(pa, pb, asp, mo, force_publish_unstable=run_params.force_publish_unstable, status=result.status)
    else:
        stab_dict = {"stable": None, "reason": "(not evaluated)", "publish_blocked": False}

    caption_mode = _read_caption_source(result.package_dir)
    if caption_mode is None and result.package_dir:
        caption_mode = "unknown"
    if not result.package_dir:
        caption_mode = None

    publish_extra: dict[str, Any] = {}
    if publish_result is not None:
        publish_extra = {
            "instagram_media_id": publish_result.instagram_media_id,
            "instagram_container_id": publish_result.instagram_container_id,
            "publish_job_id": publish_result.publish_job_id,
            "draft_id": publish_result.draft_id,
            "error_type": publish_result.error_type,
            "error_message": publish_result.error_message,
        }

    payload: dict[str, Any] = {
        "version": "catstyle-daily-agent-summary-v1",
        "date": result.date,
        "exit_code": result.exit_code,
        "status": result.status,
        "selected_aspect": {
            "planet_a": pa or None,
            "planet_b": pb or None,
            "aspect_type": asp or None,
            "mode": mo or None,
            "label": result.selected_aspect or None,
        },
        "render_style_profile": run_params.render_style_profile,
        "shot_mode": run_params.shot_mode,
        "scan_mode": run_params.scan_mode,
        "editorial_profile": run_params.editorial_profile,
        "creative_stability": stab_dict,
        "approved_reference": {
            "reference_tier": ref_meta.get("reference_tier"),
            "exact_reference_used": ref_meta.get("exact_reference_used"),
            "archetype_reference_used": ref_meta.get("archetype_reference_used"),
            "archetype_key": ref_meta.get("archetype_key"),
            "used": bool(ref_meta.get("approved_reference_used")),
            "registry_key": ref_meta.get("approved_reference_registry_key") or ref_meta.get("registry_key"),
            "source": ref_meta.get("source"),
            "style_reference_image_path": ref_meta.get("approved_reference_image_path")
            or ref_meta.get("path")
            or ref_meta.get("style_reference_image_path"),
        },
        "image_generation": {
            "provider": run_params.provider,
            "executor_status": result.image_executor_status or (exec_res.status if exec_res else None),
            "generation_modes": _generation_modes(exec_res, run_params.provider),
            "generated_images_dir": result.generated_images_dir,
            "generated_image_paths": _generated_image_paths(exec_res, result),
            "execution_manifest_path": exec_res.execution_manifest_path if exec_res else None,
        },
        "artifacts": {
            "manifest_path": result.manifest_path,
            "image_jobs_dir": result.image_jobs_dir,
            "package_dir": result.package_dir,
            "publish_handoff_dir": result.publish_handoff_dir,
            "reference_candidates_dir": result.reference_candidates_dir,
            "visual_review_path": result.visual_review_path,
            "publish_result_paths": result.publish_result_paths,
        },
        "caption": {
            "mode": caption_mode,
            "compensation_used": _compensation_used(pa, pb, asp, mo, result.package_dir)
            if pa and pb
            else False,
        },
        "publish": {
            "validate_only": run_params.validate_only,
            "publish_requested": run_params.publish,
            "publish_exit_code": result.publish_exit_code,
            "publish_status": result.publish_status,
            **publish_extra,
        },
        "pipeline_status": result.pipeline_status,
        "warnings": list(warnings or []),
        "errors": list(result.errors),
        "blocked_reasons": list(result.errors) if result.status == "creative_publish_blocked_unstable_pair" else [],
    }
    return _redact_value(payload)


def render_daily_agent_summary_markdown(data: dict[str, Any]) -> str:
    sel = data.get("selected_aspect") or {}
    ref = data.get("approved_reference") or {}
    img = data.get("image_generation") or {}
    cap = data.get("caption") or {}
    pub = data.get("publish") or {}
    stab = data.get("creative_stability") or {}
    art = data.get("artifacts") or {}

    lines = [
        f"# Catstyle daily agent — {data.get('date')}",
        "",
        f"- **Status:** `{data.get('status')}` (exit `{data.get('exit_code')}`)",
        "",
        "## Selected aspect",
        f"- **planet_a:** {sel.get('planet_a') or '—'}",
        f"- **planet_b:** {sel.get('planet_b') or '—'}",
        f"- **aspect_type:** {sel.get('aspect_type') or '—'}",
        f"- **mode:** {sel.get('mode') or '—'}",
        f"- **label:** {sel.get('label') or '—'}",
        "",
        "## Creative setup",
        f"- **render_style_profile:** {data.get('render_style_profile') or '—'}",
        f"- **shot_mode:** {data.get('shot_mode') or '—'}",
        f"- **editorial_profile:** {data.get('editorial_profile') or '—'}",
        f"- **scan_mode:** {data.get('scan_mode') or '—'}",
        "",
        "## Creative stability",
        f"- **stable:** {stab.get('stable')}",
        f"- **reason:** {stab.get('reason') or '—'}",
        f"- **publish_blocked:** {stab.get('publish_blocked')}",
        "",
        "## Style reference",
        f"- **reference_tier:** {ref.get('reference_tier') or '—'}",
        f"- **exact_reference_used:** {ref.get('exact_reference_used')}",
        f"- **archetype_reference_used:** {ref.get('archetype_reference_used')}",
        f"- **archetype_key:** {ref.get('archetype_key') or '—'}",
        f"- **approved_reference_used:** {ref.get('used')}",
        f"- **registry_key:** {ref.get('registry_key') or '—'}",
        f"- **source:** {ref.get('source') or '—'}",
        f"- **style_reference_image_path:** {ref.get('style_reference_image_path') or '—'}",
        "",
        "## Image generation",
        f"- **provider:** {img.get('provider') or '—'}",
        f"- **executor_status:** {img.get('executor_status') or '—'}",
        f"- **generation_modes:** {', '.join(img.get('generation_modes') or []) or '—'}",
        f"- **generated_images_dir:** {img.get('generated_images_dir') or '—'}",
        "",
        "## Caption",
        f"- **mode:** {cap.get('mode') or '—'}",
        f"- **compensation_used:** {cap.get('compensation_used')}",
        "",
        "## Publish",
        f"- **validate_only:** {pub.get('validate_only')}",
        f"- **publish_requested:** {pub.get('publish_requested')}",
        f"- **publish_status:** {pub.get('publish_status') or '—'}",
        f"- **publish_exit_code:** {pub.get('publish_exit_code') if pub.get('publish_exit_code') is not None else '—'}",
        f"- **instagram_media_id:** {pub.get('instagram_media_id') or '—'}",
        f"- **instagram_container_id:** {pub.get('instagram_container_id') or '—'}",
        "",
        "## Artifacts",
    ]
    for key in (
        "manifest_path",
        "image_jobs_dir",
        "package_dir",
        "publish_handoff_dir",
        "reference_candidates_dir",
        "visual_review_path",
    ):
        val = art.get(key)
        if val:
            lines.append(f"- **{key}:** `{val}`")
    gen_paths = img.get("generated_image_paths") or []
    if gen_paths:
        lines.extend(["", "### Generated images", ""])
        for p in gen_paths:
            lines.append(f"- `{p}`")
    if pub.get("publish_result_paths"):
        lines.extend(["", "### Publish result files", ""])
        for p in pub.get("publish_result_paths") or art.get("publish_result_paths") or []:
            lines.append(f"- `{p}`")
    warns = data.get("warnings") or []
    if warns:
        lines.extend(["", "## Warnings", ""])
        for w in warns:
            lines.append(f"- {w}")
    errs = data.get("errors") or []
    if errs:
        lines.extend(["", "## Errors", ""])
        for e in errs:
            lines.append(f"- {e}")
    blocked = data.get("blocked_reasons") or []
    if blocked:
        lines.extend(["", "## Blocked", ""])
        for b in blocked:
            lines.append(f"- {b}")
    lines.append("")
    return "\n".join(lines)


def write_daily_agent_summary(
    work_root: Path,
    result: _DailyAgentResultLike,
    *,
    run_params: DailyAgentRunParams,
    jobs_res: CatstyleImageGenerationJobsResult | None = None,
    exec_res: CatstyleImageExecutorStubResult | None = None,
    pipe: CatstylePostPipelineResult | None = None,
    publish_result: CatstyleRealPublishResult | None = None,
    planet_a: str = "",
    planet_b: str = "",
    aspect_type: str = "",
    mode: str = "",
    style_reference_meta: dict[str, Any] | None = None,
    stability: CreativePublishStabilityResult | None = None,
    warnings: list[str] | None = None,
    write_json: bool = True,
) -> DailyAgentSummaryWriteResult:
    """Write summary artifacts under ``catstyle_daily_runs/<date>/``."""
    out_dir = daily_runs_dir(work_root, result.date)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = build_daily_agent_summary_payload(
        result,
        run_params=run_params,
        jobs_res=jobs_res,
        exec_res=exec_res,
        pipe=pipe,
        publish_result=publish_result,
        planet_a=planet_a,
        planet_b=planet_b,
        aspect_type=aspect_type,
        mode=mode,
        style_reference_meta=style_reference_meta,
        stability=stability,
        warnings=warnings,
    )
    md_path = out_dir / "daily_agent_summary.md"
    md_path.write_text(render_daily_agent_summary_markdown(safe), encoding="utf-8")
    json_path = out_dir / "daily_agent_summary.json"
    if write_json:
        json_path.write_text(json.dumps(safe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return DailyAgentSummaryWriteResult(md_path=md_path, json_path=json_path)


def attach_summary_to_result(
    work_root: Path,
    result: _DailyAgentResultLike,
    **kwargs: Any,
) -> _DailyAgentResultLike:
    """Write summary files and return result with paths set."""
    written = write_daily_agent_summary(work_root, result, **kwargs)
    result.summary_md_path = str(written.md_path.resolve())
    result.summary_json_path = str(written.json_path.resolve())
    return result


__all__ = [
    "DailyAgentRunParams",
    "DailyAgentSummaryWriteResult",
    "attach_summary_to_result",
    "build_daily_agent_summary_payload",
    "daily_runs_dir",
    "render_daily_agent_summary_markdown",
    "write_daily_agent_summary",
]
