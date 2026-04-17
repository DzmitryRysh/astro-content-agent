from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import ContentPlan


class ContentPlanRepository:
    def get_by_day(self, db: Session, *, brand_profile_id: str, day_yyyy_mm_dd: str) -> ContentPlan | None:
        stmt = select(ContentPlan).where(
            ContentPlan.brand_profile_id == brand_profile_id,
            ContentPlan.plan_date == day_yyyy_mm_dd,
        )
        return db.execute(stmt).scalars().first()

    def upsert(
        self,
        db: Session,
        *,
        brand_profile_id: str,
        day_yyyy_mm_dd: str,
        astro_signal_id: str | None,
        payload: dict,
    ) -> ContentPlan:
        existing = self.get_by_day(db, brand_profile_id=brand_profile_id, day_yyyy_mm_dd=day_yyyy_mm_dd)
        if existing is not None:
            existing.astro_signal_id = astro_signal_id
            existing.payload = payload
            db.add(existing)
            return existing

        rec = ContentPlan(
            brand_profile_id=brand_profile_id,
            plan_date=day_yyyy_mm_dd,
            astro_signal_id=astro_signal_id,
            payload=payload,
        )
        db.add(rec)
        return rec

