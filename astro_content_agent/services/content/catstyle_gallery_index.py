"""Catstyle Gallery Index v1 — deterministic local index for publish handoffs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


GALLERY_INDEX_VERSION = "catstyle-gallery-index-v1"


class CatstyleGalleryIndexEntry(BaseModel):
    """One indexed publish handoff row."""

    date: str
    publish_status: str
    approval_status: str
    reviewed_at: str | None = None
    created_at: str | None = None
    recommended_primary_image: str
    caption_preview: str
    hook: str
    reviewer_notes: str = ""
    source_post_package_path: str
    source_manual_review_path: str
    handoff_dir: str
    publish_state: str | None = None
    published_at: str | None = None
    instagram_url: str | None = None
    planet_a: str | None = None
    planet_b: str | None = None
    aspect_type: str | None = None
    mode: str | None = None
    aspect_summary: str | None = None
    manual_aspect_override: dict[str, Any] | None = None


class CatstyleGalleryIndex(BaseModel):
    """Result bundle for gallery index build + write."""

    version: str = GALLERY_INDEX_VERSION
    generated_at: str
    handoffs_dir: str
    include_not_ready: bool = False
    posts_indexed: int
    entries: list[CatstyleGalleryIndexEntry] = Field(default_factory=list)


def _read_json_object(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def _caption_preview(caption: str, max_len: int = 140) -> str:
    s = " ".join((caption or "").split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def _clean_opt_str(raw: Any) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _extract_aspect_metadata(
    handoff_obj: dict[str, Any],
    handoff_dir: Path,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "planet_a": _clean_opt_str(handoff_obj.get("planet_a")),
        "planet_b": _clean_opt_str(handoff_obj.get("planet_b")),
        "aspect_type": _clean_opt_str(handoff_obj.get("aspect_type")),
        "mode": _clean_opt_str(handoff_obj.get("mode")),
        "aspect_summary": _clean_opt_str(handoff_obj.get("aspect_summary")),
        "manual_aspect_override": handoff_obj.get("manual_aspect_override")
        if isinstance(handoff_obj.get("manual_aspect_override"), dict)
        else None,
    }

    if meta["planet_a"] and meta["planet_b"] and meta["aspect_type"]:
        return meta

    spp = _clean_opt_str(handoff_obj.get("source_post_package_path"))
    if not spp:
        return meta

    post_path = Path(spp).expanduser()
    if not post_path.is_absolute():
        post_path = (handoff_dir / post_path).resolve()
    if not post_path.is_file():
        return meta

    try:
        post = _read_json_object(post_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return meta

    meta["planet_a"] = meta["planet_a"] or _clean_opt_str(post.get("planet_a"))
    meta["planet_b"] = meta["planet_b"] or _clean_opt_str(post.get("planet_b"))
    meta["aspect_type"] = meta["aspect_type"] or _clean_opt_str(post.get("aspect_type"))
    meta["mode"] = meta["mode"] or _clean_opt_str(post.get("mode"))
    meta["aspect_summary"] = meta["aspect_summary"] or _clean_opt_str(post.get("aspect_summary"))
    if meta["manual_aspect_override"] is None and isinstance(post.get("manual_aspect_override"), dict):
        meta["manual_aspect_override"] = post.get("manual_aspect_override")
    return meta


def _is_ready_for_publish(handoff_obj: dict[str, Any]) -> bool:
    return (
        _clean_opt_str(handoff_obj.get("publish_status")) == "ready_for_manual_publish"
        and _clean_opt_str(handoff_obj.get("approval_status")) == "approve"
    )


def _load_publish_record_meta(handoff_dir: Path) -> dict[str, str | None]:
    rp = handoff_dir / "publish_record.json"
    if not rp.is_file():
        return {"publish_state": None, "published_at": None, "instagram_url": None}
    try:
        rec = _read_json_object(rp)
    except (OSError, json.JSONDecodeError, ValueError):
        return {"publish_state": None, "published_at": None, "instagram_url": None}
    return {
        "publish_state": _clean_opt_str(rec.get("publish_state")),
        "published_at": _clean_opt_str(rec.get("published_at")),
        "instagram_url": _clean_opt_str(rec.get("instagram_url")),
    }


def _build_entry(handoff_path: Path) -> CatstyleGalleryIndexEntry | None:
    try:
        handoff_obj = _read_json_object(handoff_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return None

    date = _clean_opt_str(handoff_obj.get("date"))
    publish_status = _clean_opt_str(handoff_obj.get("publish_status"))
    approval_status = _clean_opt_str(handoff_obj.get("approval_status"))
    primary = _clean_opt_str(handoff_obj.get("recommended_primary_image"))
    caption_final = _clean_opt_str(handoff_obj.get("caption_final"))
    hook = _clean_opt_str(handoff_obj.get("hook"))
    spp = _clean_opt_str(handoff_obj.get("source_post_package_path"))
    smr = _clean_opt_str(handoff_obj.get("source_manual_review_path"))

    if not (date and publish_status and approval_status and primary and caption_final and hook and spp and smr):
        return None

    meta = _extract_aspect_metadata(handoff_obj, handoff_path.parent)

    published_meta = _load_publish_record_meta(handoff_path.parent)

    return CatstyleGalleryIndexEntry(
        date=date,
        publish_status=publish_status,
        approval_status=approval_status,
        reviewed_at=_clean_opt_str(handoff_obj.get("reviewed_at")),
        created_at=_clean_opt_str(handoff_obj.get("created_at")),
        recommended_primary_image=primary,
        caption_preview=_caption_preview(caption_final),
        hook=hook,
        reviewer_notes=_clean_opt_str(handoff_obj.get("reviewer_notes")) or "",
        source_post_package_path=spp,
        source_manual_review_path=smr,
        handoff_dir=str(handoff_path.parent.resolve()),
        publish_state=published_meta.get("publish_state"),
        published_at=published_meta.get("published_at"),
        instagram_url=published_meta.get("instagram_url"),
        planet_a=meta.get("planet_a"),
        planet_b=meta.get("planet_b"),
        aspect_type=meta.get("aspect_type"),
        mode=meta.get("mode"),
        aspect_summary=meta.get("aspect_summary"),
        manual_aspect_override=meta.get("manual_aspect_override"),
    )


def build_catstyle_gallery_index(
    handoffs_dir: Path | str = "catstyle_publish_handoffs",
    *,
    include_not_ready: bool = False,
) -> CatstyleGalleryIndex:
    """Scan publish handoff subfolders and build a deterministic local index."""
    root = Path(handoffs_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Handoffs directory not found: {root}")
    if not root.is_dir():
        raise ValueError(f"Handoffs path must be a directory: {root}")

    handoff_paths = sorted({p.resolve() for p in root.rglob("publish_handoff.json")}, key=lambda p: str(p.parent))
    entries: list[CatstyleGalleryIndexEntry] = []
    for hp in handoff_paths:
        entry = _build_entry(hp)
        if entry is None:
            continue
        if not include_not_ready and not _is_ready_for_publish(_read_json_object(hp)):
            continue
        entries.append(entry)

    entries.sort(key=lambda e: (e.date, e.created_at or "", e.handoff_dir), reverse=True)
    return CatstyleGalleryIndex(
        generated_at=datetime.now(timezone.utc).isoformat(),
        handoffs_dir=str(root),
        include_not_ready=include_not_ready,
        posts_indexed=len(entries),
        entries=entries,
    )


def _aspect_cell(entry: CatstyleGalleryIndexEntry) -> str:
    if entry.aspect_summary:
        return entry.aspect_summary
    if entry.planet_a and entry.planet_b and entry.aspect_type:
        mode_tail = f" ({entry.mode})" if entry.mode else ""
        return f"{entry.planet_a} {entry.aspect_type} {entry.planet_b}{mode_tail}"
    return "—"


def render_catstyle_gallery_index_markdown(index: CatstyleGalleryIndex) -> str:
    """Human-readable markdown view of indexed publish handoffs."""
    lines: list[str] = [
        "# Catstyle gallery index",
        "",
        f"- **generated_at:** {index.generated_at}",
        f"- **handoffs_dir:** `{index.handoffs_dir}`",
        f"- **total posts indexed:** {index.posts_indexed}",
        "",
        "## Posts",
        "",
        "| date | aspect | status | primary image | caption preview | handoff path |",
        "|---|---|---|---|---|---|",
    ]
    for e in index.entries:
        state = e.publish_state or e.publish_status
        status = f"{state} / {e.approval_status}"
        lines.append(
            f"| {e.date} | {_aspect_cell(e)} | {status} | `{e.recommended_primary_image}` | "
            f"{e.caption_preview.replace('|', '/')} | `{e.handoff_dir}` |"
        )
    if not index.entries:
        lines.append("| _(none)_ | — | — | — | — | — |")

    lines.extend(["", "## Details", ""])
    for i, e in enumerate(index.entries, start=1):
        lines.extend(
            [
                f"### {i}. {e.date} — {_aspect_cell(e)}",
                "",
                f"- **publish_state:** `{e.publish_state or '_(none)_'}`",
                f"- **publish_status:** `{e.publish_status}`",
                f"- **approval_status:** `{e.approval_status}`",
                f"- **published_at:** {e.published_at or '_(none)_'}",
                f"- **reviewed_at:** {e.reviewed_at or '_(none)_'}",
                f"- **created_at:** {e.created_at or '_(none)_'}",
                f"- **instagram_url:** {e.instagram_url or '_(none)_'}",
                f"- **primary image:** `{e.recommended_primary_image}`",
                f"- **publish handoff path:** `{e.handoff_dir}`",
                f"- **post package source:** `{e.source_post_package_path}`",
                f"- **manual review source:** `{e.source_manual_review_path}`",
                "",
                "#### Hook",
                "",
                e.hook,
                "",
                "#### Caption preview",
                "",
                e.caption_preview,
                "",
                "#### Reviewer notes",
                "",
                e.reviewer_notes or "_(none)_",
                "",
            ]
        )
    return "\n".join(lines)


def write_catstyle_gallery_index(
    index: CatstyleGalleryIndex,
    output_dir: Path | str = "catstyle_publish_handoffs",
    *,
    overwrite: bool = True,
) -> list[str]:
    """Write ``gallery_index.json`` and ``gallery_index.md``."""
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    payloads: dict[str, tuple[str, str]] = {
        "gallery_index.json": (
            "utf-8",
            json.dumps(index.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        ),
        "gallery_index.md": ("utf-8-sig", render_catstyle_gallery_index_markdown(index).rstrip("\n") + "\n"),
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
    "GALLERY_INDEX_VERSION",
    "CatstyleGalleryIndex",
    "CatstyleGalleryIndexEntry",
    "build_catstyle_gallery_index",
    "render_catstyle_gallery_index_markdown",
    "write_catstyle_gallery_index",
]
