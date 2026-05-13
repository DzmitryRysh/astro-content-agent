"""Catstyle Manual Review v1 — deterministic local artifact for human producers before IG publishing."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

ALLOWED_APPROVAL_DECISIONS = frozenset({"approve", "revise_text", "regenerate_images", "reject"})

from astro_content_agent.services.content.catstyle_post_package_quality import (
    CatstylePostPackageQualityResult,
    check_catstyle_post_package,
)

MANUAL_REVIEW_VERSION = "catstyle-manual-review-v1"

_PLANET_MARKER_GENITIVE_RU: dict[str, str] = {
    "sun": "Солнца",
    "moon": "Луны",
    "mercury": "Меркурия",
    "venus": "Венеры",
    "mars": "Марса",
    "jupiter": "Юпитера",
    "saturn": "Сатурна",
    "uranus": "Урана",
    "neptune": "Нептуна",
    "pluto": "Плутона",
}


def planet_marker_genitive_ru(planet_name: str | None) -> str | None:
    """Russian genitive planet label for marker review prompts (single-word keys)."""
    if planet_name is None or not str(planet_name).strip():
        return None
    return _PLANET_MARKER_GENITIVE_RU.get(str(planet_name).strip().lower())


def marker_visibility_question_ru(planet_a: str | None, planet_b: str | None) -> str:
    ga = planet_marker_genitive_ru(planet_a)
    gb = planet_marker_genitive_ru(planet_b)
    if ga and gb:
        return f"Маркеры {ga} и {gb} выглядят правильно?"
    return "Маркеры планет выглядят правильно?"


def build_review_questions(planet_a: str | None, planet_b: str | None) -> list[str]:
    """Deterministic review worksheet lines with aspect-aware marker wording."""
    return [
        "Основная картинка сильнее альтернативной?",
        "Символы планет видны, но не перегружены?",
        "Планетные знаки на **флагах** нарисованы **в ткани** (геральдика, перспектива полотна), а не как белые «наклейки» поверх морд?",
        "Каждый требуемый знак на флаге — канонический Unicode-глиф (как в реестре Catstyle), читаемый на мобильном?",
        "Отклонить, если любой планетный символ искажён, похож на случайную руну или латинскую букву вместо глифа?",
        marker_visibility_question_ru(planet_a, planet_b),
        "Картинка избегает CGI/game-render/детского mascot-стиля?",
        "Зодиакальная арена читается без визуального мусора?",
        "Композиция достаточно сильная для первого слайда Instagram?",
        "Hook короткий и острый?",
        "Caption звучит как Catstyle: космично, дерзко, чуть саркастично, но полезно?",
        "Компенсация практичная, а не generic?",
        "Текст карусели можно использовать?",
        "Package quality готов?",
        "Ты бы опубликовал это вручную сегодня?",
        "Что нужно поправить перед публикацией?",
    ]


REVIEW_QUESTIONS: list[str] = build_review_questions("Jupiter", "Mars")

SUGGESTED_DECISIONS: list[dict[str, str]] = [
    {
        "value": "approve",
        "description": "Ship as-is after any tiny polish (typos, line breaks). Images and copy are good enough to post manually.",
    },
    {
        "value": "revise_text",
        "description": "Keep the approved images; rewrite hook, caption, compensation, and/or carousel text before publishing.",
    },
    {
        "value": "regenerate_images",
        "description": "Copy direction is acceptable; rerun image generation or pick alternates, then re-run post package + QC.",
    },
    {
        "value": "reject",
        "description": "Do not publish this package. Restart from prompts, references, or aspect selection.",
    },
]


def _review_planet_pair_from_post_package(pkg: dict[str, Any]) -> tuple[str | None, str | None]:
    """Prefer explicit post-package aspect fields, then manual override, then first job summary row."""

    def _pick_str(raw: Any) -> str | None:
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return None

    pa = _pick_str(pkg.get("planet_a"))
    pb = _pick_str(pkg.get("planet_b"))

    mo_pkg = pkg.get("manual_aspect_override")
    if isinstance(mo_pkg, dict) and mo_pkg.get("enabled") is True:
        pa = pa or _pick_str(mo_pkg.get("planet_a"))
        pb = pb or _pick_str(mo_pkg.get("planet_b"))

    summary = pkg.get("image_jobs_summary")
    if isinstance(summary, list) and summary:
        row = summary[0]
        if isinstance(row, dict):
            pa = pa or _pick_str(row.get("planet_a"))
            pb = pb or _pick_str(row.get("planet_b"))

    return pa, pb


def load_catstyle_post_package_json(package_dir: Path | str) -> dict[str, Any]:
    """Load ``post_package.json`` from a Catstyle post package directory."""
    root = Path(package_dir).expanduser().resolve()
    jp = root / "post_package.json"
    if not jp.is_file():
        raise FileNotFoundError(f"Missing post_package.json in {root}")
    raw = jp.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("post_package.json root must be a JSON object.")
    return data


class CatstyleManualReview(BaseModel):
    """Human-facing review worksheet derived from ``post_package.json`` + optional QC."""

    version: str = MANUAL_REVIEW_VERSION
    date: str
    package_dir: str
    quality_status: Literal["ready", "needs_attention"]
    quality_score: int = Field(ge=0, le=100)
    quality_errors: list[str] = Field(default_factory=list)
    quality_warnings: list[str] = Field(default_factory=list)
    recommended_primary_image: str | None = None
    generated_image_paths: list[str] = Field(default_factory=list)
    style_reference_image_path: str | None = None
    aspect_summary: str | None = None
    manual_aspect_override: dict[str, Any] | None = None
    hook: str = ""
    caption: str = ""
    compensation: str = ""
    checklist: str = ""
    carousel_slide_text: str = ""
    review_questions: list[str] = Field(default_factory=list)
    suggested_decisions: list[dict[str, str]] = Field(default_factory=list)
    approval_status: Literal["pending_review", "approve", "revise_text", "regenerate_images", "reject"] = (
        "pending_review"
    )
    reviewer_notes: str = ""
    reviewed_at: str | None = Field(
        default=None,
        description="UTC ISO-8601 timestamp when approval was recorded (timezone-aware).",
    )


def build_catstyle_manual_review(
    package_dir: Path | str,
    *,
    quality_result: CatstylePostPackageQualityResult | None = None,
) -> CatstyleManualReview:
    """Build a manual review record from ``post_package.json`` and the quality gate."""
    root = Path(package_dir).expanduser().resolve()
    pkg = load_catstyle_post_package_json(root)

    qc = quality_result if quality_result is not None else check_catstyle_post_package(root)

    date = str(pkg.get("date") or "").strip()
    if not date:
        raise ValueError("post_package.json missing required field: date")

    gen_paths = pkg.get("generated_image_paths")
    paths_out: list[str] = []
    if isinstance(gen_paths, list):
        paths_out = [str(x) for x in gen_paths if isinstance(x, str) and str(x).strip()]

    primary = pkg.get("recommended_primary_image")
    primary_out = str(primary).strip() if isinstance(primary, str) and primary.strip() else None

    style_ref = pkg.get("style_reference_image_path")
    style_out = str(style_ref).strip() if isinstance(style_ref, str) and style_ref.strip() else None

    asp_sum = pkg.get("aspect_summary")
    aspect_summary_out = str(asp_sum).strip() if isinstance(asp_sum, str) and asp_sum.strip() else None

    mo_pkg = pkg.get("manual_aspect_override")
    manual_override_out: dict[str, Any] | None = None
    if isinstance(mo_pkg, dict) and mo_pkg.get("enabled") is True:
        manual_override_out = {
            "enabled": True,
            "planet_a": str(mo_pkg.get("planet_a") or ""),
            "planet_b": str(mo_pkg.get("planet_b") or ""),
            "aspect_type": str(mo_pkg.get("aspect_type") or ""),
            "mode": str(mo_pkg.get("mode") or ""),
        }

    car = pkg.get("carousel_slide_text")
    carousel = str(car) if isinstance(car, str) else ""

    def _str_field(key: str) -> str:
        v = pkg.get(key)
        return str(v) if isinstance(v, str) else ""

    rq_pa, rq_pb = _review_planet_pair_from_post_package(pkg)

    return CatstyleManualReview(
        date=date,
        package_dir=str(root),
        quality_status=qc.status,
        quality_score=qc.score,
        quality_errors=list(qc.errors),
        quality_warnings=list(qc.warnings),
        recommended_primary_image=primary_out,
        generated_image_paths=paths_out,
        style_reference_image_path=style_out,
        aspect_summary=aspect_summary_out,
        manual_aspect_override=manual_override_out,
        hook=_str_field("hook"),
        caption=_str_field("caption"),
        compensation=_str_field("compensation"),
        checklist=_str_field("checklist"),
        carousel_slide_text=carousel,
        review_questions=build_review_questions(rq_pa, rq_pb),
        suggested_decisions=list(SUGGESTED_DECISIONS),
        approval_status="pending_review",
        reviewer_notes="",
        reviewed_at=None,
    )


def render_catstyle_manual_review_markdown(review: CatstyleManualReview) -> str:
    """Readable Markdown worksheet for producers."""
    lines: list[str] = [
        f"# Catstyle manual review — {review.date}",
        "",
        "## Package summary",
        "",
        f"- **Package directory:** `{review.package_dir}`",
        f"- **Recommended primary image:** {review.recommended_primary_image or '_(none)_'}",
        f"- **Style reference:** {review.style_reference_image_path or '_(none)_'}",
        f"- **Aspect summary:** {review.aspect_summary or '_(none)_'}",
        "",
    ]
    if review.manual_aspect_override:
        mo = review.manual_aspect_override
        lines.append(
            f"- **Manual aspect override:** `{mo.get('planet_a')}` `{mo.get('aspect_type')}` `{mo.get('planet_b')}` "
            f"(mode=`{mo.get('mode')}`)"
        )
        lines.append("")
    lines.extend(
        [
        "## Quality summary",
        "",
        f"- **Status:** {review.quality_status}",
        f"- **Score:** {review.quality_score}",
        "",
        ]
    )
    lines.extend(["### Quality errors", ""])
    if review.quality_errors:
        for e in review.quality_errors:
            lines.append(f"- {e}")
    else:
        lines.append("- _(none)_")
    lines.extend(["", "### Quality warnings", ""])
    if review.quality_warnings:
        for w in review.quality_warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- _(none)_")

    lines.extend(
        [
            "",
            "## Generated images",
            "",
        ]
    )
    if review.generated_image_paths:
        for p in review.generated_image_paths:
            lines.append(f"- `{p}`")
    else:
        lines.append("- _(none listed)_")

    lines.extend(
        [
            "",
            "## Hook",
            "",
            review.hook or "_(empty)_",
            "",
            "## Caption",
            "",
            review.caption or "_(empty)_",
            "",
            "## Compensation",
            "",
            review.compensation or "_(empty)_",
            "",
            "## Post checklist (from package)",
            "",
            review.checklist or "_(empty)_",
            "",
            "## Carousel text",
            "",
            review.carousel_slide_text or "_(empty)_",
            "",
            "## Review questions",
            "",
        ]
    )
    for i, q in enumerate(review.review_questions, start=1):
        lines.append(f"{i}. {q}")
        lines.append("   - [ ] Заметки: _______________________________________________")
    lines.extend(
        [
            "",
            "## Suggested decisions (reference)",
            "",
        ]
    )
    for sd in review.suggested_decisions:
        lines.append(f"- **`{sd['value']}`:** {sd['description']}")
    reviewed_line = review.reviewed_at if review.reviewed_at else "_(ещё не зафиксировано)_"
    notes_body = review.reviewer_notes.strip() if review.reviewer_notes.strip() else "_(пусто)_"

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- **approval_status:** `{review.approval_status}`",
            f"- **reviewed_at:** {reviewed_line}",
            "",
            "### Заметки рецензента",
            "",
            notes_body,
            "",
        ]
    )
    return "\n".join(lines)


def write_catstyle_manual_review(
    review: CatstyleManualReview,
    output_dir: Path | str,
    *,
    overwrite: bool = False,
) -> list[str]:
    """Write ``manual_review.json`` (UTF-8) and ``manual_review.md`` (UTF-8 with BOM)."""
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    targets: dict[str, tuple[str, str]] = {
        "manual_review.json": ("utf-8", json.dumps(review.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"),
        "manual_review.md": ("utf-8-sig", render_catstyle_manual_review_markdown(review).rstrip("\n") + "\n"),
    }

    written: list[str] = []
    for name, (enc, body) in targets.items():
        dest = out / name
        if dest.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file (use --overwrite): {dest}")
        dest.write_text(body, encoding=enc)
        written.append(name)
    return written


def load_catstyle_manual_review(package_dir: Path | str) -> CatstyleManualReview:
    """Load ``manual_review.json`` from a Catstyle package directory."""
    root = Path(package_dir).expanduser().resolve()
    mr_path = root / "manual_review.json"
    if not mr_path.is_file():
        raise FileNotFoundError(f"Missing manual_review.json in {root}")
    raw = mr_path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("manual_review.json root must be a JSON object.")
    return CatstyleManualReview.model_validate(data)


def approve_catstyle_manual_review(
    package_dir: Path | str,
    decision: str,
    reviewer_notes: str = "",
    *,
    overwrite: bool = True,
) -> CatstyleManualReview:
    """Update ``manual_review.json`` / ``manual_review.md`` with reviewer decision and UTC timestamp."""
    root = Path(package_dir).expanduser().resolve()
    key = str(decision).strip().lower()
    if key not in ALLOWED_APPROVAL_DECISIONS:
        raise ValueError(
            f"Invalid decision {decision!r}. Allowed: {', '.join(sorted(ALLOWED_APPROVAL_DECISIONS))}."
        )

    review = load_catstyle_manual_review(root)
    reviewed_iso = datetime.now(timezone.utc).isoformat()

    updated = review.model_copy(
        update={
            "approval_status": key,  # type: ignore[arg-type]
            "reviewer_notes": str(reviewer_notes) if reviewer_notes is not None else "",
            "reviewed_at": reviewed_iso,
        }
    )

    write_catstyle_manual_review(updated, root, overwrite=overwrite)
    return updated


__all__ = [
    "ALLOWED_APPROVAL_DECISIONS",
    "MANUAL_REVIEW_VERSION",
    "build_review_questions",
    "marker_visibility_question_ru",
    "planet_marker_genitive_ru",
    "REVIEW_QUESTIONS",
    "SUGGESTED_DECISIONS",
    "CatstyleManualReview",
    "approve_catstyle_manual_review",
    "build_catstyle_manual_review",
    "load_catstyle_manual_review",
    "load_catstyle_post_package_json",
    "render_catstyle_manual_review_markdown",
    "write_catstyle_manual_review",
]
