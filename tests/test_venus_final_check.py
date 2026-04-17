"""Tests for Venus weekly final publish-readiness check."""
from __future__ import annotations

import json
from pathlib import Path

from astro_content_agent.services.content.venus_final_check import run_final_check


def _minimal_handoff(
    *,
    post_hook: str = "Hook line",
    post_body: str = "Body " * 50,
    post_cta: str = "Save post",
    reel_ok: bool = True,
    support: bool = False,
    forbidden: str | None = None,
) -> dict:
    post_body = (post_body + (forbidden or "")).strip()
    reel = {
        "type": "reel",
        "hook_0_3s": "Open",
        "spoken_hook": "Different hook",
        "script": "Script " * 20,
        "cta": "Save reel",
    }
    if not reel_ok:
        reel["script"] = ""
    items: list[dict] = [
        {
            "type": "post",
            "title": "T",
            "hook": post_hook,
            "body": post_body,
            "cta": post_cta,
            "hashtags": ["#a", "#b"],
        },
        reel,
    ]
    if support:
        items.append({"type": "support", "lead": "L", "body": "x" * 100, "cta": "c"})
    return {"version": 1, "items": items}


def test_final_check_passes(tmp_path: Path) -> None:
    ws = "2099-02-01"
    d = tmp_path
    state = {
        "week_start": ws,
        "week_end": "2099-02-07",
        "status": "approved",
        "package": {"compensation_focus": "уникальное слово compensation xyztestword"},
    }
    body = "word " * 30 + " xyztestword " + "more " * 30
    handoff = _minimal_handoff(post_body=body)
    (d / f"venus_weekly_state_{ws}.json").write_text(json.dumps(state), encoding="utf-8")
    (d / f"venus_publish_handoff_{ws}.json").write_text(json.dumps(handoff), encoding="utf-8")

    r = run_final_check(week_dir=d, week_start_hint=ws, write_markdown_summary=False)
    assert r.final_check_status == "pass"
    assert r.ready_for_publish is True
    assert (d / f"venus_final_check_{ws}.json").is_file()


def test_final_check_fails_not_approved(tmp_path: Path) -> None:
    ws = "2099-02-02"
    d = tmp_path
    (d / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-02-08", "status": "awaiting_approval"}),
        encoding="utf-8",
    )
    (d / f"venus_publish_handoff_{ws}.json").write_text(json.dumps(_minimal_handoff()), encoding="utf-8")
    r = run_final_check(week_dir=d, week_start_hint=ws, write_markdown_summary=False)
    assert r.final_check_status == "fail"
    assert not r.ready_for_publish
    assert any("approved" in i for i in r.issues)


def test_final_check_fails_empty_post_body(tmp_path: Path) -> None:
    ws = "2099-02-03"
    d = tmp_path
    state = {"week_start": ws, "week_end": "2099-02-09", "status": "approved"}
    h = _minimal_handoff(post_body="   ")
    (d / f"venus_weekly_state_{ws}.json").write_text(json.dumps(state), encoding="utf-8")
    (d / f"venus_publish_handoff_{ws}.json").write_text(json.dumps(h), encoding="utf-8")
    r = run_final_check(week_dir=d, week_start_hint=ws, write_markdown_summary=False)
    assert r.final_check_status == "fail"
    assert any("post.body" in i for i in r.issues)


def test_final_check_forbidden_phrase(tmp_path: Path) -> None:
    ws = "2099-02-04"
    d = tmp_path
    state = {"week_start": ws, "week_end": "2099-02-10", "status": "approved"}
    h = _minimal_handoff(forbidden=" money compass ")
    (d / f"venus_weekly_state_{ws}.json").write_text(json.dumps(state), encoding="utf-8")
    (d / f"venus_publish_handoff_{ws}.json").write_text(json.dumps(h), encoding="utf-8")
    r = run_final_check(week_dir=d, week_start_hint=ws, write_markdown_summary=False)
    assert r.final_check_status == "fail"
    assert any("forbidden" in i.lower() for i in r.issues)


def test_final_check_missing_handoff(tmp_path: Path) -> None:
    ws = "2099-02-05"
    d = tmp_path
    (d / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-02-11", "status": "approved"}),
        encoding="utf-8",
    )
    r = run_final_check(week_dir=d, week_start_hint=ws, write_markdown_summary=False)
    assert r.final_check_status == "fail"
    assert any("handoff" in i.lower() for i in r.issues)
