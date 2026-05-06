"""Catstyle v0: daily pack → production handoff artifact (Markdown / JSON, no images)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date

from pydantic import BaseModel, Field

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.services.content.catstyle_daily_pack import generate_catstyle_daily_pack

NEXT_STEPS_CHECKLIST_V0: tuple[str, ...] = (
    "Generate 2 premium hero images from prompts (poster hero + alternate angle)",
    "Pick best hero frame",
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
    why_this_aspect_won: str
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
    editorial_profile: str = "charged"
    ranked_candidates_count: int
    selected_count: int
    no_post_reason: str | None = None
    items: list[CatstyleHandoffItem] = Field(default_factory=list)
    secondary_supportive_candidate: dict | None = None
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


def _why_this_aspect_won(profile: str, cand_dict: dict) -> str:
    pair = f"{cand_dict['planet_a']} {cand_dict['aspect_type']} {cand_dict['planet_b']}"
    bonus = cand_dict.get("editorial_bonus")
    sel = cand_dict.get("editorial_selection_score")
    total = cand_dict.get("total_score")
    score_tail = ""
    if bonus is not None and sel is not None and total is not None:
        score_tail = f" Intrinsic total_score={total}; editorial_bonus={bonus}; selection_score={sel}."
    if profile == "charged":
        return (
            "Editorial profile **charged** re-ranks toward conjunction, opposition, and square "
            "(trine small boost, sextile penalty) so a tight soft aspect does not automatically beat "
            f"a reasonably close hard aspect. Chosen primary: **{pair}**.{score_tail}"
        )
    if profile == "supportive":
        return (
            "Editorial profile **supportive** re-ranks toward trine and sextile with mild penalties on "
            f"square/opposition so compensation-forward beats read cleaner for softer campaigns. "
            f"Chosen primary: **{pair}**.{score_tail}"
        )
    return (
        "Editorial profile **balanced** keeps intrinsic Catstyle ordering (aspect strength, orb tightness, "
        f"deep/seed visual scores) with no extra editorial bias. Chosen primary: **{pair}**.{score_tail}"
    )


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


def _aspect_line_from_dict(d: dict) -> str:
    return f"{d.get('planet_a')} {d.get('aspect_type')} {d.get('planet_b')}"


def _supportive_compensation_section(sec: dict) -> list[str]:
    """Human-readable supportive / compensation angle from secondary candidate dict."""
    pair = _aspect_line_from_dict(sec)
    mode = sec.get("mode_recommendation", "compensation")
    src = sec.get("source", "")
    angle = str(sec.get("recommended_scene_angle", "")).strip()
    orb = sec.get("orb")
    lines: list[str] = [
        f"- **Pair:** {pair}",
        f"- **Mode:** {mode} (supportive read for integration / soften the hook)",
    ]
    if src:
        lines.append(f"- **Source:** {src}")
    if orb is not None:
        lines.append(f"- **Orb:** ~{float(orb):.2f}° (exact supportive geometry)")
    if angle:
        lines.append(f"- **Scene angle:** {angle}")
    sel = sec.get("editorial_selection_score")
    tot = sec.get("total_score")
    if sel is not None and tot is not None:
        lines.append(
            f"- **Editorial note:** supportive-ranking score **{sel}** (intrinsic total_score **{tot}**) "
            "— use for payoff, B-roll, or caption contrast to the main charged beat."
        )
    return lines


def _why_pairing_works(primary: CatstyleHandoffCandidateSummary, sec: dict) -> str:
    main = f"{primary.planet_a} {primary.aspect_type} {primary.planet_b}"
    soft = _aspect_line_from_dict(sec)
    return (
        f"The **{main}** beat carries tension and visual punch for the hook. **{soft}** offers a "
        "same-day compensation channel: viewers get the friction first, then a believable soft landing "
        "that still feels on-brand for Catstyle. Keep both in the same session so the story arc "
        "reads as one sky day, not two unrelated posts."
    )


def _suggested_carousel_structure_lines(primary: CatstyleHandoffCandidateSummary, sec: dict) -> list[str]:
    charged = f"{primary.planet_a}+{primary.planet_b} ({primary.aspect_type})"
    supportive = _aspect_line_from_dict(sec)
    return [
        f"- **Cover:** Lead with the main charged aspect — **{charged}** — bold read, clear conflict hook.",
        "- **Slide 1:** Introduce the charged conflict (what the two planet-cats are fighting / negotiating).",
        "- **Slide 2:** Visual escalation of the main aspect (bigger gesture, sharper contrast, same Catstyle rules).",
        "- **Slide 3:** What this feels like / behavioral pattern (name the tension in plain language, still visual).",
        f"- **Slide 4:** Supportive / compensation aspect — **{supportive}** — shift palette or posture toward relief.",
        "- **Final:** Practical integration / CTA (how to use the day constructively; soft close, no on-image text).",
    ]


def _charged_main_aspect_title(idx: int, n_items: int) -> str:
    if n_items == 1:
        return "## Main Charged Aspect"
    return f"## Main Charged Aspect #{idx}"


def build_catstyle_daily_handoff(
    day: date,
    top: int = 1,
    scan_mode: str = "day-window",
    step_hours: int = 2,
    editorial_profile: str = "charged",
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleDailyHandoff:
    pack = generate_catstyle_daily_pack(
        day,
        top=top,
        scan_mode=scan_mode,
        step_hours=step_hours,
        editorial_profile=editorial_profile,
        compute_positions_fn=compute_positions_fn,
        orb_config=orb_config,
    )

    if pack.selected_count == 0:
        return CatstyleDailyHandoff(
            date=pack.date,
            scan_mode=pack.scan_mode,
            step_hours=pack.step_hours,
            editorial_profile=pack.editorial_profile,
            ranked_candidates_count=pack.ranked_candidates_count,
            selected_count=0,
            no_post_reason="No Catstyle-ranked outer→personal aspects for this date/scan; nothing to hand off.",
            items=[],
            secondary_supportive_candidate=None,
        )

    items: list[CatstyleHandoffItem] = []
    for cand, pp in zip(pack.selected_candidates, pack.prompt_packs, strict=True):
        summary = _summary_from_candidate_dict(cand)
        items.append(
            CatstyleHandoffItem(
                candidate=summary,
                why_this_aspect_won=_why_this_aspect_won(pack.editorial_profile, cand),
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
        editorial_profile=pack.editorial_profile,
        ranked_candidates_count=pack.ranked_candidates_count,
        selected_count=pack.selected_count,
        items=items,
        secondary_supportive_candidate=pack.secondary_supportive_candidate,
    )


def render_catstyle_daily_handoff_markdown(h: CatstyleDailyHandoff) -> str:
    """Render the handoff as Markdown for editors / CapCut / IG prep."""
    lines: list[str] = []
    lines.append(f"# Catstyle Daily Handoff - {h.date}")
    lines.append("")
    lines.append(f"- Scan: **{h.scan_mode}**" + (f" (step {h.step_hours}h UTC)" if h.step_hours else ""))
    lines.append(f"- Editorial profile: **{h.editorial_profile}**")
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

    charged_secondary = (
        h.editorial_profile == "charged"
        and h.secondary_supportive_candidate is not None
        and len(h.items) == 1
    )

    def _append_main_aspect_bullets(c: CatstyleHandoffCandidateSummary) -> None:
        lines.append(f"- Pair: **{c.planet_a} + {c.planet_b}**")
        lines.append(f"- Aspect: **{c.aspect_type}**")
        lines.append(f"- Mode: **{c.mode_recommendation}**")
        lines.append(f"- Score: **{c.total_score}**")
        lines.append(f"- Orb: **{c.orb}** deg" if c.orb is not None else "- Orb: **n/a**")
        lines.append(f"- Window: **{_window_line(c)}**")
        lines.append(f"- Source: **{c.source}**")
        lines.append(f"- Scene angle: {c.recommended_scene_angle}")
        lines.append("")

    def _append_why_blocks(it: CatstyleHandoffItem) -> None:
        lines.append("## Why this aspect won")
        lines.append(it.why_this_aspect_won)
        lines.append("")
        lines.append("## Why this post")
        lines.append(it.why_this_post)
        lines.append("")

    def _append_visual_through_caption(it: CatstyleHandoffItem) -> None:
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
        lines.append("## Carousel Idea (from prompt pack)")
        lines.append(it.carousel_idea)
        lines.append("")
        lines.append("## Caption Draft")
        lines.append(it.caption_draft)
        lines.append("")

    if charged_secondary:
        it0 = h.items[0]
        c0 = it0.candidate
        sec = h.secondary_supportive_candidate
        lines.append("## Main Charged Aspect")
        _append_main_aspect_bullets(c0)
        _append_why_blocks(it0)
        lines.append("## Supportive / Compensation Aspect")
        lines.extend(_supportive_compensation_section(sec))
        lines.append("")
        lines.append("## Why this pairing works")
        lines.append(_why_pairing_works(c0, sec))
        lines.append("")
        lines.append("## Suggested Carousel Structure")
        lines.extend(_suggested_carousel_structure_lines(c0, sec))
        lines.append("")
        _append_visual_through_caption(it0)
    else:
        for idx, it in enumerate(h.items, start=1):
            c = it.candidate
            if h.editorial_profile == "charged":
                lines.append(_charged_main_aspect_title(idx, len(h.items)))
            else:
                lines.append("## Selected Aspect" if len(h.items) == 1 else f"## Selected Aspect #{idx}")
            _append_main_aspect_bullets(c)
            _append_why_blocks(it)
            _append_visual_through_caption(it)

        if h.secondary_supportive_candidate and h.editorial_profile != "charged":
            sec = h.secondary_supportive_candidate
            lines.append("## Secondary supportive candidate")
            lines.append(
                f"- **{sec.get('planet_a')} {sec.get('aspect_type')} {sec.get('planet_b')}** "
                f"(selection_score={sec.get('editorial_selection_score')}, total_score={sec.get('total_score')})."
            )
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
