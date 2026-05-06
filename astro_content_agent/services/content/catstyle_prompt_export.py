"""Catstyle v0: export image-generation prompt text files from a daily pack (no API / no images)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.services.content.catstyle_daily_pack import generate_catstyle_daily_pack


class CatstylePromptExportResult(BaseModel):
    """Structured result from ``export_catstyle_image_prompts``."""

    date: str
    output_dir: str
    files_written: list[str] = Field(default_factory=list)
    selected_candidate: dict[str, Any] | None = None
    secondary_supportive_candidate: dict[str, Any] | None = None
    success: bool = True
    message: str | None = None


def _aspect_one_liner(c: dict[str, Any]) -> str:
    return (
        f"{c.get('planet_a')} {c.get('aspect_type')} {c.get('planet_b')}  "
        f"mode={c.get('mode_recommendation')}  source={c.get('source')}  "
        f"total_score={c.get('total_score')}  orb={c.get('orb')}"
    )


def _build_selected_aspect_summary(
    primary: dict[str, Any],
    secondary: dict[str, Any] | None,
    pack_date: str,
    editorial_profile: str,
) -> str:
    lines: list[str] = [
        f"Catstyle selected aspect summary (pack date {pack_date}, editorial_profile={editorial_profile})",
        "",
        "## Primary (exported prompts)",
        _aspect_one_liner(primary),
    ]
    if primary.get("recommended_scene_angle"):
        lines.extend(["", "Scene angle:", str(primary["recommended_scene_angle"])])
    if secondary:
        lines.extend(
            [
                "",
                "## Secondary supportive / compensation (same day)",
                _aspect_one_liner(secondary),
            ]
        )
        if secondary.get("recommended_scene_angle"):
            lines.extend(["", "Scene angle:", str(secondary["recommended_scene_angle"])])
    lines.append("")
    return "\n".join(lines)


def export_catstyle_image_prompts(
    day: date,
    output_dir: Path,
    top: int = 1,
    editorial_profile: str = "charged",
    scan_mode: str = "day-window",
    step_hours: int = 2,
    *,
    compute_positions_fn: Callable[..., dict[str, PlanetPosition]] | None = None,
    orb_config: dict[str, tuple[float, float]] | None = None,
) -> CatstylePromptExportResult:
    """
    Run ``generate_catstyle_daily_pack`` and write image-ready ``.txt`` files for the primary pack.

    Does not call image APIs, Cloudinary, or Instagram.
    """
    out = output_dir.expanduser().resolve()
    pack = generate_catstyle_daily_pack(
        day,
        top=top,
        scan_mode=scan_mode,
        step_hours=step_hours,
        editorial_profile=editorial_profile,
        compute_positions_fn=compute_positions_fn,
        orb_config=orb_config,
    )

    if pack.selected_count == 0 or not pack.prompt_packs or not pack.selected_candidates:
        return CatstylePromptExportResult(
            date=pack.date,
            output_dir=str(out),
            files_written=[],
            selected_candidate=None,
            secondary_supportive_candidate=pack.secondary_supportive_candidate,
            success=False,
            message="No Catstyle-selected candidates for this date/scan; nothing exported.",
        )

    out.mkdir(parents=True, exist_ok=True)

    primary = pack.selected_candidates[0]
    pp = pack.prompt_packs[0]
    secondary = pack.secondary_supportive_candidate

    image_prompts: list[str] = list(pp.get("image_prompts") or [])
    files_written: list[str] = []

    def _write_txt(name: str, body: str) -> None:
        normalized = (body or "").rstrip("\n") + "\n"
        (out / name).write_text(normalized, encoding="utf-8")
        files_written.append(name)

    for i, prompt_text in enumerate(image_prompts, start=1):
        _write_txt(f"prompt_{i}.txt", prompt_text)

    _write_txt("animation_prompt.txt", str(pp.get("animation_prompt", "")))
    _write_txt("negative_prompt.txt", str(pp.get("negative_prompt", "")))
    _write_txt("carousel_idea.txt", str(pp.get("carousel_idea", "")))

    summary_body = _build_selected_aspect_summary(
        primary,
        secondary,
        pack.date,
        pack.editorial_profile,
    )
    _write_txt("selected_aspect_summary.txt", summary_body.rstrip("\n"))

    return CatstylePromptExportResult(
        date=pack.date,
        output_dir=str(out),
        files_written=files_written,
        selected_candidate=dict(primary),
        secondary_supportive_candidate=dict(secondary) if secondary else None,
        success=True,
        message=None,
    )


__all__ = ["CatstylePromptExportResult", "export_catstyle_image_prompts"]
