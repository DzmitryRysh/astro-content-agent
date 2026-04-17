"""Weekly Venus Review Artifact — human-readable packaging for WeeklyVenusPackage.

Consumes output from ``VenusWeeklySelector`` only; does not change selector logic,
climate, or overlay layers. Produces:

- Markdown brief (editorial skim / weekly planning)
- Optional compact JSON (compare across weeks, CI, tooling)

Filenames (default stem): ``venus_weekly_review_<YYYY-MM-DD>.md`` / ``.json``
where the date is ``package.week_start``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from astro_content_agent.services.content.venus_weekly_selector import WeeklyVenusPackage


def _truncate(text: str, max_len: int = 220) -> str:
    t = text.strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def _climate_summary_lines(pkg: WeeklyVenusPackage) -> tuple[str, list[str], list[str]]:
    """Return (money one-liner, leak bullets, strength bullets)."""
    climate = pkg.climate_ctx.climate
    if not climate:
        return ("—", [], [])
    money = _truncate(climate.money_style, 240)
    comfort = _truncate(climate.comfort_style, 180)
    summary = f"{money} / {_truncate(comfort, 160)}"
    leaks = list(climate.likely_leak[:3])
    strengths = list(climate.likely_strength[:3])
    return (summary, leaks, strengths)


def _combined_pattern_one_line(pkg: WeeklyVenusPackage) -> str:
    if not pkg.overlay_ctx or not pkg.overlay_ctx.overlay.active:
        return "—"
    bullets = pkg.overlay_ctx.overlay.combined_pattern
    return bullets[0] if bullets else "—"


def _rationale_bullets(rationale: str, max_bullets: int = 5) -> list[str]:
    lines = [ln.strip() for ln in rationale.splitlines() if ln.strip()]
    return lines[:max_bullets]


def render_weekly_review_markdown(pkg: WeeklyVenusPackage) -> str:
    """Build a concise markdown editorial brief from a weekly package."""
    money_comfort, leaks, strengths = _climate_summary_lines(pkg)
    combined = _combined_pattern_one_line(pkg)
    rationale_lines = _rationale_bullets(pkg.selection_rationale)

    alt_line = ""
    if len(pkg.scored_overlays) >= 2:
        alt = pkg.scored_overlays[1]
        alt_line = (
            f"\n**Альтернатива:** `{alt.get('pair_key', '—')}` "
            f"(день {alt.get('day', '—')}, score={alt.get('score', 0):.2f}, orb={alt.get('orb', 0):.1f}°).\n"
        )

    notes_block = "\n".join(f"- {n}" for n in pkg.editorial_notes) if pkg.editorial_notes else "—"

    overlay_active = "да" if pkg.overlay_active else "нет"
    pair = pkg.overlay_pair or "—"
    mode = pkg.overlay_mode
    best = pkg.best_day.isoformat() if pkg.best_day else "—"
    hook = pkg.hook_family
    comp = pkg.compensation_focus

    table_rows = ""
    if pkg.scored_overlays:
        table_rows = "\n".join(
            f"| {c.get('day', '—')} | `{c.get('pair_key', '—')}` | {c.get('mode', '—')} | "
            f"{c.get('score', 0):.2f} | {c.get('orb', 0):.1f}° | "
            f"{'да' if c.get('has_curated_pattern') else 'нет'} |"
            for c in pkg.scored_overlays
        )
        overlay_table = (
            "| День | Пара | Режим | Score | Орб | Curated |\n"
            "|------|------|-------|-------|-----|--------|\n"
            f"{table_rows}\n"
        )
    else:
        overlay_table = "_Нет кандидатов оверлея за неделю._\n"

    rationale_md = "\n".join(f"- {ln}" for ln in rationale_lines)

    return f"""# Venus weekly review

## Week

- **Диапазон:** {pkg.week_start.isoformat()} → {pkg.week_end.isoformat()}

## Venus climate of the week

