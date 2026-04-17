"""Lightweight publish-readiness check for approved Venus weekly handoff (no Instagram API).

Reads ``venus_weekly_state_*.json`` + ``venus_publish_handoff_*.json``. Gate: ``status == approved``.
Does not replace human approval or editorial review.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_FORBIDDEN_SUBSTRINGS = (
    "money compass",
    "moneycompass",
    "2-й дом",
    "10-й дом",
    "натальный дом",
    "natal house",
    "ваш асцендент",
    "ваш 2 дом",
    "ваш 10 дом",
    "по вашему гороскопу",
)

_PLACEHOLDER_SNIPPETS = (
    "[insert",
    "[todo",
    "todo:",
    "tbd",
    "заглушка",
    "lorem ipsum",
)

_MIN_HOOK_DUP_LEN = 24


@dataclass
class FinalCheckResult:
    week_start: str
    week_end: str
    final_check_status: str  # pass | fail
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_items: list[str] = field(default_factory=list)
    ready_for_publish: bool = False
    out_path: Path | None = None


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _collect_publish_text(handoff: dict[str, Any]) -> str:
    parts: list[str] = []
    for it in handoff.get("items") or []:
        if not isinstance(it, dict):
            continue
        for k in ("hook", "body", "cta", "hook_0_3s", "spoken_hook", "script", "lead"):
            v = it.get(k)
            if isinstance(v, str):
                parts.append(v)
        if isinstance(it.get("hashtags"), list):
            parts.append(" ".join(str(h) for h in it["hashtags"]))
    return "\n".join(parts).lower()


def _forbidden_hits(text: str) -> list[str]:
    hits: list[str] = []
    t = text.lower()
    for ph in _FORBIDDEN_SUBSTRINGS:
        if ph.lower() in t:
            hits.append(ph)
    return hits


def _placeholder_hits(text: str) -> list[str]:
    hits: list[str] = []
    tl = text.lower()
    for ph in _PLACEHOLDER_SNIPPETS:
        if ph.lower() in tl:
            hits.append(ph)
    return hits


def _compensation_words(pkg: dict[str, Any] | None) -> list[str]:
    if not pkg or not isinstance(pkg, dict):
        return []
    cf = str(pkg.get("compensation_focus") or "").strip()
    if len(cf) < 12:
        return []
    words = re.findall(r"[а-яёa-z]{5,}", cf.lower())
    # de-dupe, cap
    out: list[str] = []
    for w in words:
        if w not in out and len(w) >= 5:
            out.append(w)
    return out[:12]


def _compensation_echoed(post_body: str, words: list[str]) -> bool:
    if not words:
        return True
    b = post_body.lower()
    return any(w in b for w in words)


def _find_items(handoff: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for it in handoff.get("items") or []:
        if isinstance(it, dict) and isinstance(it.get("type"), str):
            out[it["type"]] = it
    return out


def run_final_check(
    *,
    week_dir: Path,
    state_path: Path | None = None,
    handoff_path: Path | None = None,
    week_start_hint: str | None = None,
    write_markdown_summary: bool = True,
) -> FinalCheckResult:
    """Run checks; write ``venus_final_check_<week_start>.json`` into *week_dir*."""
    week_dir = Path(week_dir)
    if state_path is not None:
        sp = Path(state_path)
    else:
        hint = week_start_hint or week_dir.name
        exact = week_dir / f"venus_weekly_state_{hint}.json"
        if exact.is_file():
            sp = exact
        else:
            matches = sorted(week_dir.glob("venus_weekly_state_*.json"))
            if not matches:
                raise ValueError(f"No venus_weekly_state_*.json in {week_dir}")
            if len(matches) > 1:
                raise ValueError(
                    f"Multiple state files; pass state_path or week_start_hint: "
                    f"{', '.join(m.name for m in matches)}"
                )
            sp = matches[0]

    state = json.loads(sp.read_text(encoding="utf-8"))
    ws = str(state.get("week_start") or week_dir.name)
    we = str(state.get("week_end") or "")

    issues: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []

    checked.append("state_file_present")
    if str(state.get("status", "")) != "approved":
        issues.append(f"status must be 'approved', got {state.get('status')!r}")

    if handoff_path is not None:
        hp = Path(handoff_path)
    else:
        hp = week_dir / f"venus_publish_handoff_{ws}.json"

    checked.append("handoff_path_resolved")
    handoff_missing = not hp.is_file()
    if handoff_missing:
        issues.append(f"handoff file missing: {hp.name}")

    handoff: dict[str, Any] | None = None
    handoff_name = hp.name if not handoff_missing else None
    if not handoff_missing:
        handoff = json.loads(hp.read_text(encoding="utf-8"))
        checked.append("handoff_json_parsed")

    items: dict[str, dict[str, Any]] = {}
    if handoff is not None:
        items = _find_items(handoff)
        for t in ("post", "reel"):
            checked.append(f"item_type_{t}")
            if t not in items:
                issues.append(f"missing required item type: {t}")

        if "post" in items:
            p = items["post"]
            for field in ("hook", "body", "cta"):
                v = p.get(field)
                if not isinstance(v, str) or not v.strip():
                    issues.append(f"post.{field} empty or missing")
            tags = p.get("hashtags")
            if not isinstance(tags, list) or len(tags) == 0:
                issues.append("post.hashtags must be non-empty list")
            elif not all(isinstance(x, str) and x.strip() for x in tags):
                issues.append("post.hashtags contains empty entry")

        if "reel" in items:
            r = items["reel"]
            for field in ("hook_0_3s", "spoken_hook", "script", "cta"):
                v = r.get(field)
                if not isinstance(v, str) or not v.strip():
                    issues.append(f"reel.{field} empty or missing")

        if "support" in items:
            checked.append("item_type_support")
            s = items["support"]
            body = s.get("body")
            if not isinstance(body, str) or len(body.strip()) < 80:
                warnings.append("support.body short or empty (<80 chars meaningful threshold)")

        for it in handoff.get("items") or []:
            if isinstance(it, dict) and it.get("type") not in ("post", "reel", "support", None):
                issues.append(f"unknown item type: {it.get('type')!r}")

        combined = _collect_publish_text(handoff)
        for hit in _forbidden_hits(combined):
            issues.append(f"forbidden phrase in publish text: {hit!r}")

        for hit in _placeholder_hits(combined):
            warnings.append(f"possible placeholder in publish text: {hit!r}")

        post = items.get("post") or {}
        reel = items.get("reel") or {}
        ph = _norm(str(post.get("hook") or ""))
        sh = _norm(str(reel.get("spoken_hook") or ""))
        if ph and sh and ph == sh and len(ph) >= _MIN_HOOK_DUP_LEN:
            warnings.append("post.hook and reel.spoken_hook are identical (anti-repeat smell)")

        pkg = state.get("package") if isinstance(state.get("package"), dict) else None
        cw = _compensation_words(pkg)
        if cw:
            checked.append("compensation_echo_cheap_check")
            body = str(post.get("body") or "")
            if not _compensation_echoed(body, cw):
                warnings.append(
                    "post.body does not echo compensation_focus keywords "
                    "(cheap check; verify manually if warning is wrong)"
                )

    ready = len(issues) == 0
    status = "pass" if ready else "fail"

    result = FinalCheckResult(
        week_start=ws,
        week_end=we,
        final_check_status=status,
        issues=issues,
        warnings=warnings,
        checked_items=checked,
        ready_for_publish=ready,
    )
    _write_result(week_dir, ws, result, write_markdown_summary, handoff_path=handoff_name)
    return result


def _write_result(
    week_dir: Path,
    ws: str,
    result: FinalCheckResult,
    write_md: bool,
    *,
    handoff_path: str | None = None,
) -> None:
    out = week_dir / f"venus_final_check_{ws}.json"
    payload = {
        "version": 1,
        "week_start": result.week_start,
        "week_end": result.week_end,
        "final_check_status": result.final_check_status,
        "issues": result.issues,
        "warnings": result.warnings,
        "checked_items": result.checked_items,
        "ready_for_publish": result.ready_for_publish,
        "handoff_file": handoff_path,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result.out_path = out
    if write_md:
        md = week_dir / f"venus_final_check_{ws}.md"
        issue_lines = [f"- {i}" for i in result.issues] if result.issues else ["- _none_"]
        warn_lines = [f"- {w}" for w in result.warnings] if result.warnings else ["- _none_"]
        md.write_text(
            "\n".join(
                [
                    f"# Venus final check — {ws}",
                    "",
                    f"- **Status:** {result.final_check_status}",
                    f"- **Ready for publish:** {result.ready_for_publish}",
                    f"- **Issues:** {len(result.issues)}",
                    f"- **Warnings:** {len(result.warnings)}",
                    "",
                    "## Issues",
                    *issue_lines,
                    "",
                    "## Warnings",
                    *warn_lines,
                    "",
                ]
            ),
            encoding="utf-8",
        )


def print_final_check_summary(result: FinalCheckResult) -> None:
    print()
    print("Venus weekly — final check")
    print(f"  Week:               {result.week_start} -> {result.week_end}")
    print(f"  Pass/fail:          {result.final_check_status}")
    print(f"  Issue count:        {len(result.issues)}")
    print(f"  Warning count:      {len(result.warnings)}")
    print(f"  Ready for publish:  {'yes' if result.ready_for_publish else 'no'}")
    if result.out_path:
        print(f"  Result JSON:        {result.out_path}")
    print()
