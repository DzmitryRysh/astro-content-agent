"""Approved weekly pack → structured publish handoff JSON (no Instagram API).

Reads ``venus_weekly_state_*.json`` + existing post/reel/support markdown drafts.
Gate: ``status`` must be ``approved``. Does not regenerate LLM content.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


def _split_sections(md: str) -> dict[str, str]:
    """Split markdown body on ``## Heading`` lines; keys are heading text (trimmed)."""
    sections: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for line in md.splitlines():
        if line.startswith("## "):
            if key is not None:
                sections[key] = "\n".join(buf).strip()
            key = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if key is not None:
        sections[key] = "\n".join(buf).strip()
    return sections


def _parse_hashtag_block(text: str) -> list[str]:
    tags: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            t = line[2:].strip()
            if t and t != "-":
                tags.append(t)
    return tags


def _first_line_title(hook: str, caption: str, *, max_len: int = 120) -> str:
    for raw in (hook, caption):
        line = raw.strip().split("\n", 1)[0].strip()
        if line:
            return line if len(line) <= max_len else line[: max_len - 1].rstrip() + "…"
    return "Venus weekly post"


def parse_weekly_post_draft(md: str) -> dict[str, Any]:
    sec = _split_sections(md)
    hook = sec.get("Hook", "")
    caption = sec.get("Caption", "")
    cta = sec.get("CTA", "")
    ht_raw = sec.get("Hashtags", "")
    return {
        "type": "post",
        "title": _first_line_title(hook, caption),
        "hook": hook,
        "body": caption,
        "cta": cta,
        "hashtags": _parse_hashtag_block(ht_raw),
    }


def parse_weekly_reel_draft(md: str) -> dict[str, Any]:
    sec = _split_sections(md)
    return {
        "type": "reel",
        "hook_0_3s": sec.get("hook_0_3s", ""),
        "spoken_hook": sec.get("Spoken hook", ""),
        "script": sec.get("Script", ""),
        "cta": sec.get("CTA", ""),
    }


def parse_weekly_support_draft(md: str) -> dict[str, Any]:
    sec = _split_sections(md)
    return {
        "type": "support",
        "lead": sec.get("Lead", ""),
        "body": sec.get("Body", ""),
        "cta": sec.get("CTA", ""),
    }


@dataclass
class PublishHandoffResult:
    week_start: str
    week_end: str
    out_json: Path
    out_md: Path | None
    items: list[dict[str, Any]]
    state: dict[str, Any]


def _default_week_dir(week_start: date, weekly_venus_root: Path) -> Path:
    return weekly_venus_root / week_start.isoformat()


def _state_path_for_week(week_start: date, weekly_venus_root: Path) -> Path:
    return _default_week_dir(week_start, weekly_venus_root) / f"venus_weekly_state_{week_start.isoformat()}.json"


def _resolve_draft_paths(
    week_dir: Path,
    week_start: str,
    state: dict[str, Any],
) -> tuple[Path, Path, Path | None]:
    outs = state.get("outputs")
    if not isinstance(outs, dict):
        outs = {}
    post_n = outs.get("post_draft") or f"venus_weekly_post_{week_start}.md"
    reel_n = outs.get("reel_draft") or f"venus_weekly_reel_{week_start}.md"
    post_p = week_dir / post_n
    reel_p = week_dir / reel_n
    support_p: Path | None = None
    if outs.get("support_draft"):
        cand = week_dir / str(outs["support_draft"])
        if cand.is_file():
            support_p = cand
    else:
        cand = week_dir / f"venus_weekly_support_{week_start}.md"
        if cand.is_file():
            support_p = cand
    return post_p, reel_p, support_p


_MOJIBAKE_MARKERS = ("Ð", "Ñ", "â", "Ã")
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def _looks_like_utf8_mojibake(text: str) -> bool:
    """Heuristic: detect common UTF-8-decoded-as-Latin1/CP1252 artifacts.

    This does not attempt repair; it raises a clear error so operators can
    regenerate the weekly drafts from source.
    """
    if not text:
        return False
    if _CYRILLIC_RE.search(text):
        return False
    # Typical artifacts for Cyrillic corruption include dense Ð/Ñ digrams.
    marker_count = sum(text.count(m) for m in _MOJIBAKE_MARKERS)
    return marker_count >= 3 and ("Ð " in text or "Ñ" in text)


