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
from astro_content_agent.content.catstyle.approved_arena_reference_registry import ResolvedArenaReference
from astro_content_agent.content.catstyle.catstyle_approved_arena_reference_v1 import (
    apply_approved_arena_reference_to_prompt_pack,
)
from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
    resolve_planet_references_for_pair,
)
from astro_content_agent.content.catstyle.models import CatstylePromptPack, CatstylePromptRequest
from astro_content_agent.services.content.catstyle_arena_reference_resolver import resolve_arena_reference
from astro_content_agent.services.content.catstyle_style_reference_resolver import resolve_style_reference
from astro_content_agent.services.content.catstyle_daily_pack import generate_catstyle_daily_pack
from astro_content_agent.services.content.catstyle_manual_override_timing import (
    merge_manual_override_day_window_into_primary,
)
from astro_content_agent.services.content.catstyle_editorial_selection import normalize_editorial_profile
from astro_content_agent.services.content.catstyle_aspect_source_truth_v1 import (
    DEFAULT_FORCED_ASPECT_SOURCE,
    annotate_manifest_aspect_source,
    annotate_manifest_sky_timing_mode,
    infer_sky_timing_mode_from_manifest,
    normalize_aspect_source,
)
from astro_content_agent.services.content.catstyle_prompt_generator import (
    generate_catstyle_prompt_pack,
    normalize_planet_name,
)


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
    shot_role: str | None = Field(
        default=None,
        description="hero_poster | alternate_action_angle when hero_pair shot_mode produced parallel roles.",
    )
    style_reference_image_path: str | None = Field(
        default=None,
        description="Optional local path to approved style reference image for providers that support image-conditioned generation.",
    )
    banner_glyph_reference_planet_a_path: str | None = Field(
        default=None,
        description="Narrow banner-glyph reference for planet A (left/port banner), Image B when style ref present.",
    )
    banner_glyph_reference_planet_b_path: str | None = Field(
        default=None,
        description="Narrow banner-glyph reference for planet B (right/starboard banner), Image C when style ref present.",
    )
    arena_reference_image_path: str | None = Field(
        default=None,
        description="Optional local path to approved arena/environment reference (coliseum, sky, floor only).",
    )
    planet_a_reference_image_path: str | None = Field(
        default=None,
        description="Optional local path to approved planet A character reference.",
    )
    planet_b_reference_image_path: str | None = Field(
        default=None,
        description="Optional local path to approved planet B character reference.",
    )
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
    world_template_key: str | None = Field(
        default=None,
        description="From prompt pack world_template_profile.template_key when present.",
    )
    scene_template_key: str | None = Field(
        default=None,
        description="From prompt pack scene_template_profile.template_key when present.",
    )
    world_template_profile: dict[str, Any] | None = Field(
        default=None,
        description="Copied serialized CatstyleWorldTemplate when applied to the prompt pack.",
    )
    scene_template_profile: dict[str, Any] | None = Field(
        default=None,
        description="Copied serialized CatstyleSceneTemplate when applied to the prompt pack.",
    )
    render_style_profile_key: str | None = Field(
        default=None,
        description="From prompt pack render_style_profile.key when present.",
    )
    render_style_profile: dict[str, Any] | None = Field(
        default=None,
        description="Copied serialized CatstyleRenderStyleProfile when applied to the prompt pack.",
    )


