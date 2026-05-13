"""Catstyle Publish Handoff v1 — final local bundle after approved manual review (no APIs)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.models import CatstyleAspectTimingMetadata
from astro_content_agent.services.content.catstyle_aspect_timing import render_aspect_timing_markdown_section
from astro_content_agent.services.content.catstyle_manual_review import load_catstyle_manual_review
from astro_content_agent.services.content.catstyle_post_package import CatstylePostPackage

PUBLISH_HANDOFF_VERSION = "catstyle-publish-handoff-v1"


class CatstylePublishHandoffError(ValueError):
    """Blocked publish handoff (approval / QC / assets)."""


class CatstylePublishHandoff(BaseModel):
    """Deterministic handoff for manual Instagram publishing."""

    version: str = PUBLISH_HANDOFF_VERSION
    date: str
    package_dir: str
    source_post_package_path: str
    source_manual_review_path: str
    publish_status: Literal["ready_for_manual_publish"] = "ready_for_manual_publish"
    approval_status: str
    reviewed_at: str | None = None
    reviewer_notes: str = ""
    recommended_primary_image: str
    generated_image_paths: list[str] = Field(default_factory=list)
    caption_final: str
    hook: str
    carousel_text: str
    compensation: str
    publish_checklist: str
    created_at: str = Field(
        ...,
        description="UTC ISO-8601 when the handoff artifact was created.",
    )
    aspect_timing: CatstyleAspectTimingMetadata | None = Field(
        default=None,
        description="Echo of post_package aspect_timing for producers (UTC scan-derived).",
    )


def _load_post_package_model(package_dir: Path) -> CatstylePostPackage:
    jp = package_dir / "post_package.json"
    if not jp.is_file():
        raise FileNotFoundError(f"Missing post_package.json in {package_dir}")
    raw = jp.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("post_package.json root must be a JSON object.")
    return CatstylePostPackage.model_validate(data)


def build_catstyle_publish_handoff(package_dir: Path | str) -> CatstylePublishHandoff:
    """Load package + manual review and validate gates for a publish handoff."""
    root = Path(package_dir).expanduser().resolve()

    pkg = _load_post_package_model(root)
    mr = load_catstyle_manual_review(root)

    if mr.approval_status != "approve":
        raise CatstylePublishHandoffError(
            f"Publish handoff requires manual_review approval_status 'approve' (got {mr.approval_status!r})."
        )

    if mr.quality_status != "ready":
        raise CatstylePublishHandoffError(
            f"Publish handoff requires manual_review quality_status 'ready' (got {mr.quality_status!r})."
        )

    if mr.quality_score < 85:
        raise CatstylePublishHandoffError(
            f"Publish handoff requires manual_review quality_score >= 85 (got {mr.quality_score})."
        )

    hook = pkg.hook.strip()
    caption = pkg.caption.strip()
    if not hook:
        raise CatstylePublishHandoffError("Publish handoff requires non-empty hook in post_package.json.")
    if not caption:
        raise CatstylePublishHandoffError("Publish handoff requires non-empty caption in post_package.json.")

    primary = (pkg.recommended_primary_image or "").strip() or (mr.recommended_primary_image or "").strip()
    if not primary:
        raise CatstylePublishHandoffError("Publish handoff requires recommended_primary_image in the package.")

    pth = Path(primary).expanduser()
    if not pth.is_file():
        raise CatstylePublishHandoffError(f"recommended_primary_image path does not exist: {primary}")

    paths_out = [str(x) for x in pkg.generated_image_paths if isinstance(x, str) and str(x).strip()]
    created_iso = datetime.now(timezone.utc).isoformat()

    return CatstylePublishHandoff(
        date=str(pkg.date).strip(),
        package_dir=str(root),
        source_post_package_path=str((root / "post_package.json").resolve()),
        source_manual_review_path=str((root / "manual_review.json").resolve()),
        publish_status="ready_for_manual_publish",
        approval_status=mr.approval_status,
        reviewed_at=mr.reviewed_at,
        reviewer_notes=str(mr.reviewer_notes or ""),
        recommended_primary_image=str(pth.resolve()),
        generated_image_paths=paths_out,
        caption_final=caption,
        hook=hook,
        carousel_text=str(pkg.carousel_slide_text or ""),
        compensation=str(pkg.compensation or ""),
        publish_checklist=str(pkg.checklist or ""),
        created_at=created_iso,
        aspect_timing=pkg.aspect_timing,
    )


def render_catstyle_publish_handoff_markdown(h: CatstylePublishHandoff) -> str:
    """Human-readable Markdown for the producer."""
    lines: list[str] = [
        f"# Catstyle publish handoff — {h.date}",
        "",
        "## Status",
        "",
        f"- **publish_status:** `{h.publish_status}`",
        f"- **created_at:** {h.created_at}",
        "",
        "## Approval summary",
        "",
        f"- **approval_status:** `{h.approval_status}`",
        f"- **reviewed_at:** {h.reviewed_at or '_(none)_'}",
        "",
        "### Reviewer notes",
        "",
        (h.reviewer_notes.strip() or "_(none)_"),
        "",
        "## Primary image",
        "",
        f"`{h.recommended_primary_image}`",
        "",
        "## Caption (final)",
        "",
        h.caption_final,
        "",
    ]
    if h.aspect_timing is not None:
        lines.extend(render_aspect_timing_markdown_section(h.aspect_timing).rstrip("\n").split("\n"))
    lines.extend(
        [
            "## Hook",
            "",
            h.hook,
            "",
            "## Carousel text",
            "",
            h.carousel_text or "_(empty)_",
            "",
            "## Compensation",
            "",
            h.compensation or "_(empty)_",
            "",
            "## Manual publish checklist",
            "",
            h.publish_checklist or "_(empty)_",
            "",
            "## Generated images",
            "",
        ]
    )
    if h.generated_image_paths:
        for p in h.generated_image_paths:
            lines.append(f"- `{p}`")
    else:
        lines.append("- _(none)_")

    lines.extend(
        [
            "",
            "## Sources",
            "",
            f"- **post_package.json:** `{h.source_post_package_path}`",
            f"- **manual_review.json:** `{h.source_manual_review_path}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_catstyle_publish_handoff(
    handoff: CatstylePublishHandoff,
    output_dir: Path | str,
    *,
    overwrite: bool = False,
) -> list[str]:
    """Write handoff JSON/Markdown and snippet files."""
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    payloads: dict[str, tuple[str, str]] = {
        "publish_handoff.json": (
            "utf-8",
            json.dumps(handoff.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        ),
        "publish_handoff.md": ("utf-8-sig", render_catstyle_publish_handoff_markdown(handoff).rstrip("\n") + "\n"),
        "caption_final.txt": ("utf-8-sig", handoff.caption_final + "\n"),
        "primary_image_path.txt": ("utf-8-sig", handoff.recommended_primary_image + "\n"),
        "publish_checklist.txt": ("utf-8-sig", handoff.publish_checklist + "\n"),
    }

    written: list[str] = []
    for name, (enc, body) in payloads.items():
        dest = out / name
        if dest.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file (use --overwrite): {dest}")
        dest.write_text(body, encoding=enc)
        written.append(name)
    return written


__all__ = [
    "PUBLISH_HANDOFF_VERSION",
    "CatstylePublishHandoff",
    "CatstylePublishHandoffError",
    "build_catstyle_publish_handoff",
    "render_catstyle_publish_handoff_markdown",
    "write_catstyle_publish_handoff",
]
