from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from astro_content_agent.db.session import get_db
from astro_content_agent.schemas.astro import (
    AstroCalculateDayRequest,
    AstroSignalRecordResponse,
)
from astro_content_agent.services.astro.signals import AstroSignalService

router = APIRouter()


@router.post("/calculate-day", response_model=AstroSignalRecordResponse)
def calculate_day(req: AstroCalculateDayRequest, db: Session = Depends(get_db)) -> AstroSignalRecordResponse:
    svc = AstroSignalService()
    try:
        rec = svc.calculate_and_store(db=db, brand_profile_id=req.brand_profile_id, day=req.day)
        return AstroSignalRecordResponse.from_orm_model(rec)
    except AstroSignalService.BrandProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/today", response_model=AstroSignalRecordResponse)
def get_today(
    brand_profile_id: str = Query(...),
    day: date | None = Query(default=None, description="Optional override; defaults to today (server-local)."),
    generate_if_missing: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> AstroSignalRecordResponse:
    svc = AstroSignalService()
    try:
        rec = svc.get_or_calculate_today(
            db=db,
            brand_profile_id=brand_profile_id,
            day=day,
            generate_if_missing=generate_if_missing,
        )
        return AstroSignalRecordResponse.from_orm_model(rec)
    except AstroSignalService.BrandProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except AstroSignalService.AstroSignalsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