def _read_markdown_utf8(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    if _looks_like_utf8_mojibake(text):
        raise ValueError(
            f"Markdown appears already mojibake-corrupted: {path}. "
            "Rebuild/regenerate weekly draft markdown as UTF-8, then rerun build_venus_publish_handoff.py."
        )
    return text


def build_publish_handoff(
    *,
    week_dir: Path,
    state_path: Path | None = None,
    week_start_hint: str | None = None,
    write_markdown_summary: bool = True,
) -> PublishHandoffResult:
    """Build ``venus_publish_handoff_<week_start>.json`` under *week_dir*.

    Draft markdown is read from *week_dir*. State JSON is loaded from *state_path* if given,
    otherwise the sole ``venus_weekly_state_*.json`` in *week_dir*.

    Raises ``ValueError`` with a clear message if the pack is not approved or drafts are missing.
    """
    week_dir = Path(week_dir)
    if state_path is not None:
        resolved_state_path = Path(state_path)
        state: dict[str, Any] = json.loads(resolved_state_path.read_text(encoding="utf-8"))
    else:
        hint = week_start_hint or week_dir.name
        exact = week_dir / f"venus_weekly_state_{hint}.json"
        if exact.is_file():
            resolved_state_path = exact
            state = json.loads(resolved_state_path.read_text(encoding="utf-8"))
        else:
            matches = sorted(week_dir.glob("venus_weekly_state_*.json"))
            if not matches:
                raise ValueError(f"No venus_weekly_state_*.json in {week_dir}")
            if len(matches) > 1:
                raise ValueError(
                    f"Multiple state files in {week_dir}; pass --state-file or use folder name = week_start: "
                    f"{', '.join(m.name for m in matches)}"
                )
            resolved_state_path = matches[0]
            state = json.loads(resolved_state_path.read_text(encoding="utf-8"))

    ws = str(state.get("week_start") or week_dir.name)
    we = str(state.get("week_end") or "")
    if str(state.get("status", "")) != "approved":
        raise ValueError(
            f"Handoff requires status 'approved'; got {state.get('status')!r}. "
            "Run approve_venus_weekly.py approve first."
        )

    post_p, reel_p, support_p = _resolve_draft_paths(week_dir, ws, state)
    if not post_p.is_file():
        raise ValueError(f"Missing post draft: {post_p}")
    if not reel_p.is_file():
        raise ValueError(f"Missing reel draft: {reel_p}")

    post_item = parse_weekly_post_draft(_read_markdown_utf8(post_p))
    reel_item = parse_weekly_reel_draft(_read_markdown_utf8(reel_p))
    items: list[dict[str, Any]] = [post_item, reel_item]
    if support_p is not None:
        items.append(parse_weekly_support_draft(_read_markdown_utf8(support_p)))

    approved_at = state.get("approval_timestamp") or ""
    payload: dict[str, Any] = {
        "version": 1,
        "week_start": ws,
        "week_end": we,
        "status_snapshot": state.get("status"),
        "approved_at": approved_at,
        "climate": state.get("climate"),
        "overlay": {
            "active": state.get("overlay_active"),
            "pair": state.get("overlay_pair"),
        },
        "items": items,
        "sources": {
            "state": resolved_state_path.name,
            "post_draft": post_p.name,
            "reel_draft": reel_p.name,
            "support_draft": support_p.name if support_p else None,
        },
    }

    out_json = week_dir / f"venus_publish_handoff_{ws}.json"
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    out_md: Path | None = None
    if write_markdown_summary:
        out_md = week_dir / f"venus_publish_handoff_{ws}.md"
        lines = [
            f"# Venus publish handoff — {ws}",
            "",
            f"- **Week:** {ws} → {we}",
            f"- **Approved at:** {approved_at or '—'}",
            f"- **Handoff JSON:** `{out_json.name}`",
            "",
            "## Items",
            "",
        ]
        for it in items:
            t = it.get("type", "?")
            lines.append(f"### `{t}`")
            if t == "post":
                lines.append(f"- **Title:** {it.get('title', '')}")
            elif t == "reel":
                h = (it.get("hook_0_3s") or "").strip().split("\n")[0][:100]
                lines.append(f"- **0–3s hook (preview):** {h or '—'}")
            elif t == "support":
                lead = (it.get("lead") or "").strip().split("\n")[0][:100]
                lines.append(f"- **Lead (preview):** {lead or '—'}")
            lines.append("")
        out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return PublishHandoffResult(
        week_start=ws,
        week_end=we,
        out_json=out_json,
        out_md=out_md,
        items=items,
        state=state,
    )


def print_handoff_summary(result: PublishHandoffResult) -> None:
    print()
    print("Venus weekly — publish handoff")
    print(f"  Week:            {result.week_start} -> {result.week_end}")
    print(f"  Approved state:  {result.state.get('status')}")
    print(f"  Items extracted: {', '.join(i.get('type', '?') for i in result.items)}")
    print(f"  JSON written:    {result.out_json}")
    if result.out_md:
        print(f"  Summary MD:      {result.out_md}")
    print()
