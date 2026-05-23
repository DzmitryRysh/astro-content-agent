"""Unit tests for daily agent summary builder."""
from __future__ import annotations

import json

from astro_content_agent.services.content.catstyle_daily_agent import CatstyleDailyAgentResult
from astro_content_agent.services.content.catstyle_daily_agent_summary import (
    DailyAgentRunParams,
    build_daily_agent_summary_payload,
    write_daily_agent_summary,
)


def test_summary_payload_redacts_instagram_token_pattern() -> None:
    secret = "IGA" + ("X" * 35)
    result = CatstyleDailyAgentResult(
        exit_code=1,
        date="2099-01-01",
        status="publish_failed",
        errors=[f"failed with {secret}"],
    )
    payload = build_daily_agent_summary_payload(
        result,
        run_params=DailyAgentRunParams(
            provider="stub",
            render_style_profile="premium_comic_poster_v2",
            shot_mode="standard",
            scan_mode="noon",
            editorial_profile="charged",
            publish=True,
        ),
        publish_result=None,
    )
    blob = json.dumps(payload, ensure_ascii=False)
    assert secret not in blob
    assert "REDACTED" in blob