- **Знак:** {pkg.venus_sign}
- **Заголовок климата:** {pkg.climate_title}
- **Кратко (деньги + комфорт):** {money_comfort}

**Вероятная утечка**

{chr(10).join(f"- {x}" for x in leaks) if leaks else "- —"}

**Вероятная сила**

{chr(10).join(f"- {x}" for x in strengths) if strengths else "- —"}

## Main overlay

- **Активен:** {overlay_active}
- **Пара:** `{pair}`
- **Режим:** {mode}
- **Лучший день сигнала:** {best}
- **Паттерн (одна строка):** {combined}

## Main post

- **Угол:** {pkg.primary_post_angle}
- **Hook family:** `{hook}`
- **Компенсация (фокус):** {comp}

## Main reel

- **Угол:** {pkg.primary_reel_angle}
- **Hook family:** `{hook}`
- **Компенсация (фокус):** {comp}

## Support angle

{pkg.support_angle}

## Why this won

{rationale_md}
{alt_line}
## Editorial notes

{notes_block}

## Scored overlays (compact)

{overlay_table.strip()}
"""


def weekly_review_json_dict(pkg: WeeklyVenusPackage) -> dict[str, Any]:
    """Compact JSON-serialisable dict for diffs / pipelines (not full climate_ctx dump)."""
    money_comfort, leaks, strengths = _climate_summary_lines(pkg)
    alts: list[dict[str, Any]] = []
    if len(pkg.scored_overlays) >= 2:
        alt = pkg.scored_overlays[1]
        alts.append(
            {
                "pair_key": alt.get("pair_key"),
                "day": alt.get("day"),
                "score": alt.get("score"),
                "orb": alt.get("orb"),
            }
        )
    return {
        "artifact": "venus_weekly_review_v1",
        "week_start": pkg.week_start.isoformat(),
        "week_end": pkg.week_end.isoformat(),
        "venus_sign": pkg.venus_sign,
        "climate_title": pkg.climate_title,
        "climate_summary": money_comfort,
        "likely_leak": leaks,
        "likely_strength": strengths,
        "overlay": {
            "active": pkg.overlay_active,
            "pair": pkg.overlay_pair,
            "mode": pkg.overlay_mode,
            "best_day": pkg.best_day.isoformat() if pkg.best_day else None,
            "combined_pattern_one_line": _combined_pattern_one_line(pkg),
        },
        "main_post": {
            "angle": pkg.primary_post_angle,
            "hook_family": pkg.hook_family,
            "compensation_focus": pkg.compensation_focus,
        },
        "main_reel": {
            "angle": pkg.primary_reel_angle,
            "hook_family": pkg.hook_family,
            "compensation_focus": pkg.compensation_focus,
        },
        "support_angle": pkg.support_angle,
        "why_won": {
            "rationale_lines": _rationale_bullets(pkg.selection_rationale, max_bullets=8),
            "alternatives": alts,
        },
        "editorial_notes": list(pkg.editorial_notes),
        "scored_overlays": list(pkg.scored_overlays),
    }


@dataclass(frozen=True)
class WeeklyReviewPaths:
    """Paths written by ``write_weekly_review_artifacts``."""

    markdown: Path
    json_path: Path | None


def write_weekly_review_artifacts(
    pkg: WeeklyVenusPackage,
    output_dir: Path,
    *,
    write_json: bool = True,
    stem: str | None = None,
) -> WeeklyReviewPaths:
    """Write ``venus_weekly_review_<week_start>.md`` and optionally ``.json`` into *output_dir*.

    Creates *output_dir* if missing. Returns paths written.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = stem or f"venus_weekly_review_{pkg.week_start.isoformat()}"
    md_path = output_dir / f"{base}.md"
    md_path.write_text(render_weekly_review_markdown(pkg), encoding="utf-8")

    json_path: Path | None = None
    if write_json:
        json_path = output_dir / f"{base}.json"
        payload = weekly_review_json_dict(pkg)
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return WeeklyReviewPaths(markdown=md_path, json_path=json_path)
