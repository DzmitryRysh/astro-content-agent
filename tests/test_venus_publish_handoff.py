"""Tests for approved weekly → publish handoff parsing."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astro_content_agent.services.content.venus_publish_handoff import (
    build_publish_handoff,
    parse_weekly_post_draft,
    parse_weekly_reel_draft,
    parse_weekly_support_draft,
)

SAMPLE_POST = """# Venus weekly — post draft

<!-- week: 2099-01-01 → 2099-01-07 -->

## Anti-repeat
none

## Adjustments
none

## Hook
Line one hook

## Caption
Para one.

Para two.

## CTA
Save this reel.

## Hashtags
- #one
- #two
"""

SAMPLE_REEL = """# Venus weekly — reel draft

## hook_0_3s
Open fast

## Spoken hook
Say this aloud

## Script
Beat one

Beat two

## CTA
Comment below.
"""

SAMPLE_SUPPORT = """# Venus weekly — support (stories / carousel note)

## Lead
Quick lead

## Body
Support body here.

## CTA
DM me.
"""


def test_parse_post() -> None:
    d = parse_weekly_post_draft(SAMPLE_POST)
    assert d["type"] == "post"
    assert d["hook"].startswith("Line one")
    assert "Para one" in d["body"]
    assert d["cta"] == "Save this reel."
    assert d["hashtags"] == ["#one", "#two"]
    assert "Line one" in d["title"]


def test_parse_reel() -> None:
    d = parse_weekly_reel_draft(SAMPLE_REEL)
    assert d["type"] == "reel"
    assert d["hook_0_3s"] == "Open fast"
    assert d["spoken_hook"] == "Say this aloud"
    assert "Beat one" in d["script"]


def test_parse_support() -> None:
    d = parse_weekly_support_draft(SAMPLE_SUPPORT)
    assert d["type"] == "support"
    assert d["lead"].startswith("Quick")
    assert "Support body" in d["body"]


def test_build_handoff_requires_approved(tmp_path: Path) -> None:
    ws = "2099-01-03"
    d = tmp_path
    (d / f"venus_weekly_state_{ws}.json").write_text(
        json.dumps({"week_start": ws, "week_end": "2099-01-09", "status": "awaiting_approval"}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="approved"):
        build_publish_handoff(week_dir=d, week_start_hint=ws)


def test_build_handoff_ok_with_support(tmp_path: Path) -> None:
    ws = "2099-01-01"
    state = {
        "version": 1,
        "week_start": ws,
        "week_end": "2099-01-07",
        "status": "approved",
        "approval_timestamp": "2099-01-02T12:00:00+00:00",
        "climate": {"venus_sign": "Taurus"},
        "overlay_active": False,
        "overlay_pair": None,
        "outputs": {
            "post_draft": f"venus_weekly_post_{ws}.md",
            "reel_draft": f"venus_weekly_reel_{ws}.md",
            "support_draft": f"venus_weekly_support_{ws}.md",
        },
    }
    d = tmp_path
    (d / f"venus_weekly_state_{ws}.json").write_text(json.dumps(state), encoding="utf-8")
    (d / f"venus_weekly_post_{ws}.md").write_text(SAMPLE_POST, encoding="utf-8")
    (d / f"venus_weekly_reel_{ws}.md").write_text(SAMPLE_REEL, encoding="utf-8")
    (d / f"venus_weekly_support_{ws}.md").write_text(SAMPLE_SUPPORT, encoding="utf-8")

    result = build_publish_handoff(week_dir=d, week_start_hint=ws, write_markdown_summary=True)
    assert result.out_json.is_file()
    assert result.out_md is not None and result.out_md.is_file()
    payload = json.loads(result.out_json.read_text(encoding="utf-8"))
    assert payload["status_snapshot"] == "approved"
    assert payload["approved_at"] == "2099-01-02T12:00:00+00:00"
    assert len(payload["items"]) == 3
    types = [i["type"] for i in payload["items"]]
    assert types == ["post", "reel", "support"]


def test_build_handoff_omits_support_when_missing(tmp_path: Path) -> None:
    ws = "2099-01-08"
    state = {
        "week_start": ws,
        "week_end": "2099-01-14",
        "status": "approved",
        "approval_timestamp": "2099-01-09T00:00:00+00:00",
        "climate": None,
        "overlay_active": True,
        "overlay_pair": "mars_venus",
        "outputs": {
            "post_draft": f"venus_weekly_post_{ws}.md",
            "reel_draft": f"venus_weekly_reel_{ws}.md",
        },
    }
    d = tmp_path
    (d / f"venus_weekly_state_{ws}.json").write_text(json.dumps(state), encoding="utf-8")
    (d / f"venus_weekly_post_{ws}.md").write_text(SAMPLE_POST.replace("2099-01-01", ws), encoding="utf-8")
    (d / f"venus_weekly_reel_{ws}.md").write_text(SAMPLE_REEL, encoding="utf-8")

    result = build_publish_handoff(week_dir=d, week_start_hint=ws, write_markdown_summary=False)
    payload = json.loads(result.out_json.read_text(encoding="utf-8"))
    assert len(payload["items"]) == 2
    assert payload["sources"]["support_draft"] is None
