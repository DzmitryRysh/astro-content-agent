"""Catstyle aspect timing — derive UTC window metadata from manifest scan fields only (no invented ephemeris)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from astro_content_agent.content.catstyle.models import CatstyleAspectTimingMetadata

_FAST_PERSONALS = frozenset({"mercury", "moon"})
_MID_PERSONALS = frozenset({"venus", "mars", "sun"})


def _urgency_tier(personal: str | None) -> str:
    if not personal:
        return "mid"
    key = personal.strip().lower()
    if key in _FAST_PERSONALS:
        return "fast"
    if key in _MID_PERSONALS:
        return "mid"
    return "slow"


def _parse_post_date(manifest: dict[str, Any]) -> date | None:
    raw = str(manifest.get("date") or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _safe_int(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _safe_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _utc_hour_iso(d: date, hour: int) -> str:
    h = max(0, min(hour, 23))
    return datetime(d.year, d.month, d.day, h, 0, 0, tzinfo=timezone.utc).isoformat()


def _window_end_exclusive_iso(d: date, last_sample_hour: int, step_hours: int) -> str:
    step = max(1, int(step_hours))
    end = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(hours=int(last_sample_hour) + step)
    return end.isoformat()


def _ru_orb_phrase(orb: float | None) -> str:
    if orb is None:
        return ""
    s = f"{orb:.2f}".replace(".", ",")
    return f"Орбис в данных скана: ~{s}°."


def _window_span_days(meta: CatstyleAspectTimingMetadata) -> float | None:
    """Calendar span in days from window_start_utc to window_end_utc (exclusive end ISO)."""
    if not meta.window_start_utc or not meta.window_end_utc:
        return None
    try:
        t0 = datetime.fromisoformat(meta.window_start_utc.replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(meta.window_end_utc.replace("Z", "+00:00"))
        if t0.tzinfo is None:
            t0 = t0.replace(tzinfo=timezone.utc)
        if t1.tzinfo is None:
            t1 = t1.replace(tzinfo=timezone.utc)
        sec = (t1 - t0).total_seconds()
        return max(0.0, sec / 86400.0)
    except ValueError:
        return None


def _human_duration_around_peak_ru(meta: CatstyleAspectTimingMetadata) -> str | None:
    """Approximate subscriber phrasing from real window span (audit uses exact UTC in Markdown)."""
    d = _window_span_days(meta)
    if d is None:
        return None
    if d <= 2.25:
        return "1–2 дня"
    if d <= 3.75:
        return "около 3 дней"
    if d <= 5.5:
        return "около 4 дней"
    if d <= 8.0:
        return "около недели"
    return "около недели"


def _infer_phase(orb: float | None) -> Any:
    if orb is not None and orb <= 0.12:
        return "exact"
    return "unknown"


def _selected_or_job_row(manifest: dict[str, Any]) -> dict[str, Any] | None:
    sel = manifest.get("selected_candidate")
    if isinstance(sel, dict):
        return sel
    jobs_raw = manifest.get("jobs")
    if isinstance(jobs_raw, list) and jobs_raw and isinstance(jobs_raw[0], dict):
        return jobs_raw[0]
    return None


def _orb_from_manifest(manifest: dict[str, Any], row: dict[str, Any] | None) -> float | None:
    if row:
        o = _safe_float(row.get("orb"))
        if o is not None:
            return o
    jobs_raw = manifest.get("jobs")
    if isinstance(jobs_raw, list):
        for j in jobs_raw:
            if isinstance(j, dict) and j.get("orb") is not None:
                return _safe_float(j.get("orb"))
    return None


def _resolve_timing_data_source(
    manifest: dict[str, Any],
    row: dict[str, Any] | None,
    timing_status: str,
) -> str:
    mo = manifest.get("manual_aspect_override")
    manual = isinstance(mo, dict) and mo.get("enabled") is True
    if not manual:
        return "manifest_selected_candidate_v1"
    scan = str(manifest.get("sky_scan_mode") or "").strip().lower()
    matched_flag = bool(row.get("manual_override_sky_timing_match")) if row else False
    if scan == "day-window":
        if matched_flag and timing_status in ("sky_window_utc", "estimated", "orb_only_estimate"):
            return "manual_override_with_timing_v1"
        return "manual_override_no_sky_match_v1"
    if scan == "manual_override":
        return "manifest_manual_override_v1"
    return "manifest_selected_candidate_v1"


def manifest_has_editorial_timing_handoff(manifest: dict[str, Any]) -> bool:
    """
    True when a manual editorial override matched a day-window scan with explicit UTC bounds.

    Used to attach factual timing metadata (and optional caption timing) without treating the post
    as ``sky_current``.
    """
    row = _selected_or_job_row(manifest)
    if not row or not bool(row.get("manual_override_sky_timing_match")):
        return False
    if str(manifest.get("sky_scan_mode") or "").strip().lower() != "day-window":
        return False
    return (
        row.get("window_start_hour_utc") is not None
        and row.get("window_end_hour_utc") is not None
    )


def build_aspect_timing_from_manifest(manifest: dict[str, Any]) -> CatstyleAspectTimingMetadata:
    """
    Build timing metadata strictly from manifest fields (selected_candidate / first job).

    Does not compute new ephemeris; applying/separating stays unknown unless orb is very tight (exact-ish).
    """
    d = _parse_post_date(manifest)
    row = _selected_or_job_row(manifest)
    scan_mode = manifest.get("sky_scan_mode")
    scan_mode_s = str(scan_mode).strip() if scan_mode is not None else ""
    step_raw = _safe_int(manifest.get("sky_scan_step_hours_utc"))
    wf = _safe_int(row.get("window_first_seen_hour_utc")) if row else None
    wl = _safe_int(row.get("window_last_seen_hour_utc")) if row else None
    ch = _safe_int(row.get("closest_hour_utc")) if row else None
    orb = _orb_from_manifest(manifest, row)
    phase = _infer_phase(orb)

    common = dict(
        orb_at_post_date=orb,
        phase=phase,
        timezone_note="UTC",
        sky_scan_mode=scan_mode_s or None,
        sky_scan_step_hours_utc=step_raw,
        data_source="manifest_selected_candidate_v1",
    )

    if d is None:
        ts = "missing_exact_window"
        return CatstyleAspectTimingMetadata(
            timing_status=ts,
            data_source=_resolve_timing_data_source(manifest, row, ts),
            **{k: v for k, v in common.items() if k != "data_source"},
        )

    if wf is not None and wl is not None and ch is not None:
        step = step_raw if step_raw is not None else 2
        step = max(1, int(step))
        w_start = _utc_hour_iso(d, wf)
        peak = _utc_hour_iso(d, ch)
        w_end = _window_end_exclusive_iso(d, wl, step)
        ts = "sky_window_utc"
        return CatstyleAspectTimingMetadata(
            timing_status=ts,
            window_start_utc=w_start,
            peak_at_utc=peak,
            exact_at_utc=peak,
            window_end_utc=w_end,
            sky_scan_step_hours_utc=step,
            data_source=_resolve_timing_data_source(manifest, row, ts),
            **{k: v for k, v in common.items() if k not in ("sky_scan_step_hours_utc", "data_source")},
        )

    if ch is not None:
        peak = _utc_hour_iso(d, ch)
        ts = "estimated"
        return CatstyleAspectTimingMetadata(
            timing_status=ts,
            peak_at_utc=peak,
            exact_at_utc=peak,
            data_source=_resolve_timing_data_source(manifest, row, ts),
            **{k: v for k, v in common.items() if k != "data_source"},
        )

    if orb is not None:
        ts = "orb_only_estimate"
        return CatstyleAspectTimingMetadata(
            timing_status=ts,
            data_source=_resolve_timing_data_source(manifest, row, ts),
            **{k: v for k, v in common.items() if k != "data_source"},
        )

    ts = "missing_exact_window"
    return CatstyleAspectTimingMetadata(
        timing_status=ts,
        data_source=_resolve_timing_data_source(manifest, row, ts),
        **{k: v for k, v in common.items() if k != "data_source"},
    )


def format_ru_timing_caption_append(
    meta: CatstyleAspectTimingMetadata,
    *,
    post_date: date,
    personal_planet: str | None,
) -> str:
    """Short subscriber-facing Russian timing (no UTC/orb/step jargon). Audit detail lives in Markdown only."""
    tier = _urgency_tier(personal_planet)
    parts: list[str] = []

    if meta.timing_status == "sky_window_utc" and meta.window_start_utc and meta.window_end_utc and meta.peak_at_utc:
        dur = _human_duration_around_peak_ru(meta)
        if dur:
            parts.append(
                f"Окно аспекта короткое: примерно на {dur} вокруг пика. "
                "Это не энергия «на весь месяц», поэтому не растягивай шанс на красивую теорию — "
                "выбери один конкретный шаг сегодня."
            )
        else:
            parts.append(
                "Окно аспекта короткое — ориентируйся на день публикации и ближайшие сутки; "
                "не растягивай шанс на красивую теорию — один конкретный шаг сегодня."
            )
        if tier == "fast":
            parts.append("Лучше не растягивать на неделю.")
    elif meta.timing_status == "estimated" and meta.peak_at_utc:
        parts.append(
            "Окно короткое вокруг пика сути — держи фокус на день публикации и ближайшие сутки; "
            "эффект не «на весь месяц»."
        )
        if tier == "fast":
            parts.append("Один конкретный шаг сегодня; лучше не растягивать на неделю.")
        elif tier == "mid":
            parts.append("Не расползайся на неделю без необходимости.")
    elif meta.timing_status == "orb_only_estimate":
        parts.append("Окно короткое: лучше использовать день публикации и ближайшие сутки.")
        if tier == "fast":
            parts.append("Один конкретный шаг сегодня; лучше не растягивать на неделю.")
        elif tier == "mid":
            parts.append("Не расползайся на неделю без необходимости.")
    else:
        parts.append("Окно короткое: лучше использовать день публикации и ближайшие сутки.")
        if tier == "fast":
            parts.append("Один конкретный шаг сегодня; лучше не растягивать на неделю.")
        elif tier == "mid":
            parts.append("Не расползайся на неделю без необходимости.")
        else:
            parts.append("Опирайся на день публикации и ближайшие сутки — не растягивай смысл на месяц теории.")

    return " ".join(parts).strip()


def append_ru_timing_to_caption(
    caption: str,
    meta: CatstyleAspectTimingMetadata,
    post_date: date,
    personal: str | None,
) -> str:
    para = format_ru_timing_caption_append(meta, post_date=post_date, personal_planet=personal)
    if not para:
        return caption
    block = f"**Про сроки:** {para}"
    base = caption.rstrip()
    if block in base:
        return caption
    return f"{base}\n\n{block}" if base else block


def render_aspect_timing_markdown_section(meta: CatstyleAspectTimingMetadata) -> str:
    lines = [
        "## Aspect timing (UTC)",
        "",
        f"- **timing_status:** `{meta.timing_status}`",
        f"- **timezone_note:** {meta.timezone_note}",
        f"- **phase:** `{meta.phase}`",
        f"- **data_source:** {meta.data_source}",
    ]
    if meta.sky_scan_mode:
        lines.append(f"- **sky_scan_mode:** `{meta.sky_scan_mode}`")
    if meta.sky_scan_step_hours_utc is not None:
        lines.append(f"- **sky_scan_step_hours_utc:** {meta.sky_scan_step_hours_utc}")
    if meta.window_start_utc:
        lines.append(f"- **window_start_utc:** `{meta.window_start_utc}`")
    if meta.window_end_utc:
        lines.append(f"- **window_end_utc:** `{meta.window_end_utc}` (exclusive end of last sampling bucket)")
    if meta.peak_at_utc:
        lines.append(f"- **peak_at_utc:** `{meta.peak_at_utc}`")
    if meta.exact_at_utc:
        lines.append(f"- **exact_at_utc:** `{meta.exact_at_utc}`")
    if meta.orb_at_post_date is not None:
        lines.append(f"- **orb_at_post_date:** {meta.orb_at_post_date}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "append_ru_timing_to_caption",
    "build_aspect_timing_from_manifest",
    "manifest_has_editorial_timing_handoff",
    "format_ru_timing_caption_append",
    "render_aspect_timing_markdown_section",
]
