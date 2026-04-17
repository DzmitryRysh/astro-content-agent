from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.services.content.caption_service import CaptionService
from astro_content_agent.services.content.reel_script_service import ReelScriptService
from astro_content_agent.services.strategy.planner import StrategyPlannerService
from astro_content_agent.tests.fakes.fake_openai import FakeOpenAIClient, default_responder


def _runner() -> ResponsesRunner:
    prompts_root = Path(__file__).resolve().parents[1] / "services" / "ai" / "prompts"
    return ResponsesRunner(model="test", client=FakeOpenAIClient(default_responder), prompts_root=prompts_root)


def test_strategy_planner_persists_content_plan(db_session: Session, brand_profile) -> None:
    runner = _runner()
    svc = StrategyPlannerService(runner=runner)
    plan = svc.generate_day_plan(db=db_session, brand_profile_id=brand_profile.id, day=date(2026, 4, 3), generate_astro_if_missing=True)

    assert plan.brand_profile_id == brand_profile.id
    assert plan.plan_date == "2026-04-03"
    assert "items" in plan.payload
    assert len(plan.payload["items"]) >= 2


def test_caption_service_creates_post_draft(db_session: Session, brand_profile) -> None:
    runner = _runner()
    planner = StrategyPlannerService(runner=runner)
    plan = planner.generate_day_plan(db=db_session, brand_profile_id=brand_profile.id, day=date(2026, 4, 3), generate_astro_if_missing=True)

    svc = CaptionService(runner=runner)
    draft = svc.generate_post_draft(
        db=db_session,
        brand_profile_id=brand_profile.id,
        day=date(2026, 4, 3),
        content_plan=plan,
        plan_slot=1,
    )

    assert draft.draft_type == "post"
    assert draft.status == "draft"
    assert isinstance(draft.payload, dict)
    assert draft.payload["hook"]


def test_reel_script_service_creates_reel_draft(db_session: Session, brand_profile) -> None:
    runner = _runner()
    planner = StrategyPlannerService(runner=runner)
    plan = planner.generate_day_plan(db=db_session, brand_profile_id=brand_profile.id, day=date(2026, 4, 3), generate_astro_if_missing=True)

    svc = ReelScriptService(runner=runner)
    draft = svc.generate_reel_draft(
        db=db_session,
        brand_profile_id=brand_profile.id,
        day=date(2026, 4, 3),
        content_plan=plan,
        plan_slot=2,
    )

    assert draft.draft_type == "reel"
    assert draft.status == "draft"
    assert isinstance(draft.payload, dict)
    assert draft.payload["script"]

