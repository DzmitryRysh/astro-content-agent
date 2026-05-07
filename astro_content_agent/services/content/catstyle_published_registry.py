"""Catstyle Published Registry v1 — mark ready handoff as manually published."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


PUBLISHED_RECORD_VERSION = "catstyle-published-record-v1"


class CatstylePublishedRegistryError(ValueError):
    """Invalid handoff state for marking as published."""


class CatstylePublishedRecord(BaseModel):
    """Persistent record of manual Instagram publication."""

    version: str = PUBLISHED_RECORD_VERSION
    publish_state: Literal["published_manual"] = "published_manual"
    published_at: str = Field(..., description="Timezone-aware UTC ISO-8601 publish timestamp.")
    handoff_dir: str
    source_publish_handoff_path: str
    recommended_primary_image: str
    caption_final: str
    hook: str
    instagram_url: str | None = None
    notes: str = ""


def _load_handoff(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing publish_handoff.json in {path.parent}")
    raw = path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("publish_handoff.json root must be a JSON object.")
    return data


def mark_catstyle_handoff_published(
    handoff_dir: Path | str,
    *,
    instagram_url: str | None = None,
    notes: str | None = None,
) -> CatstylePublishedRecord:
    """Create a deterministic manual publish record for a ready handoff folder."""
    root = Path(handoff_dir).expanduser().resolve()
    hp = root / "publish_handoff.json"
    handoff = _load_handoff(hp)

    status = str(handoff.get("publish_status") or "").strip()
    if status != "ready_for_manual_publish":
        raise CatstylePublishedRegistryError(
            f"Cannot mark published: publish_handoff publish_status must be 'ready_for_manual_publish' (got {status!r})."
        )

    primary = str(handoff.get("recommended_primary_image") or "").strip()
    caption = str(handoff.get("caption_final") or "").strip()
    hook = str(handoff.get("hook") or "").strip()
    if not primary:
        raise CatstylePublishedRegistryError("publish_handoff.json missing required field: recommended_primary_image")
    if not caption:
        raise CatstylePublishedRegistryError("publish_handoff.json missing required field: caption_final")
    if not hook:
        raise CatstylePublishedRegistryError("publish_handoff.json missing required field: hook")

    ig = str(instagram_url).strip() if instagram_url is not None else None
    ig = ig if ig else None
    nts = str(notes).strip() if notes is not None else ""

    return CatstylePublishedRecord(
        published_at=datetime.now(timezone.utc).isoformat(),
        handoff_dir=str(root),
        source_publish_handoff_path=str(hp.resolve()),
        recommended_primary_image=primary,
        caption_final=caption,
        hook=hook,
        instagram_url=ig,
        notes=nts,
    )


def render_catstyle_published_record_markdown(record: CatstylePublishedRecord) -> str:
    """Human-readable markdown for manual publication record."""
    lines: list[str] = [
        "# Catstyle published record",
        "",
        "## Status",
        "",
        f"- **publish_state:** `{record.publish_state}`",
        f"- **published_at:** {record.published_at}",
        f"- **instagram_url:** {record.instagram_url or '_(none)_'}",
        "",
        "## Sources",
        "",
        f"- **handoff_dir:** `{record.handoff_dir}`",
        f"- **publish_handoff.json:** `{record.source_publish_handoff_path}`",
        "",
        "## Primary image",
        "",
        f"`{record.recommended_primary_image}`",
        "",
        "## Hook",
        "",
        record.hook,
        "",
        "## Caption",
        "",
        record.caption_final,
        "",
        "## Notes",
        "",
        record.notes or "_(none)_",
        "",
    ]
    return "\n".join(lines)


def write_catstyle_published_record(
    record: CatstylePublishedRecord,
    output_dir: Path | str,
    *,
    overwrite: bool = False,
) -> list[str]:
    """Write ``publish_record.json`` and ``publish_record.md`` under handoff directory."""
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    payloads: dict[str, tuple[str, str]] = {
        "publish_record.json": (
            "utf-8",
            json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        ),
        "publish_record.md": ("utf-8-sig", render_catstyle_published_record_markdown(record).rstrip("\n") + "\n"),
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
    "PUBLISHED_RECORD_VERSION",
    "CatstylePublishedRecord",
    "CatstylePublishedRegistryError",
    "mark_catstyle_handoff_published",
    "render_catstyle_published_record_markdown",
    "write_catstyle_published_record",
]