class CatstyleImageGenerationJobsResult(BaseModel):
    """Result of ``build_catstyle_image_generation_jobs``."""

    date: str
    editorial_profile: str
    selected_candidate: dict[str, Any] | None = None
    secondary_supportive_candidate: dict[str, Any] | None = None
    manual_aspect_override: dict[str, Any] | None = Field(
        default=None,
        description="When set, jobs were built from explicit planet/aspect/mode override (v1).",
    )
    jobs: list[CatstyleImageGenJob] = Field(default_factory=list)
    output_dir: str | None = None
    manifest_path: str | None = None
    files_written: list[str] = Field(default_factory=list)
    message: str | None = None
    style_reference_meta: dict[str, Any] | None = Field(
        default=None,
        description="How the style reference path was chosen: explicit CLI, approved registry v1, or none.",
    )
    arena_reference_meta: dict[str, Any] | None = Field(
        default=None,
        description="How the arena/environment reference path was chosen: explicit CLI, arena registry v1, or none.",
    )
    planet_references_meta: dict[str, Any] | None = Field(
        default=None,
        description="Resolved per-planet character references for planet_a and planet_b.",
    )


def _write_utf8_text(path: Path, body: str) -> None:
    """Write UTF-8 text with trailing newline normalization."""
    path.write_text((body or "").rstrip("\n") + "\n", encoding="utf-8")


