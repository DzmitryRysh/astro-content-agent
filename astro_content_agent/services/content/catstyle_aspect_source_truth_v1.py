"""Catstyle aspect source truth layer — sky vs editorial vs natal vs educational copy guards."""
from __future__ import annotations

import re
from typing import Any, Literal

AspectSource = Literal["sky_current", "manual_editorial", "natal_case", "educational"]

ASPECT_SOURCES: frozenset[str] = frozenset(
    {"sky_current", "manual_editorial", "natal_case", "educational"}
)

DEFAULT_FORCED_ASPECT_SOURCE: AspectSource = "manual_editorial"

# Phrases allowed only when aspect_source == sky_current (EN + RU).
_CURRENT_SKY_PHRASE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
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


def normalize_aspect_source(raw: str | None) -> AspectSource:
    key = (raw or "").strip().lower().replace("-", "_")
    if key not in ASPECT_SOURCES:
        known = ", ".join(sorted(ASPECT_SOURCES))
        raise ValueError(f"aspect_source must be one of: {known} (got {raw!r}).")
    return key  # type: ignore[return-value]


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
    """Remove current-sky-only phrasing from caption/summary copy."""
    out = text or ""
    for pat in _CURRENT_SKY_PHRASE_PATTERNS:
        out = pat.sub("", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def apply_aspect_source_caption_guard(caption: str, aspect_source: str | None) -> str:
    """Strip current-sky language unless aspect_source is sky_current."""
    if allows_current_sky_language(aspect_source):
        return (caption or "").strip()
    return strip_forbidden_current_sky_phrases(caption or "")


def aspect_source_copy_rules(aspect_source: str | None) -> dict[str, Any]:
    """LLM / operator hints for caption generation."""
    try:
        src = normalize_aspect_source(aspect_source) if aspect_source else DEFAULT_FORCED_ASPECT_SOURCE
    except ValueError:
        src = DEFAULT_FORCED_ASPECT_SOURCE
    allows = allows_current_sky_language(src)
    return {
        "aspect_source": src,
        "allows_current_sky_language": allows,
        "forbidden_when_not_sky_current": (
            [] if allows else [p.pattern for p in _CURRENT_SKY_PHRASE_PATTERNS]
        ),
        "timing_block_allowed": allows,
        "sky_weather_stack_allowed": allows,
    }


__all__ = [
    "ASPECT_SOURCES",
    "DEFAULT_FORCED_ASPECT_SOURCE",
    "AspectSource",
    "annotate_manifest_aspect_source",
    "apply_aspect_source_caption_guard",
    "allows_current_sky_language",
    "aspect_source_copy_rules",
    "infer_aspect_source_from_manifest",
    "normalize_aspect_source",
    "strip_forbidden_current_sky_phrases",
]
