"""Catstyle v0 image generation job manifests (structured tasks only — no image APIs)."""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.services.content.catstyle_daily_pack import generate_catstyle_daily_pack


def _slug_part(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_") or "x"


class CatstyleImageGenJob(BaseModel):
    """One render task derived from a single image prompt line (v0)."""

    job_id: str
    date: str
    planet_a: str
    planet_b: str
    aspect_type: str
    editorial_profile: str
    mode: str
    source: str
    total_score: int
    selection_score: int | None = None
    orb: float | None = None
    prompt_index: int = Field(ge=1, description="1-based index into the daily pack image_prompts list.")
    variant_index: int = Field(default=0, ge=0, description="0-based variant when variants_per_prompt > 1.")
    prompt_text: str
    negative_prompt: str
    animation_prompt: str
    carousel_idea: str
    suggested_output_name: str
    status: Literal["pending"] = "pending"
    art_direction_profile: dict[str, Any] | None = Field(
        default=None,
        description="Copied from prompt pack art_direction_profile when premium enrichment was applied.",
    )


class CatstyleImageGenerationJobsResult(BaseModel):
    """Result of ``build_catstyle_image_generation_jobs``."""

    date: str
    editorial_profile: str
    selected_candidate: dict[str, Any] | None = None
    secondary_supportive_candidate: dict[str, Any] | None = None
    jobs: list[CatstyleImageGenJob] = Field(default_factory=list)
    output_dir: str | None = None
    manifest_path: str | None = None
    files_written: list[str] = Field(default_factory=list)
    message: str | None = None


def _manifest_summary_text(
    *,
    date: str,
    editorial_profile: str,
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
    jobs: list[CatstyleImageGenJob],
    output_dir: Path,
) -> str:
    lines: list[str] = [
        f"Catstyle image generation jobs v0 — {date}",
        f"Editorial profile: {editorial_profile}",
        f"Output directory: {output_dir}",
        f"Total jobs: {len(jobs)}",
        "",
        "## Primary selected aspect",
    ]
    if primary:
        lines.append(
            f"{primary.get('planet_a')} {primary.get('aspect_type')} {primary.get('planet_b')}  "
            f"mode={primary.get('mode_recommendation')}  source={primary.get('source')}  "
            f"total_score={primary.get('total_score')}"
        )
        if primary.get("editorial_selection_score") is not None:
            lines.append(f"selection_score={primary.get('editorial_selection_score')}")
    else:
        lines.append("(none)")
    lines.append("")
    if secondary:
        lines.extend(
            [
                "## Secondary supportive / compensation (same day)",
                f"{secondary.get('planet_a')} {secondary.get('aspect_type')} {secondary.get('planet_b')}  "
                f"mode={secondary.get('mode_recommendation')}  source={secondary.get('source')}",
                "",
            ]
        )
    lines.append("## Job index")
    for j in jobs:
        lines.append(f"- {j.job_id}  prompt_index={j.prompt_index}  variant={j.variant_index}  -> {j.suggested_output_name}")
    lines.append("")
    lines.append("Each job is pending until a human or future worker runs an image model and approves output.")
    lines.append("")
    return "\n".join(lines)


def build_catstyle_image_generation_jobs(
    day: date,
    editorial_profile: str = "charged",
    top: int = 1,
    scan_mode: str = "day-window",
    step_hours: int = 2,
    variants_per_prompt: int = 1,
    output_dir: Path | None = None,
    skin_a: str | None = None,
    skin_b: str | None = None,
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleImageGenerationJobsResult:
    """
    Build deterministic image-generation job records from a Catstyle daily pack.

    Does not call OpenAI, Cloudinary, or Instagram.
    """
    skin_a_c = str(skin_a).strip() if skin_a else None
    skin_b_c = str(skin_b).strip() if skin_b else None
    if skin_a_c == "":
        skin_a_c = None
    if skin_b_c == "":
        skin_b_c = None

    pack = generate_catstyle_daily_pack(
        day,
        top=top,
        scan_mode=scan_mode,
        step_hours=step_hours,
        editorial_profile=editorial_profile,
        skin_a=skin_a_c,
        skin_b=skin_b_c,
        compute_positions_fn=compute_positions_fn,
        orb_config=orb_config,
    )

    iso = pack.date
    profile = pack.editorial_profile

    if pack.selected_count == 0 or not pack.selected_candidates or not pack.prompt_packs:
        return CatstyleImageGenerationJobsResult(
            date=iso,
            editorial_profile=profile,
            selected_candidate=None,
            secondary_supportive_candidate=pack.secondary_supportive_candidate,
            jobs=[],
            message="No Catstyle-selected candidates for this date/scan; no image jobs created.",
        )

    primary: dict[str, Any] = dict(pack.selected_candidates[0])
    pp: dict[str, Any] = dict(pack.prompt_packs[0])
    secondary = pack.secondary_supportive_candidate

    image_prompts: list[str] = [str(p) for p in (pp.get("image_prompts") or [])]
    neg = str(pp.get("negative_prompt", ""))
    anim = str(pp.get("animation_prompt", ""))
    carousel = str(pp.get("carousel_idea", ""))
    art_meta = pp.get("art_direction_profile")
    art_direction_profile = art_meta if isinstance(art_meta, dict) else None

    vpp = max(1, int(variants_per_prompt))
    pa = str(primary["planet_a"])
    pb = str(primary["planet_b"])
    aspect = str(primary["aspect_type"])
    mode = str(primary["mode_recommendation"])
    source = str(primary.get("source", ""))
    total_score = int(primary["total_score"])
    sel_score = primary.get("editorial_selection_score")
    selection_score = int(sel_score) if sel_score is not None else None
    orb_val = primary.get("orb")
    orb: float | None = float(orb_val) if orb_val is not None else None

    slug_a = _slug_part(pa)
    slug_b = _slug_part(pb)
    slug_aspect = _slug_part(aspect)
    slug_mode = _slug_part(mode)

    jobs: list[CatstyleImageGenJob] = []
    seq = 0
    for pi, prompt_text in enumerate(image_prompts):
        prompt_index = pi + 1
        for variant_index in range(vpp):
            seq += 1
            job_id = f"catstyle-{iso}-{seq:03d}"
            if vpp > 1:
                suggested = (
                    f"catstyle_{iso}_{seq:03d}_{slug_a}_{slug_b}_{slug_aspect}_{slug_mode}_"
                    f"var{variant_index}.png"
                )
            else:
                suggested = f"catstyle_{iso}_{seq:03d}_{slug_a}_{slug_b}_{slug_aspect}_{slug_mode}.png"
            jobs.append(
                CatstyleImageGenJob(
                    job_id=job_id,
                    date=iso,
                    planet_a=pa,
                    planet_b=pb,
                    aspect_type=aspect,
                    editorial_profile=profile,
                    mode=mode,
                    source=source,
                    total_score=total_score,
                    selection_score=selection_score,
                    orb=orb,
                    prompt_index=prompt_index,
                    variant_index=variant_index,
                    prompt_text=prompt_text,
                    negative_prompt=neg,
                    animation_prompt=anim,
                    carousel_idea=carousel,
                    suggested_output_name=suggested,
                    status="pending",
                    art_direction_profile=art_direction_profile,
                )
            )

    if not jobs:
        return CatstyleImageGenerationJobsResult(
            date=iso,
            editorial_profile=profile,
            selected_candidate=primary,
            secondary_supportive_candidate=secondary,
            jobs=[],
            message="Primary prompt pack had no image_prompts lines; no jobs created.",
        )

    files_written: list[str] = []
    manifest_path: str | None = None
    out_resolved: str | None = None

    if output_dir is not None:
        out = output_dir.expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        out_resolved = str(out)

        manifest = {
            "version": "catstyle-image-generation-jobs-v0",
            "date": iso,
            "editorial_profile": profile,
            "selected_candidate": primary,
            "secondary_supportive_candidate": secondary,
            "jobs": [j.model_dump(mode="json") for j in jobs],
        }
        mp = out / "image_generation_jobs.json"
        mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        manifest_path = str(mp)
        files_written.append("image_generation_jobs.json")

        width = max(2, len(str(len(jobs))))
        for i, job in enumerate(jobs, start=1):
            fname = f"job_{i:0{width}d}_prompt.txt"
            (out / fname).write_text(
                (job.prompt_text or "").rstrip("\n") + "\n",
                encoding="utf-8",
            )
            files_written.append(fname)

        (out / "negative_prompt.txt").write_text(neg.rstrip("\n") + "\n", encoding="utf-8")
        files_written.append("negative_prompt.txt")
        (out / "animation_prompt.txt").write_text(anim.rstrip("\n") + "\n", encoding="utf-8")
        files_written.append("animation_prompt.txt")
        summary = _manifest_summary_text(
            date=iso,
            editorial_profile=profile,
            primary=primary,
            secondary=dict(secondary) if secondary else None,
            jobs=jobs,
            output_dir=out,
        )
        (out / "manifest_summary.txt").write_text(summary, encoding="utf-8")
        files_written.append("manifest_summary.txt")

    return CatstyleImageGenerationJobsResult(
        date=iso,
        editorial_profile=profile,
        selected_candidate=primary,
        secondary_supportive_candidate=dict(secondary) if secondary else None,
        jobs=jobs,
        output_dir=out_resolved,
        manifest_path=manifest_path,
        files_written=files_written,
        message=None,
    )


__all__ = [
    "CatstyleImageGenJob",
    "CatstyleImageGenerationJobsResult",
    "build_catstyle_image_generation_jobs",
]
