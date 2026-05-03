"""Catstyle daily pack: sky scan + top ranked prompt packs (text only)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.content.catstyle.models import CatstyleDailyPackResult, CatstylePromptRequest
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
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstyleDailyPackResult:
    """
    Run sky scan (noon or full UTC day window), take top *top* ranked candidates,
    and build a ``CatstylePromptPack`` for each using ``mode_recommendation``.
    """
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

    n = max(0, int(top))
    selected = ranking.ranked[:n]

    sel_dicts: list[dict] = []
    packs: list[dict] = []
    for c in selected:
        req = CatstylePromptRequest(
            planet_a=c.planet_a,
            planet_b=c.planet_b,
            aspect_type=c.aspect_type,
            mode=c.mode_recommendation,
            variants_count=4,
        )
        pack = generate_catstyle_prompt_pack(req)
        sel_dicts.append(c.model_dump(mode="json"))
        packs.append(pack.model_dump(mode="json"))

    return CatstyleDailyPackResult(
        date=day.isoformat(),
        scan_mode=mode,  # type: ignore[arg-type]
        step_hours=step,
        ranked_candidates_count=len(ranking.ranked),
        selected_count=len(selected),
        selected_candidates=sel_dicts,
        prompt_packs=packs,
    )


__all__ = ["generate_catstyle_daily_pack"]
