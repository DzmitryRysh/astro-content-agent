"""Catstyle Post Package v1 — deterministic local quality gate before manual IG review."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def _utf8_bytes_as_latin1_text(bs: bytes) -> str:
    """UTF-8 bytes decoded as Latin-1 yields common PowerShell mojibake substrings."""
    return bs.decode("latin-1")


# Typical markers when UTF-8 was read as Latin-1 / legacy code pages (Windows consoles).
MOJIBAKE_SNIPPETS = (
    "\u00d0",
    "\u00d1",
    _utf8_bytes_as_latin1_text(bytes([0xE2, 0x80, 0x94])),
    _utf8_bytes_as_latin1_text(bytes([0xE2, 0x80, 0xA2])),
    _utf8_bytes_as_latin1_text(bytes([0xE2, 0x98, 0x90]))[:2],
)

ERROR_WEIGHT = 30
WARNING_WEIGHT = 8


def _looks_like_http_url(s: str) -> bool:
    t = s.strip().lower()
    return t.startswith("http://") or t.startswith("https://")


def _scan_text_fields(pkg: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("hook", "caption", "compensation", "checklist", "carousel_slide_text"):
        v = pkg.get(key)
        if isinstance(v, str):
            parts.append(v)
    return "\n".join(parts)


def _detect_mojibake(text: str) -> list[str]:
    found: list[str] = []
    for snippet in MOJIBAKE_SNIPPETS:
        if snippet in text:
            found.append(snippet)
    return found


class CatstylePostPackageQualityResult(BaseModel):
    status: Literal["ready", "needs_attention"]
    score: int = Field(ge=0, le=100)
    passed_checks: list[str]
    warnings: list[str]
    errors: list[str]
    package_dir: str
    recommended_primary_image: str | None = None


def check_catstyle_post_package(package_dir: Path | str) -> CatstylePostPackageQualityResult:
    """Load ``post_package.json`` under ``package_dir`` and run deterministic QC checks."""
    root = Path(package_dir).expanduser().resolve()
    passed: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    json_path = root / "post_package.json"
    if not json_path.is_file():
        errors.append(f"Missing post_package.json in {root}")
        return CatstylePostPackageQualityResult(
            status="needs_attention",
            score=0,
            passed_checks=passed,
            warnings=warnings,
            errors=errors,
            package_dir=str(root),
            recommended_primary_image=None,
        )

    try:
        raw_text = json_path.read_text(encoding="utf-8-sig")
        pkg = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        errors.append(f"post_package.json is not valid JSON: {exc}")
        return CatstylePostPackageQualityResult(
            status="needs_attention",
            score=0,
            passed_checks=passed,
            warnings=warnings,
            errors=errors,
            package_dir=str(root),
            recommended_primary_image=None,
        )

    if not isinstance(pkg, dict):
        errors.append("post_package.json root must be a JSON object.")
        return CatstylePostPackageQualityResult(
            status="needs_attention",
            score=0,
            passed_checks=passed,
            warnings=warnings,
            errors=errors,
            package_dir=str(root),
            recommended_primary_image=None,
        )

    passed.append("post_package.json exists and is valid JSON")

    date = pkg.get("date")
    if not (isinstance(date, str) and date.strip()):
        errors.append("Field date is missing or empty.")
    else:
        passed.append("date is present")

    for field in ("hook", "caption", "compensation", "checklist"):
        val = pkg.get(field)
        if not (isinstance(val, str) and val.strip()):
            errors.append(f"Field {field} is missing or empty.")
        else:
            passed.append(f"{field} is non-empty")

    recommended_out: str | None = None
    primary = pkg.get("recommended_primary_image")
    if not (isinstance(primary, str) and primary.strip()):
        errors.append("recommended_primary_image is missing or empty.")
    else:
        recommended_out = primary.strip()
        passed.append("recommended_primary_image is present in package")
        if _looks_like_http_url(recommended_out):
            passed.append("recommended_primary_image looks remote — skipped local file existence check")
        else:
            pth = Path(recommended_out).expanduser()
            if not pth.is_file():
                errors.append(f"recommended_primary_image path does not exist: {recommended_out}")
            else:
                passed.append("recommended_primary_image local file exists")

    gen_paths = pkg.get("generated_image_paths")
    if not isinstance(gen_paths, list):
        errors.append("generated_image_paths must be a JSON array.")
    elif len(gen_paths) < 1:
        errors.append("generated_image_paths must contain at least one image path.")
    else:
        passed.append(f"generated_image_paths has {len(gen_paths)} entr(y/ies)")
        str_paths = [str(x) for x in gen_paths if isinstance(x, str) and str(x).strip()]
        missing_local = []
        for gp in str_paths:
            if _looks_like_http_url(gp):
                continue
            if not Path(gp).expanduser().is_file():
                missing_local.append(gp)
        if missing_local:
            warnings.append(
                "Some generated_image_paths are missing on disk: "
                + "; ".join(missing_local[:3])
                + ("..." if len(missing_local) > 3 else "")
            )
        else:
            passed.append("generated_image_paths local files exist (where checked)")

    shot_mode = pkg.get("shot_mode")
    sm = str(shot_mode).strip() if isinstance(shot_mode, str) else ""
    if sm == "hero_pair" and isinstance(gen_paths, list) and len(gen_paths) < 2:
        warnings.append(
            "shot_mode is hero_pair but fewer than 2 generated_image_paths — carousel / hero pair may be incomplete."
        )

    style_ref = pkg.get("style_reference_image_path")
    if isinstance(style_ref, str) and style_ref.strip():
        passed.append("style_reference_image_path is preserved (non-empty)")
    elif style_ref is None or style_ref == "":
        passed.append("style_reference_image_path absent or empty (allowed for v1)")
    else:
        warnings.append("style_reference_image_path has unexpected type.")

    jobs = pkg.get("image_jobs_summary")
    if isinstance(jobs, list) and jobs:
        bad_jobs = 0
        for j in jobs:
            if not isinstance(j, dict):
                bad_jobs += 1
                continue
            pa, pb, asp = j.get("planet_a"), j.get("planet_b"), j.get("aspect_type")
            if not (
                isinstance(pa, str) and pa.strip() and isinstance(pb, str) and pb.strip() and isinstance(asp, str) and asp.strip()
            ):
                bad_jobs += 1
        if bad_jobs:
            warnings.append(
                f"Planet/aspect fields missing or incomplete on {bad_jobs} image_jobs_summary entr(y/ies)."
            )
        else:
            passed.append("planet_a / planet_b / aspect_type present on image_jobs_summary entries")
    elif isinstance(jobs, list) and len(jobs) == 0:
        warnings.append("image_jobs_summary is empty — cannot verify planet/aspect context.")

    blob = _scan_text_fields(pkg)
    mo = _detect_mojibake(blob)
    if mo:
        errors.append(
            "Possible UTF-8 mojibake in package text fields (patterns: "
            + ", ".join(repr(m) for m in mo)
            + "). Re-export texts as UTF-8 (e.g. utf-8-sig for PowerShell)."
        )
    else:
        passed.append("no common mojibake patterns in Russian text fields")

    if CYRILLIC_RE.search(blob):
        passed.append("Cyrillic characters present in expected text fields")
    else:
        warnings.append("No Cyrillic detected in hook/caption/compensation/checklist/carousel — unexpected for Catstyle RU v1.")

    score = 100 - ERROR_WEIGHT * len(errors) - WARNING_WEIGHT * len(warnings)
    score = max(0, min(100, score))

    status: Literal["ready", "needs_attention"] = (
        "ready" if not errors and score >= 85 else "needs_attention"
    )

    return CatstylePostPackageQualityResult(
        status=status,
        score=score,
        passed_checks=passed,
        warnings=warnings,
        errors=errors,
        package_dir=str(root),
        recommended_primary_image=recommended_out,
    )


__all__ = [
    "CYRILLIC_RE",
    "MOJIBAKE_SNIPPETS",
    "CatstylePostPackageQualityResult",
    "check_catstyle_post_package",
]
