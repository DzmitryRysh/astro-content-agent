from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from astro_content_agent.db.session import get_db
from astro_content_agent.schemas.strategy import (
    StrategyGenerateDayPlanRequest,
    StrategyGenerateDayPlanResponse,
)
from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.services.strategy.planner import StrategyPlannerService

router = APIRouter()


def get_runner() -> ResponsesRunner:
    return ResponsesRunner.from_settings()


@router.post("/generate-day-plan", response_model=StrategyGenerateDayPlanResponse)
def generate_day_plan(
    req: StrategyGenerateDayPlanRequest,
    db: Session = Depends(get_db),
    runner: ResponsesRunner = Depends(get_runner),
) -> StrategyGenerateDayPlanResponse:
    svc = StrategyPlannerService(runner=runner)
    try:
        plan = svc.generate_day_plan(
            db=db,
            brand_profile_id=req.brand_profile_id,
            day=req.day,
            generate_astro_if_missing=req.generate_astro_if_missing,
        )
    except StrategyPlannerService.BrandProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except StrategyPlannerService.AstroSignalsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return StrategyGenerateDayPlanResponse(
        content_plan_id=plan.id,
        brand_profile_id=plan.brand_profile_id,
        day=req.day,
        payload=plan.payload,
        meta={"astro_signal_id": plan.astro_signal_id},
    )

