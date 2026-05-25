"""Catstyle aspect source truth layer — sky vs editorial vs natal vs educational copy guards."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, Literal

AspectSource = Literal["sky_current", "manual_editorial", "natal_case", "educational"]
SkyTimingMode = Literal["exact_today", "upcoming", "active_window", "background"]

ASPECT_SOURCES: frozenset[str] = frozenset(
    {"sky_current", "manual_editorial", "natal_case", "educational"}
)
SKY_TIMING_MODES: frozenset[str] = frozenset(
    {"exact_today", "upcoming", "active_window", "background"}
)

DEFAULT_FORCED_ASPECT_SOURCE: AspectSource = "manual_editorial"
DEFAULT_SKY_TIMING_MODE: SkyTimingMode = "active_window"

_DURATION_CATEGORY_TO_SKY_TIMING: dict[str, SkyTimingMode] = {
    "short_flash": "exact_today",
    "active_wave": "active_window",
    "pressure_background": "background",
}

# Exact-today sky copy (only sky_current + sky_timing_mode exact_today).
_EXACT_TODAY_SKY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"today on the sky",
        r"current sky weather",
        r"this transit is active now",
        r"today this aspect is happening",
        r"the sky is bringing",
        r"active in the sky today",
        r"in today['\u2019]s sky",
        r"сегодня на небе",
        r"сейчас ид[её]т аспект",
        r"этот транзит сейчас активен",
        r"небо включает",
        r"сегодняшний аспект",
        r"текущая небесная погода",
        r"сейчас в небе",
        r"аспект сейчас в небе",
        r"небесная погода сегодня",
        r"на небе сегодня",
    )
)

_UPCOMING_SKY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"подходит к пику",
        r"в ближайшие сутки",
        r"скоро на пике",
        r"завтра на пике",
        r"approaching peak",
        r"in the next day or two",
    )
)

_ACTIVE_WINDOW_SKY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"в эти дни",
        r"сейчас активен период",
        r"active across this window",
        r"window is open now",
    )
)

_BACKGROUND_SKY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"фоном держится",
        r"длинное давление",
        r"несколько дней подряд",
        r"background pressure",
        r"long.?running pressure",
    )
)

_MODE_PHRASE_PATTERNS: dict[SkyTimingMode, tuple[re.Pattern[str], ...]] = {
    "exact_today": _EXACT_TODAY_SKY_PATTERNS,
    "upcoming": _UPCOMING_SKY_PATTERNS,
    "active_window": _ACTIVE_WINDOW_SKY_PATTERNS,
    "background": _BACKGROUND_SKY_PATTERNS,
}

_ALL_NON_SKY_FORBIDDEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    _EXACT_TODAY_SKY_PATTERNS + _UPCOMING_SKY_PATTERNS + _ACTIVE_WINDOW_SKY_PATTERNS + _BACKGROUND_SKY_PATTERNS
)

_SKY_TIMING_PHRASE_HINTS: dict[SkyTimingMode, tuple[str, ...]] = {
    "exact_today": (
        "сегодня на небе",
        "сегодняшний аспект",
        "аспект сейчас в небе",
    ),
    "upcoming": (
        "подходит к пику",
        "в ближайшие сутки",
        "завтра",
    ),
    "active_window": (
        "в эти дни",
        "сейчас активен период",
        "окно аспекта",
    ),
    "background": (
        "фоном держится",
        "длинное давление",
        "несколько дней",
    ),
}

_SKY_TIMING_GUIDANCE_RU: dict[SkyTimingMode, str] = {
    "exact_today": (
        "Аспект на пике сегодня — можно «сегодня на небе», «сейчас в небе», короткое окно 1–2 дня."
    ),
    "upcoming": (
        "Аспект ещё на подходе — «подходит к пику», «в ближайшие сутки», «завтра» только если дата в данных это поддерживает; "
        "не пиши «сегодня на небе»."
    ),
    "active_window": (
        "Аспект в активном окне несколько дней — «в эти дни», «сейчас активен период», «окно открыто»; "
        "не своди к одному «сегодня на небе»."
    ),
    "background": (
        "Длинный фоновый аспект — «фоном держится», «длинное давление», «несколько дней подряд»; "
        "не «сегодня на небе» и не «сейчас идёт аспект» как у короткой вспышки."
    ),
}


def normalize_aspect_source(raw: str | None) -> AspectSource:
    key = (raw or "").strip().lower().replace("-", "_")
    if key not in ASPECT_SOURCES:
        known = ", ".join(sorted(ASPECT_SOURCES))
        raise ValueError(f"aspect_source must be one of: {known} (got {raw!r}).")
    return key  # type: ignore[return-value]


def normalize_sky_timing_mode(raw: str | None) -> SkyTimingMode:
    key = (raw or "").strip().lower().replace("-", "_")
    if key not in SKY_TIMING_MODES:
        known = ", ".join(sorted(SKY_TIMING_MODES))
        raise ValueError(f"sky_timing_mode must be one of: {known} (got {raw!r}).")
    return key  # type: ignore[return-value]


def resolve_sky_timing_mode(
    aspect_source: str | None,
    explicit_mode: str | None = None,
) -> SkyTimingMode | None:
    """Return timing mode only for sky_current; ignore accidental mode on editorial/natal/educational."""
    if not allows_current_sky_language(aspect_source):
        return None
    if explicit_mode:
        try:
            return normalize_sky_timing_mode(explicit_mode)
        except ValueError:
            return DEFAULT_SKY_TIMING_MODE
    return DEFAULT_SKY_TIMING_MODE


def duration_category_to_sky_timing_mode(duration_category: str | None) -> SkyTimingMode | None:
    key = (duration_category or "").strip().lower()
    return _DURATION_CATEGORY_TO_SKY_TIMING.get(key)  # type: ignore[return-value]


def _parse_manifest_post_date(manifest: dict[str, Any]) -> date | None:
    raw = str(manifest.get("date") or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _peak_date_after_post(manifest: dict[str, Any], post_d: date) -> bool:
    """True when scan timing peak is strictly after the publication date (upcoming)."""
    from astro_content_agent.services.content.catstyle_aspect_timing import (
        build_aspect_timing_from_manifest,
    )

    meta = build_aspect_timing_from_manifest(manifest)
    if not meta or not meta.peak_at_utc:
        return False
    try:
        dt = datetime.fromisoformat(str(meta.peak_at_utc).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.date() > post_d
    except (TypeError, ValueError):
        return False


def infer_sky_timing_mode_from_manifest(
    manifest: dict[str, Any],
    aspect_source: str | None = None,
) -> SkyTimingMode | None:
    """
    Resolve sky timing copy mode for sky_current manifests.

    Defaults to ``active_window`` when not inferable. Returns ``None`` for non-sky sources.
    """
    src = aspect_source
    if src is None:
        src = infer_aspect_source_from_manifest(manifest)
    if not allows_current_sky_language(src):
        return None

    for container in (
        manifest,
        _row_from_manifest(manifest) or {},
        manifest.get("manual_aspect_override")
        if isinstance(manifest.get("manual_aspect_override"), dict)
        else {},
    ):
        raw = container.get("sky_timing_mode")
        if raw:
            return normalize_sky_timing_mode(str(raw))

    stack = manifest.get("sky_weather_stack")
    if isinstance(stack, dict):
        raw = stack.get("sky_timing_mode")
        if raw:
            return normalize_sky_timing_mode(str(raw))
        primary = stack.get("primary_aspect")
        if isinstance(primary, dict):
            raw = primary.get("sky_timing_mode")
            if raw:
                return normalize_sky_timing_mode(str(raw))
            mapped = duration_category_to_sky_timing_mode(str(primary.get("duration_category") or ""))
            if mapped:
                post_d = _parse_manifest_post_date(manifest)
                if mapped == "exact_today" and post_d and _peak_date_after_post(manifest, post_d):
                    return "upcoming"
                return mapped

    row = _row_from_manifest(manifest)
    if row:
        mapped = duration_category_to_sky_timing_mode(str(row.get("duration_category") or ""))
        if mapped:
            post_d = _parse_manifest_post_date(manifest)
            if mapped == "exact_today" and post_d and _peak_date_after_post(manifest, post_d):
                return "upcoming"
            return mapped

    post_d = _parse_manifest_post_date(manifest)
    if post_d and _peak_date_after_post(manifest, post_d):
        return "upcoming"

    return DEFAULT_SKY_TIMING_MODE


def annotate_manifest_sky_timing_mode(manifest: dict[str, Any], mode: SkyTimingMode | None) -> None:
    """Write sky_timing_mode when aspect is sky_current."""
    if mode is None:
        return
    m = normalize_sky_timing_mode(mode)
    manifest["sky_timing_mode"] = m
    sel = manifest.get("selected_candidate")
    if isinstance(sel, dict):
        sel["sky_timing_mode"] = m
    stack = manifest.get("sky_weather_stack")
    if isinstance(stack, dict):
        stack["sky_timing_mode"] = m
        primary = stack.get("primary_aspect")
        if isinstance(primary, dict):
            primary["sky_timing_mode"] = m


def sky_timing_copy_rules(
    aspect_source: str | None,
    sky_timing_mode: str | None = None,
) -> dict[str, Any]:
    """Allowed timing phrase family and writer guidance for sky_current."""
    mode = resolve_sky_timing_mode(aspect_source, sky_timing_mode)
    if mode is None:
        return {
            "sky_timing_mode": None,
            "allows_sky_timing_language": False,
            "allowed_timing_phrase_hints": [],
            "timing_copy_guidance": (
                "Не используй язык «сегодня на небе» / текущего транзита — aspect_source не sky_current."
            ),
            "forbidden_timing_phrase_families": ["exact_today", "upcoming", "active_window", "background"],
        }
    return {
        "sky_timing_mode": mode,
        "allows_sky_timing_language": True,
        "allowed_timing_phrase_hints": list(_SKY_TIMING_PHRASE_HINTS[mode]),
        "timing_copy_guidance": _SKY_TIMING_GUIDANCE_RU[mode],
        "forbidden_timing_phrase_families": [
            k for k in sorted(SKY_TIMING_MODES) if k != mode
        ],
    }


def allows_timing_phrase_family(
    phrase: str,
    aspect_source: str | None,
    sky_timing_mode: str | None = None,
) -> bool:
    """Heuristic check whether a phrase fits the resolved sky timing family."""
    if not allows_current_sky_language(aspect_source):
        return False
    mode = resolve_sky_timing_mode(aspect_source, sky_timing_mode)
    assert mode is not None
    low = (phrase or "").lower()
    for hint in _SKY_TIMING_PHRASE_HINTS[mode]:
        if hint.lower() in low:
            return True
    return False


def _patterns_for_other_modes(mode: SkyTimingMode) -> tuple[re.Pattern[str], ...]:
    out: list[re.Pattern[str]] = []
    for key, patterns in _MODE_PHRASE_PATTERNS.items():
        if key != mode:
            out.extend(patterns)
    return tuple(out)


def strip_disallowed_sky_timing_phrases(
    text: str,
    aspect_source: str | None,
    sky_timing_mode: str | None = None,
) -> str:
    """Remove sky-timing phrases forbidden for this aspect_source / timing mode."""
    if not allows_current_sky_language(aspect_source):
        patterns = _ALL_NON_SKY_FORBIDDEN_PATTERNS
    else:
        mode = resolve_sky_timing_mode(aspect_source, sky_timing_mode)
        patterns = _patterns_for_other_modes(mode) if mode else _ALL_NON_SKY_FORBIDDEN_PATTERNS
    out = text or ""
    for pat in patterns:
        out = pat.sub("", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def allows_current_sky_language(aspect_source: str | None) -> bool:
    if not aspect_source:
        return False
    try:
        return normalize_aspect_source(aspect_source) == "sky_current"
    except ValueError:
        return False


def _row_from_manifest(manifest: dict[str, Any]) -> dict[str, Any] | None:
    sel = manifest.get("selected_candidate")
    if isinstance(sel, dict):
        return sel
    jobs = manifest.get("jobs")
    if isinstance(jobs, list) and jobs and isinstance(jobs[0], dict):
        return jobs[0]
    return None


def infer_aspect_source_from_manifest(manifest: dict[str, Any]) -> AspectSource:
    """
    Resolve truth-layer aspect source from manifest metadata.

    Forced/manual aspects default to ``manual_editorial`` unless explicitly marked.
    Sky scan without manual override → ``sky_current``.
    """
    top = manifest.get("aspect_source")
    if top:
        return normalize_aspect_source(str(top))

    row = _row_from_manifest(manifest)
    if row and row.get("aspect_source"):
        return normalize_aspect_source(str(row["aspect_source"]))

    mo = manifest.get("manual_aspect_override")
    if isinstance(mo, dict) and mo.get("enabled") is True:
        if mo.get("aspect_source"):
            return normalize_aspect_source(str(mo["aspect_source"]))
        return DEFAULT_FORCED_ASPECT_SOURCE

    if row:
        if row.get("manual_aspect_override") is True:
            return DEFAULT_FORCED_ASPECT_SOURCE
        if str(row.get("source") or "").strip().lower() == "manual_override":
            return DEFAULT_FORCED_ASPECT_SOURCE

    scan = str(manifest.get("sky_scan_mode") or "").strip().lower()
    if scan and scan not in ("manual_override", ""):
        return "sky_current"

    return DEFAULT_FORCED_ASPECT_SOURCE


def annotate_manifest_aspect_source(manifest: dict[str, Any], aspect_source: AspectSource) -> None:
    """Write aspect_source onto manifest root and selected_candidate when present."""
    src = normalize_aspect_source(aspect_source)
    manifest["aspect_source"] = src
    sel = manifest.get("selected_candidate")
    if isinstance(sel, dict):
        sel["aspect_source"] = src
    mo = manifest.get("manual_aspect_override")
    if isinstance(mo, dict) and mo.get("enabled") is True:
        mo["aspect_source"] = src


def strip_forbidden_current_sky_phrases(text: str) -> str:
    """Remove all sky-timing phrasing (non-sky_current captions)."""
    out = text or ""
    for pat in _ALL_NON_SKY_FORBIDDEN_PATTERNS:
        out = pat.sub("", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def apply_aspect_source_caption_guard(
    caption: str,
    aspect_source: str | None,
    sky_timing_mode: str | None = None,
) -> str:
    """Strip sky-timing language forbidden for aspect_source and sky_timing_mode."""
    if allows_current_sky_language(aspect_source):
        return strip_disallowed_sky_timing_phrases(
            caption or "", aspect_source, sky_timing_mode
        )
    return strip_forbidden_current_sky_phrases(caption or "")


def aspect_source_copy_rules(
    aspect_source: str | None,
    sky_timing_mode: str | None = None,
) -> dict[str, Any]:
    """LLM / operator hints for caption generation."""
    try:
        src = normalize_aspect_source(aspect_source) if aspect_source else DEFAULT_FORCED_ASPECT_SOURCE
    except ValueError:
        src = DEFAULT_FORCED_ASPECT_SOURCE
    allows = allows_current_sky_language(src)
    timing_rules = sky_timing_copy_rules(src, sky_timing_mode)
    return {
        "aspect_source": src,
        "allows_current_sky_language": allows,
        "forbidden_when_not_sky_current": (
            [] if allows else [p.pattern for p in _ALL_NON_SKY_FORBIDDEN_PATTERNS]
        ),
        "timing_block_allowed": allows,
        "sky_weather_stack_allowed": allows,
        "sky_timing_mode": timing_rules.get("sky_timing_mode"),
        "timing_copy_guidance": timing_rules.get("timing_copy_guidance"),
    }


__all__ = [
    "ASPECT_SOURCES",
    "DEFAULT_FORCED_ASPECT_SOURCE",
    "DEFAULT_SKY_TIMING_MODE",
    "SKY_TIMING_MODES",
    "AspectSource",
    "SkyTimingMode",
    "annotate_manifest_aspect_source",
    "annotate_manifest_sky_timing_mode",
    "apply_aspect_source_caption_guard",
    "allows_current_sky_language",
    "allows_timing_phrase_family",
    "aspect_source_copy_rules",
    "duration_category_to_sky_timing_mode",
    "infer_aspect_source_from_manifest",
    "infer_sky_timing_mode_from_manifest",
    "normalize_aspect_source",
    "normalize_sky_timing_mode",
    "resolve_sky_timing_mode",
    "sky_timing_copy_rules",
    "strip_disallowed_sky_timing_phrases",
    "strip_forbidden_current_sky_phrases",
]
