"""Catstyle daily pack: sky scan + top ranked prompt packs (text only)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.content.catstyle.models import CatstyleDailyPackResult, CatstylePromptRequest
from astro_content_agent.services.content.catstyle_editorial_selection import (
    EDITORIAL_PROFILE_DEFAULT,
    EditorialProfile,
    candidate_to_editorial_dict,
    normalize_editorial_profile,
    pick_secondary_supportive_for_charged,
    sort_candidates_for_editorial_profile,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack
from astro_content_agent.services.content.catstyle_sky_aspect_scan import (
    scan_catstyle_sky_aspect_windows,
    scan_catstyle_sky_aspects,
)


def generate_catstyle_daily_pack(
    day: date,
    top: int = 1,
    scan_mode: str = "day-window",
    step_hours: int = 2,
    editorial_profile: str = EDITORIAL_PROFILE_DEFAULT,
    skin_a: str | None = None,
    skin_b: str | None = None,
    world_template_key: str | None = None,
    scene_template_key: str | None = None,
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleDailyPackResult:
    """
    Run sky scan (noon or full UTC day window), rank intrinsically, then select top *top*
    by ``editorial_profile`` (charged / balanced / supportive), and build a ``CatstylePromptPack``
    for each selected row using ``mode_recommendation``.

    Optional ``skin_a`` / ``skin_b`` are passed through to ``CatstylePromptRequest`` (character_skins v0).
    Optional ``world_template_key`` / ``scene_template_key`` map to world/scene templates v1 when set.
    """
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

    mode = str(scan_mode).strip().lower()
    if mode not in ("noon", "day-window"):
        raise ValueError("scan_mode must be 'noon' or 'day-window'")

    step: int | None
    if mode == "noon":
        ranking = scan_catstyle_sky_aspects(day, compute_positions_fn=compute_positions_fn, orb_config=orb_config)
        step = None
    else:
        ranking = scan_catstyle_sky_aspect_windows(
            day,
            step_hours=step_hours,
            compute_positions_fn=compute_positions_fn,
            orb_config=orb_config,
        )
        step = max(1, int(step_hours))

    profile: EditorialProfile = normalize_editorial_profile(str(editorial_profile))

    ranked_list = list(ranking.ranked)
    ranked_dicts = [c.model_dump(mode="json") for c in ranked_list]

    n = max(0, int(top))
    if profile == "balanced":
        editorial_ordered = ranked_list
    else:
        editorial_ordered = sort_candidates_for_editorial_profile(ranked_list, profile)

    selected = editorial_ordered[:n]

    sel_dicts: list[dict] = []
    packs: list[dict] = []
    for c in selected:
        req = CatstylePromptRequest(
            planet_a=c.planet_a,
            planet_b=c.planet_b,
            aspect_type=c.aspect_type,
            mode=c.mode_recommendation,
            variants_count=4,
            skin_a=skin_a_c,
            skin_b=skin_b_c,
            editorial_profile=profile,
            world_template_key=world_k,
            scene_template_key=scene_k,
        )
        pack = generate_catstyle_prompt_pack(req)
        sel_dicts.append(candidate_to_editorial_dict(c, profile))
        packs.append(pack.model_dump(mode="json"))

    primary = sel_dicts[0] if sel_dicts else None
    secondary: dict | None = None
    if profile == "charged" and selected:
        sec_c = pick_secondary_supportive_for_charged(ranked_list, selected[0])
        if sec_c is not None:
            secondary = candidate_to_editorial_dict(sec_c, "supportive")

    return CatstyleDailyPackResult(
        date=day.isoformat(),
        scan_mode=mode,  # type: ignore[arg-type]
        step_hours=step,
        editorial_profile=profile,
        ranked_candidates_count=len(ranking.ranked),
        selected_count=len(selected),
        ranked_candidates=ranked_dicts,
        selected_candidates=sel_dicts,
        prompt_packs=packs,
        primary_candidate=primary,
        secondary_supportive_candidate=secondary,
    )


__all__ = ["generate_catstyle_daily_pack"]
