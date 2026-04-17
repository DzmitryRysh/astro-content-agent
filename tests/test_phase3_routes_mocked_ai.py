from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.main import create_app
from astro_content_agent.db.session import get_db
from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.api.routes import strategy as strategy_routes
from astro_content_agent.api.routes import drafts as drafts_routes
from astro_content_agent.tests.fakes.fake_openai import FakeOpenAIClient, default_responder


@pytest.fixture()
def ai_runner() -> ResponsesRunner:
    prompts_root = Path(__file__).resolve().parents[1] / "services" / "ai" / "prompts"
    return ResponsesRunner(model="test", client=FakeOpenAIClient(default_responder), prompts_root=prompts_root)


@pytest.fixture()
def client_ai(db_session: Session, ai_runner: ResponsesRunner) -> TestClient:
    app = create_app()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[strategy_routes.get_runner] = lambda: ai_runner
    app.dependency_overrides[drafts_routes.get_runner] = lambda: ai_runner
    return TestClient(app)


def test_generate_day_plan_endpoint(client_ai: TestClient, brand_profile) -> None:
    resp = client_ai.post(
        "/api/v1/strategy/generate-day-plan",
        json={"brand_profile_id": brand_profile.id, "day": "2026-04-03"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["brand_profile_id"] == brand_profile.id
    assert body["day"] == "2026-04-03"
    assert len(body["payload"]["items"]) >= 2


def test_generate_post_and_reel_endpoints(client_ai: TestClient, brand_profile) -> None:
    # first generate a plan so we have a content_plan_id
    plan_resp = client_ai.post(
        "/api/v1/strategy/generate-day-plan",
        json={"brand_profile_id": brand_profile.id, "day": "2026-04-03"},
    )
    assert plan_resp.status_code == 200, plan_resp.text
    plan_id = plan_resp.json()["content_plan_id"]

    post_resp = client_ai.post(
        "/api/v1/drafts/generate-post",
        json={"brand_profile_id": brand_profile.id, "day": "2026-04-03", "content_plan_id": plan_id, "plan_slot": 1},
    )
    assert post_resp.status_code == 200, post_resp.text
    post_body = post_resp.json()
    assert post_body["payload"]["caption"]

    reel_resp = client_ai.post(
        "/api/v1/drafts/generate-reel",
        json={"brand_profile_id": brand_profile.id, "day": "2026-04-03", "content_plan_id": plan_id, "plan_slot": 2},
    )
    assert reel_resp.status_code == 200, reel_resp.text
    reel_body = reel_resp.json()
    assert reel_body["payload"]["script"]