def _write_utf8_json(path: Path, payload: dict[str, Any]) -> None:
    """Write UTF-8 JSON preserving Unicode glyphs."""
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _strip_opt(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def parse_manual_aspect_override_fields(
    planet_a: str | None,
    planet_b: str | None,
    aspect_type: str | None,
    mode: str | None,
) -> tuple[str, str, str, str] | None:
    """
    Return ``(planet_a, planet_b, aspect_type_lowercase, mode_lowercase)`` when all four are set.

    Return ``None`` when all are absent. Raise ``ValueError`` on partial input or invalid ``mode``.
    """
    pa = _strip_opt(planet_a)
    pb = _strip_opt(planet_b)
    asp = _strip_opt(aspect_type)
    mo = _strip_opt(mode)
    filled = sum(1 for x in (pa, pb, asp, mo) if x)
    if filled == 0:
        return None
    if filled != 4:
        missing: list[str] = []
        if not pa:
            missing.append("--planet-a")
        if not pb:
            missing.append("--planet-b")
        if not asp:
            missing.append("--aspect-type")
        if not mo:
            missing.append("--mode")
        raise ValueError(
            "Manual aspect override requires all four flags together: "
            "--planet-a, --planet-b, --aspect-type, --mode. "
            f"Missing or empty: {', '.join(missing)}."
        )
    mode_l = mo.lower()
    if mode_l not in ("tension", "compensation", "mixed", "flow"):
        raise ValueError(
            "manual aspect override --mode must be one of: tension, compensation, mixed, flow "
            f"(got {mo!r})."
        )
    assert pa is not None and pb is not None and asp is not None
    return (pa, pb, asp.lower(), mode_l)


def _synthetic_primary_manual_override(pa: str, pb: str, asp: str, mode: str) -> dict[str, Any]:
    return {
        "planet_a": pa,
        "planet_b": pb,
        "aspect_type": asp,
        "mode_recommendation": mode,
        "total_score": 0,
        "source": "manual_override",
        "orb": None,
        "editorial_selection_score": None,
        "manual_aspect_override": True,
        "aspect_source": DEFAULT_FORCED_ASPECT_SOURCE,
    }


def _manual_aspect_override_manifest_block(pa: str, pb: str, asp: str, mode: str) -> dict[str, Any]:
    return {
        "enabled": True,
        "planet_a": pa,
        "planet_b": pb,
        "aspect_type": asp,
        "mode": mode,
        "aspect_source": DEFAULT_FORCED_ASPECT_SOURCE,
    }


def _merge_arena_reference_into_prompt_pack_dict(
    pp: dict[str, Any],
    *,
    arena_path: str,
    arena_meta: dict[str, Any],
) -> dict[str, Any]:
    """Ensure pack prompts include arena block when a reference path resolved."""
    if pp.get("arena_reference_assist"):
        return pp
    first = str((pp.get("image_prompts") or [""])[0])
    if "[CATSTYLE APPROVED ARENA REFERENCE v1]" in first:
        return pp
    hit = ResolvedArenaReference(
        registry_key=str(arena_meta.get("arena_reference_registry_key") or "explicit"),
        image_path=Path(arena_path),
        label=str(arena_meta.get("label") or ""),
        notes=str(arena_meta.get("notes") or ""),
        priority=int(arena_meta.get("priority") or 0),
    )
    pack = apply_approved_arena_reference_to_prompt_pack(CatstylePromptPack.model_validate(pp), hit)
    return dict(pack.model_dump(mode="json"))


def _arena_reference_log_lines(meta: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if meta.get("arena_reference_used"):
        lines.append("arena_reference_used: true")
    if meta.get("arena_reference_registry_key"):
        lines.append(f"arena_reference_registry_key: {meta.get('arena_reference_registry_key')}")
    if meta.get("arena_reference_image_path"):
        lines.append(f"arena_reference_image_path: {meta.get('arena_reference_image_path')}")
    for log_line in meta.get("log_lines") or []:
        if log_line:
            lines.append(str(log_line))
    return lines


def _style_reference_log_lines(meta: dict[str, Any]) -> list[str]:
    return list(meta.get("log_lines") or [])


def _resolve_final_style_reference(
    *,
    explicit_path: str | None,
    disable_approved_reference_auto: bool,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
) -> tuple[str | None, dict[str, Any]]:
    """Return ``(path_or_none, meta)`` — exact approved → archetype → none."""
    return resolve_style_reference(
        explicit_path=explicit_path,
        disable_approved_reference_auto=disable_approved_reference_auto,
        planet_a=planet_a,
        planet_b=planet_b,
        aspect_type=aspect_type,
        mode=mode,
    )


def _planet_reference_log_lines(meta: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for slot in ("planet_a", "planet_b"):
        row = meta.get(slot) if isinstance(meta.get(slot), dict) else None
        if not row:
            continue
        if row.get("used"):
            lines.append(
                f"{slot}: {row.get('planet')} registry_key={row.get('registry_key')} path={row.get('image_path')}"
            )
        else:
            lines.append(f"{slot}: missing ({row.get('missing_reason') or row.get('source')})")
    return lines


def _manifest_summary_text(
    *,
    date: str,
    editorial_profile: str,
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
    jobs: list[CatstyleImageGenJob],
    output_dir: Path,
    manual_aspect_override: dict[str, Any] | None = None,
    style_reference: dict[str, Any] | None = None,
    planet_references: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = [
        f"Catstyle image generation jobs v0 — {date}",
        f"Editorial profile: {editorial_profile}",
        f"Output directory: {output_dir}",
        f"Total jobs: {len(jobs)}",
        "",
    ]
    if style_reference:
        src = style_reference.get("source")
        lines.extend(
            [
                "## Style reference (v1)",
                f"source: {src}",
            ]
        )
        tier = style_reference.get("reference_tier")
        if tier:
            lines.append(f"reference_tier: {tier}")
        if style_reference.get("exact_reference_used") is not None:
            lines.append(f"exact_reference_used: {style_reference.get('exact_reference_used')}")
        if style_reference.get("archetype_reference_used") is not None:
            lines.append(f"archetype_reference_used: {style_reference.get('archetype_reference_used')}")
        if style_reference.get("archetype_key"):
            lines.append(f"archetype_key: {style_reference.get('archetype_key')}")
        if style_reference.get("approved_reference_used") is not None:
            lines.append(f"approved_reference_used: {style_reference.get('approved_reference_used')}")
        if style_reference.get("approved_reference_registry_key"):
            lines.append(f"approved_reference_registry_key: {style_reference.get('approved_reference_registry_key')}")
        if style_reference.get("approved_reference_image_path"):
            lines.append(f"approved_reference_image_path: {style_reference.get('approved_reference_image_path')}")
        if style_reference.get("style_reference_image_path"):
            lines.append(f"style_reference_image_path: {style_reference.get('style_reference_image_path')}")
        elif style_reference.get("path"):
            lines.append(f"path: {style_reference.get('path')}")
        if style_reference.get("registry_key"):
            lines.append(f"registry_key: {style_reference.get('registry_key')}")
        if style_reference.get("label"):
            lines.append(f"label: {style_reference.get('label')}")
        if style_reference.get("auto_resolve_disabled"):
            lines.append("auto_resolve_disabled: true")
        for log_line in style_reference.get("log_lines") or []:
            lines.append(log_line)
        lines.append("")
    if planet_references:
        lines.extend(["## Planet references (v1)"])
        lines.extend(_planet_reference_log_lines(planet_references))
        lines.append("")
    if manual_aspect_override:
        lines.extend(
            [
                "## Manual aspect override (v1)",
                f"planet_a={manual_aspect_override.get('planet_a')}  planet_b={manual_aspect_override.get('planet_b')}  "
                f"aspect_type={manual_aspect_override.get('aspect_type')}  mode={manual_aspect_override.get('mode')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Primary selected aspect",
        ]
    )
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
    world_template_key: str | None = None,
    scene_template_key: str | None = None,
    render_style_profile_key: str | None = None,
    shot_mode: str | None = None,
    style_reference_image_path: str | None = None,
    arena_reference_image_path: str | None = None,
    use_arena_reference_auto: bool = True,
    disable_arena_reference_auto: bool = False,
    planet_a_override: str | None = None,
    planet_b_override: str | None = None,
    aspect_type_override: str | None = None,
    mode_override: str | None = None,
    disable_approved_reference_auto: bool = False,
    jobs_count: int | None = None,
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleImageGenerationJobsResult:
    """
    Build deterministic image-generation job records from a Catstyle daily pack.

    When ``planet_a_override``, ``planet_b_override``, ``aspect_type_override``, and ``mode_override``
    are all set, skips sky-scan aspect selection and builds prompts directly for that aspect (v1).

    ``jobs_count`` (1 or 2): emit exactly this many jobs from the primary prompt pack. ``None`` keeps
    legacy behavior (one job per prompt line returned by the pack, typically two).

    Does not call OpenAI, Cloudinary, or Instagram.
    """
    if jobs_count is not None and jobs_count not in (1, 2):
        raise ValueError("jobs_count must be 1, 2, or omitted (None); got " + repr(jobs_count))
    skin_a_c = str(skin_a).strip() if skin_a else None
    skin_b_c = str(skin_b).strip() if skin_b else None
    if skin_a_c == "":
        skin_a_c = None
    if skin_b_c == "":
        skin_b_c = None

    world_k = str(world_template_key).strip() if world_template_key else None
    scene_k = str(scene_template_key).strip() if scene_template_key else None
    if world_k == "":
        world_k = None
    if scene_k == "":
        scene_k = None

    render_k = str(render_style_profile_key).strip() if render_style_profile_key else None
    if render_k == "":
        render_k = None

    shot_m = str(shot_mode).strip().lower() if shot_mode else None
    if shot_m == "":
        shot_m = None
    style_ref_cli = str(style_reference_image_path).strip() if style_reference_image_path else None
    if style_ref_cli == "":
        style_ref_cli = None
    arena_ref_cli = str(arena_reference_image_path).strip() if arena_reference_image_path else None
    if arena_ref_cli == "":
        arena_ref_cli = None

    override_quad = parse_manual_aspect_override_fields(
        planet_a_override,
        planet_b_override,
        aspect_type_override,
        mode_override,
    )
    manual_block: dict[str, Any] | None = None
    secondary: dict[str, Any] | None = None
    sky_weather_stack: dict[str, Any] | None = None
    iso: str
    profile: str
    primary: dict[str, Any]
    pp: dict[str, Any]
    style_reference_meta: dict[str, Any] | None = None
    arena_reference_meta: dict[str, Any] | None = None
    final_arena_ref: str | None = None
    manifest_sky_scan_mode: str | None = None
    manifest_sky_scan_step: int | None = None
    manifest_aspect_source: str = DEFAULT_FORCED_ASPECT_SOURCE

    if override_quad is not None:
        o_pa, o_pb, o_asp, o_mode = override_quad
        pa_n = normalize_planet_name(o_pa)
        pb_n = normalize_planet_name(o_pb)
        profile = normalize_editorial_profile(editorial_profile)
        iso = day.isoformat()
        manual_block = _manual_aspect_override_manifest_block(pa_n, pb_n, o_asp, o_mode)
        primary = _synthetic_primary_manual_override(pa_n, pb_n, o_asp, o_mode)
        final_ref, style_reference_meta = _resolve_final_style_reference(
            explicit_path=style_ref_cli,
            disable_approved_reference_auto=disable_approved_reference_auto,
            planet_a=pa_n,
            planet_b=pb_n,
            aspect_type=o_asp,
            mode=o_mode,
        )
        final_arena_ref, arena_reference_meta = resolve_arena_reference(
            explicit_path=arena_ref_cli,
            disable_arena_reference_auto=disable_arena_reference_auto,
            use_arena_reference_auto=use_arena_reference_auto,
        )
        vc_manual = 2 if jobs_count is None else jobs_count
        req_kw: dict[str, Any] = dict(
            planet_a=pa_n,
            planet_b=pb_n,
            aspect_type=o_asp,
            mode=o_mode,
            variants_count=vc_manual,
            skin_a=skin_a_c,
            skin_b=skin_b_c,
            editorial_profile=profile,
            world_template_key=world_k,
            scene_template_key=scene_k,
        )
        if shot_m is not None:
            req_kw["shot_mode"] = shot_m
        if render_k is not None:
            req_kw["render_style_profile_key"] = render_k
        req_kw["disable_approved_reference_prompt_lock"] = disable_approved_reference_auto
        req_kw["arena_reference_image_path"] = arena_ref_cli
        req_kw["use_arena_reference_auto"] = use_arena_reference_auto
        req_kw["disable_arena_reference_auto"] = disable_arena_reference_auto
        if final_ref:
            pa_chk = pa_n.lower()
            pb_chk = pb_n.lower()
            if "mars" not in {pa_chk, pb_chk}:
                req_kw["mars_heavy_style_reference_finisher"] = True
        try:
            req = CatstylePromptRequest(**req_kw)
            pack_obj = generate_catstyle_prompt_pack(req)
        except ValueError as e:
            raise ValueError(f"Cannot build prompts for manual aspect override: {e}") from e
        pp = dict(pack_obj.model_dump(mode="json"))
        if final_arena_ref and arena_reference_meta:
            pp = _merge_arena_reference_into_prompt_pack_dict(
                pp, arena_path=final_arena_ref, arena_meta=arena_reference_meta
            )
        sm_manual = str(scan_mode).strip().lower()
        if sm_manual == "day-window":
            manifest_sky_scan_mode = "day-window"
            manifest_sky_scan_step = max(1, int(step_hours))
            merge_manual_override_day_window_into_primary(
                primary,
                day=day,
                request_planet_a=pa_n,
                request_planet_b=pb_n,
                request_aspect_type=o_asp,
                step_hours=max(1, int(step_hours)),
                compute_positions_fn=compute_positions_fn,
                orb_config=orb_config,
            )
        else:
            manifest_sky_scan_mode = "manual_override"
            manifest_sky_scan_step = None
            primary["manual_override_sky_timing_match"] = False
    else:
        pack = generate_catstyle_daily_pack(
            day,
            top=top,
            scan_mode=scan_mode,
            step_hours=step_hours,
            editorial_profile=editorial_profile,
            skin_a=skin_a_c,
            skin_b=skin_b_c,
            world_template_key=world_k,
            scene_template_key=scene_k,
            render_style_profile_key=render_k,
            shot_mode=shot_m,
            compute_positions_fn=compute_positions_fn,
            orb_config=orb_config,
        )

        iso = pack.date
        profile = pack.editorial_profile
        sm = str(scan_mode).strip().lower()
        manifest_sky_scan_mode = sm
        manifest_sky_scan_step = int(step_hours) if sm == "day-window" else None

        if pack.selected_count == 0 or not pack.selected_candidates or not pack.prompt_packs:
            return CatstyleImageGenerationJobsResult(
                date=iso,
                editorial_profile=profile,
                selected_candidate=None,
                secondary_supportive_candidate=pack.secondary_supportive_candidate,
                manual_aspect_override=None,
                jobs=[],
                message="No Catstyle-selected candidates for this date/scan; no image jobs created.",
                style_reference_meta=None,
            )

        primary = dict(pack.selected_candidates[0])
        primary["aspect_source"] = "sky_current"
        pp = dict(pack.prompt_packs[0])
        secondary = pack.secondary_supportive_candidate
        sky_weather_stack = pack.sky_weather_stack
        manifest_aspect_source = "sky_current"

        pa_sel = normalize_planet_name(str(primary["planet_a"]))
        pb_sel = normalize_planet_name(str(primary["planet_b"]))
        asp_sel = str(primary["aspect_type"])
        mode_sel = str(primary["mode_recommendation"])
        final_ref, style_reference_meta = _resolve_final_style_reference(
            explicit_path=style_ref_cli,
            disable_approved_reference_auto=disable_approved_reference_auto,
            planet_a=pa_sel,
            planet_b=pb_sel,
            aspect_type=asp_sel,
            mode=mode_sel,
        )
        final_arena_ref, arena_reference_meta = resolve_arena_reference(
            explicit_path=arena_ref_cli,
            disable_arena_reference_auto=disable_arena_reference_auto,
            use_arena_reference_auto=use_arena_reference_auto,
        )

        if final_ref:
            pa_chk = pa_sel.lower()
            pb_chk = pb_sel.lower()
            if "mars" not in {pa_chk, pb_chk}:
                n_img = len(pp.get("image_prompts") or [])
                refresh_vc = jobs_count if jobs_count is not None else max(1, n_img)
                req_kw_refresh: dict[str, Any] = dict(
                    planet_a=pa_sel,
                    planet_b=pb_sel,
                    aspect_type=asp_sel,
                    mode=mode_sel,
                    variants_count=refresh_vc,
                    skin_a=skin_a_c,
                    skin_b=skin_b_c,
                    editorial_profile=profile,
                    world_template_key=world_k,
                    scene_template_key=scene_k,
                    mars_heavy_style_reference_finisher=True,
                )
                if shot_m is not None:
                    req_kw_refresh["shot_mode"] = shot_m
                if render_k is not None:
                    req_kw_refresh["render_style_profile_key"] = render_k
                req_kw_refresh["disable_approved_reference_prompt_lock"] = disable_approved_reference_auto
                req_kw_refresh["arena_reference_image_path"] = arena_ref_cli
                req_kw_refresh["use_arena_reference_auto"] = use_arena_reference_auto
                req_kw_refresh["disable_arena_reference_auto"] = disable_arena_reference_auto
                pp = generate_catstyle_prompt_pack(CatstylePromptRequest(**req_kw_refresh)).model_dump(
                    mode="json"
                )

    if final_arena_ref and arena_reference_meta:
        pp = _merge_arena_reference_into_prompt_pack_dict(
            pp, arena_path=final_arena_ref, arena_meta=arena_reference_meta
        )

    image_prompts: list[str] = [str(p) for p in (pp.get("image_prompts") or [])]
    neg = str(pp.get("negative_prompt", ""))
    anim = str(pp.get("animation_prompt", ""))
    carousel = str(pp.get("carousel_idea", ""))
    art_meta = pp.get("art_direction_profile")
    art_direction_profile = art_meta if isinstance(art_meta, dict) else None
    glyph_assist = pp.get("banner_glyph_reference_assist")
    glyph_a_path: str | None = None
    glyph_b_path: str | None = None
    if isinstance(glyph_assist, dict):
        raw_a = glyph_assist.get("banner_glyph_reference_planet_a_path")
        raw_b = glyph_assist.get("banner_glyph_reference_planet_b_path")
        glyph_a_path = str(raw_a).strip() if raw_a else None
        glyph_b_path = str(raw_b).strip() if raw_b else None

    w_prof = pp.get("world_template_profile")
    world_template_profile = w_prof if isinstance(w_prof, dict) else None
    world_template_key = (
        str(world_template_profile["template_key"]) if world_template_profile and "template_key" in world_template_profile else None
    )

    s_prof = pp.get("scene_template_profile")
    scene_template_profile = s_prof if isinstance(s_prof, dict) else None
    scene_template_key = (
        str(scene_template_profile["template_key"]) if scene_template_profile and "template_key" in scene_template_profile else None
    )

    rs_prof = pp.get("render_style_profile")
    render_style_profile = rs_prof if isinstance(rs_prof, dict) else None
    render_style_profile_key = (
        str(render_style_profile["key"]) if render_style_profile and "key" in render_style_profile else None
    )

    shot_roles_list_raw = pp.get("image_prompt_shot_roles")
    shot_roles_list: list[str | None] = (
        list(shot_roles_list_raw) if isinstance(shot_roles_list_raw, list) else []
    )

    if jobs_count is not None:
        if len(image_prompts) < jobs_count:
            raise ValueError(
                f"jobs_count={jobs_count} requires at least {jobs_count} image prompt(s); "
                f"pack has {len(image_prompts)}."
            )
        image_prompts = image_prompts[:jobs_count]
        if shot_roles_list:
            shot_roles_list = shot_roles_list[:jobs_count]

    vpp = max(1, int(variants_per_prompt))
    pa = str(primary["planet_a"])
    pb = str(primary["planet_b"])
    aspect = str(primary["aspect_type"])
    mode = str(primary["mode_recommendation"])
    planet_references_meta = resolve_planet_references_for_pair(pa, pb)
    planet_a_ref_path: str | None = None
    planet_b_ref_path: str | None = None
    pa_row = planet_references_meta.get("planet_a") or {}
    pb_row = planet_references_meta.get("planet_b") or {}
    if isinstance(pa_row, dict) and pa_row.get("used") and pa_row.get("image_path"):
        planet_a_ref_path = str(pa_row["image_path"])
    if isinstance(pb_row, dict) and pb_row.get("used") and pb_row.get("image_path"):
        planet_b_ref_path = str(pb_row["image_path"])
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
        shot_role = shot_roles_list[pi] if pi < len(shot_roles_list) else None
        if isinstance(shot_role, str):
            shot_role = shot_role.strip() or None
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
                    shot_role=shot_role,
                    style_reference_image_path=final_ref,
                    arena_reference_image_path=final_arena_ref,
                    planet_a_reference_image_path=planet_a_ref_path,
                    planet_b_reference_image_path=planet_b_ref_path,
                    banner_glyph_reference_planet_a_path=glyph_a_path,
                    banner_glyph_reference_planet_b_path=glyph_b_path,
                    prompt_text=prompt_text,
                    negative_prompt=neg,
                    animation_prompt=anim,
                    carousel_idea=carousel,
                    suggested_output_name=suggested,
                    status="pending",
                    art_direction_profile=art_direction_profile,
                    world_template_key=world_template_key,
                    scene_template_key=scene_template_key,
                    world_template_profile=world_template_profile,
                    scene_template_profile=scene_template_profile,
                    render_style_profile_key=render_style_profile_key,
                    render_style_profile=render_style_profile,
                )
            )

    if not jobs:
        return CatstyleImageGenerationJobsResult(
            date=iso,
            editorial_profile=profile,
            selected_candidate=primary,
            secondary_supportive_candidate=dict(secondary) if secondary else None,
            manual_aspect_override=manual_block,
            jobs=[],
            message="Primary prompt pack had no image_prompts lines; no jobs created.",
            style_reference_meta=style_reference_meta,
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
            "sky_scan_mode": manifest_sky_scan_mode,
            "sky_scan_step_hours_utc": manifest_sky_scan_step,
            "selected_candidate": primary,
            "secondary_supportive_candidate": secondary,
            "jobs": [j.model_dump(mode="json") for j in jobs],
        }
        if sky_weather_stack is not None and manifest_aspect_source == "sky_current":
            manifest["sky_weather_stack"] = sky_weather_stack
        annotate_manifest_aspect_source(manifest, normalize_aspect_source(manifest_aspect_source))
        if manifest_aspect_source == "sky_current":
            sky_mode = infer_sky_timing_mode_from_manifest(
                manifest, manifest_aspect_source
            )
            annotate_manifest_sky_timing_mode(manifest, sky_mode)
        if manual_block is not None:
            manifest["manual_aspect_override"] = manual_block
        if style_reference_meta is not None:
            manifest["style_reference"] = style_reference_meta
        if arena_reference_meta is not None:
            manifest["arena_reference"] = arena_reference_meta
        manifest["planet_references"] = planet_references_meta
        mp = out / "image_generation_jobs.json"
        _write_utf8_json(mp, manifest)
        manifest_path = str(mp)
        files_written.append("image_generation_jobs.json")

        width = max(2, len(str(len(jobs))))
        for i, job in enumerate(jobs, start=1):
            fname = f"job_{i:0{width}d}_prompt.txt"
            _write_utf8_text(out / fname, job.prompt_text or "")
            files_written.append(fname)

        _write_utf8_text(out / "negative_prompt.txt", neg)
        files_written.append("negative_prompt.txt")
        _write_utf8_text(out / "animation_prompt.txt", anim)
        files_written.append("animation_prompt.txt")
        summary = _manifest_summary_text(
            date=iso,
            editorial_profile=profile,
            primary=primary,
            secondary=dict(secondary) if secondary else None,
            jobs=jobs,
            output_dir=out,
            manual_aspect_override=manual_block,
            style_reference=style_reference_meta,
            planet_references=planet_references_meta,
        )
        _write_utf8_text(out / "manifest_summary.txt", summary)
        files_written.append("manifest_summary.txt")

    build_message: str | None = None
    build_lines: list[str] = []
    if style_reference_meta and style_reference_meta.get("reference_tier") in ("exact", "archetype"):
        build_lines.extend(_style_reference_log_lines(style_reference_meta))
    if arena_reference_meta and arena_reference_meta.get("arena_reference_used"):
        build_lines.extend(_arena_reference_log_lines(arena_reference_meta))
    if planet_references_meta:
        build_lines.extend(_planet_reference_log_lines(planet_references_meta))
    if build_lines:
        build_message = "; ".join(build_lines)

    return CatstyleImageGenerationJobsResult(
        date=iso,
        editorial_profile=profile,
        selected_candidate=primary,
        secondary_supportive_candidate=dict(secondary) if secondary else None,
        manual_aspect_override=manual_block,
        jobs=jobs,
        output_dir=out_resolved,
        manifest_path=manifest_path,
        files_written=files_written,
        message=build_message,
        style_reference_meta=style_reference_meta,
        arena_reference_meta=arena_reference_meta,
        planet_references_meta=planet_references_meta,
    )


__all__ = [
    "CatstyleImageGenJob",
    "CatstyleImageGenerationJobsResult",
    "build_catstyle_image_generation_jobs",
    "parse_manual_aspect_override_fields",
]
