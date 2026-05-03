"""Catstyle v0: daily pack → production handoff artifact (Markdown / JSON, no images)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date

from pydantic import BaseModel, Field

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.services.content.catstyle_daily_pack import generate_catstyle_daily_pack

NEXT_STEPS_CHECKLIST_V0: tuple[str, ...] = (
    "Generate 4 image options from prompts",
    "Pick best image",
    "Animate in CapCut if reel",
    "Upload final image/video to Cloudinary",
    "Publish via existing Instagram flow",
)


class CatstyleHandoffCandidateSummary(BaseModel):
    planet_a: str
    planet_b: str
    aspect_type: str
    orb: float | None = None
    window_first_seen_hour_utc: int | None = None
    window_last_seen_hour_utc: int | None = None
    closest_hour_utc: int | None = None
    window_samples_seen: int | None = None
    is_moon_aspect: bool = False
    total_score: int
    mode_recommendation: str
    source: str
    recommended_scene_angle: str


class CatstyleHandoffProductionPlan(BaseModel):
    recommended_format: str
    image_generation_notes: str
    capcut_animation_notes: str
    manual_review_notes: str


class CatstyleHandoffItem(BaseModel):
    candidate: CatstyleHandoffCandidateSummary
    why_this_post: str
    production_plan: CatstyleHandoffProductionPlan
    image_prompts: list[str]
    animation_prompt: str
    negative_prompt: str
    carousel_idea: str
    caption_draft: str


class CatstyleDailyHandoff(BaseModel):
    date: str
    scan_mode: str
    step_hours: int | None = None
    ranked_candidates_count: int
    selected_count: int
    no_post_reason: str | None = None
    items: list[CatstyleHandoffItem] = Field(default_factory=list)
    next_steps_checklist: list[str] = Field(default_factory=lambda: list(NEXT_STEPS_CHECKLIST_V0))


def _window_line(c: CatstyleHandoffCandidateSummary) -> str:
    if c.window_samples_seen is None:
        return "n/a (noon snapshot or no window metadata)"
    parts = [
        f"UTC {c.window_first_seen_hour_utc}h-{c.window_last_seen_hour_utc}h",
        f"samples={c.window_samples_seen}",
    ]
    if c.closest_hour_utc is not None:
        parts.append(f"closest_hour_utc={c.closest_hour_utc}")
    if c.is_moon_aspect:
        parts.append("fast Moon aspect")
    return "; ".join(parts)


def _why_this_post(c: CatstyleHandoffCandidateSummary) -> str:
    bits = [
        f"Catstyle score {c.total_score} prioritizes this {c.planet_a}+{c.planet_b} {c.aspect_type} beat for the feed.",
        f"Mode {c.mode_recommendation} with {c.source} framing matches the ranked visual read.",
    ]
    if c.orb is not None:
        bits.append(f"Tight sky orb (~{c.orb:.2f}°) keeps the beat literal for image gen.")
    if c.is_moon_aspect and c.window_samples_seen:
        bits.append("Moon moved across the UTC window—day-window scan caught the best slice.")
    return " ".join(bits)


def _production_plan(c: CatstyleHandoffCandidateSummary) -> CatstyleHandoffProductionPlan:
    hard = {"square", "opposition", "conjunction"}
    fmt = "carousel"
    if c.mode_recommendation == "tension" and (c.is_moon_aspect or c.aspect_type in hard):
        fmt = "reel or carousel (reel if you want a punchy Moon/tension hook)"
    elif c.mode_recommendation == "compensation":
        fmt = "carousel (soft payoff slide at the end)"

    img_notes = (
        "Catstyle: simple adult-cartoon planet-cats, thick black outlines, flat colors, dark starry sky, "
        "no on-image text, no logos, no photoreal glam. Generate four variants from the four prompts."
    )
    capcut = (
        "If animating: use the animation prompt as a 3–5s loop brief; keep silhouettes readable on phone; "
        "no readable text overlays in frame."
    )
    manual = (
        "Review negative prompt + seed/deep avoid lists before posting; check Moon fast-aspect caption if applicable."
    )
    return CatstyleHandoffProductionPlan(
        recommended_format=fmt,
        image_generation_notes=img_notes,
        capcut_animation_notes=capcut,
        manual_review_notes=manual,
    )


def _summary_from_candidate_dict(d: dict) -> CatstyleHandoffCandidateSummary:
    return CatstyleHandoffCandidateSummary(
        planet_a=str(d["planet_a"]),
        planet_b=str(d["planet_b"]),
        aspect_type=str(d["aspect_type"]),
        orb=d.get("orb"),
        window_first_seen_hour_utc=d.get("window_first_seen_hour_utc"),
        window_last_seen_hour_utc=d.get("window_last_seen_hour_utc"),
        closest_hour_utc=d.get("closest_hour_utc"),
        window_samples_seen=d.get("window_samples_seen"),
        is_moon_aspect=bool(d.get("is_moon_aspect", False)),
        total_score=int(d["total_score"]),
        mode_recommendation=str(d["mode_recommendation"]),
        source=str(d["source"]),
        recommended_scene_angle=str(d.get("recommended_scene_angle", "")),
    )


def _caption_draft(c: CatstyleHandoffCandidateSummary) -> str:
    moon = " (fast Moon window)" if c.is_moon_aspect else ""
    return (
        f"Transit beat: {c.planet_a} {c.aspect_type} {c.planet_b} — {c.mode_recommendation} mood, "
        f"Catstyle planet-cats under the stars.{moon} #Catstyle #AstroArt (draft—edit voice)."
    )


def build_catstyle_daily_handoff(
    day: date,
    top: int = 1,
    scan_mode: str = "day-window",
    step_hours: int = 2,
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleDailyHandoff:
    pack = generate_catstyle_daily_pack(
        day,
        top=top,
        scan_mode=scan_mode,
        step_hours=step_hours,
        compute_positions_fn=compute_positions_fn,
        orb_config=orb_config,
    )

    if pack.selected_count == 0:
        return CatstyleDailyHandoff(
            date=pack.date,
            scan_mode=pack.scan_mode,
            step_hours=pack.step_hours,
            ranked_candidates_count=pack.ranked_candidates_count,
            selected_count=0,
            no_post_reason="No Catstyle-ranked outer→personal aspects for this date/scan; nothing to hand off.",
            items=[],
        )

    items: list[CatstyleHandoffItem] = []
    for cand, pp in zip(pack.selected_candidates, pack.prompt_packs, strict=True):
        summary = _summary_from_candidate_dict(cand)
        items.append(
            CatstyleHandoffItem(
                candidate=summary,
                why_this_post=_why_this_post(summary),
                production_plan=_production_plan(summary),
                image_prompts=list(pp.get("image_prompts") or []),
                animation_prompt=str(pp.get("animation_prompt", "")),
                negative_prompt=str(pp.get("negative_prompt", "")),
                carousel_idea=str(pp.get("carousel_idea", "")),
                caption_draft=_caption_draft(summary),
            )
        )

    return CatstyleDailyHandoff(
        date=pack.date,
        scan_mode=pack.scan_mode,
        step_hours=pack.step_hours,
        ranked_candidates_count=pack.ranked_candidates_count,
        selected_count=pack.selected_count,
        items=items,
    )


def render_catstyle_daily_handoff_markdown(h: CatstyleDailyHandoff) -> str:
    """Render the handoff as Markdown for editors / CapCut / IG prep."""
    lines: list[str] = []
    lines.append(f"# Catstyle Daily Handoff - {h.date}")
    lines.append("")
    lines.append(f"- Scan: **{h.scan_mode}**" + (f" (step {h.step_hours}h UTC)" if h.step_hours else ""))
    lines.append(f"- Ranked candidates: **{h.ranked_candidates_count}** | Selected for pack: **{h.selected_count}**")
    lines.append("")

    if h.no_post_reason:
        lines.append("## No post")
        lines.append(h.no_post_reason)
        lines.append("")
        lines.append("## Production Checklist")
        for step in h.next_steps_checklist:
            lines.append(f"- [ ] {step}")
        return "\n".join(lines) + "\n"

    for idx, it in enumerate(h.items, start=1):
        c = it.candidate
        title = "## Selected Aspect" if len(h.items) == 1 else f"## Selected Aspect #{idx}"
        lines.append(title)
        lines.append(f"- Pair: **{c.planet_a} + {c.planet_b}**")
        lines.append(f"- Aspect: **{c.aspect_type}**")
        lines.append(f"- Mode: **{c.mode_recommendation}**")
        lines.append(f"- Score: **{c.total_score}**")
        lines.append(f"- Orb: **{c.orb}** deg" if c.orb is not None else "- Orb: **n/a**")
        lines.append(f"- Window: **{_window_line(c)}**")
        lines.append(f"- Source: **{c.source}**")
        lines.append(f"- Scene angle: {c.recommended_scene_angle}")
        lines.append("")
        lines.append("## Why this post")
        lines.append(it.why_this_post)
        lines.append("")
        lines.append("## Visual Direction")
        lines.append(f"- **Format:** {it.production_plan.recommended_format}")
        lines.append(f"- **Image gen:** {it.production_plan.image_generation_notes}")
        lines.append(f"- **CapCut:** {it.production_plan.capcut_animation_notes}")
        lines.append(f"- **Manual review:** {it.production_plan.manual_review_notes}")
        lines.append("")
        lines.append("## Image Prompts")
        for i, prompt in enumerate(it.image_prompts, start=1):
            lines.append(f"### Prompt {i}")
            lines.append(prompt)
            lines.append("")
        lines.append("## Animation Prompt")
        lines.append(it.animation_prompt)
        lines.append("")
        lines.append("## Negative Prompt")
        lines.append(it.negative_prompt)
        lines.append("")
        lines.append("## Carousel Idea")
        lines.append(it.carousel_idea)
        lines.append("")
        lines.append("## Caption Draft")
        lines.append(it.caption_draft)
        lines.append("")

    lines.append("## Production Checklist")
    for step in h.next_steps_checklist:
        lines.append(f"- [ ] {step}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "NEXT_STEPS_CHECKLIST_V0",
    "CatstyleDailyHandoff",
    "CatstyleHandoffItem",
    "build_catstyle_daily_handoff",
    "render_catstyle_daily_handoff_markdown",
]
