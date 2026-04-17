from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import AstroSignal


class AstroSignalRepository:
    def get_by_day(self, db: Session, *, brand_profile_id: str, day_yyyy_mm_dd: str) -> AstroSignal | None:
        stmt = select(AstroSignal).where(
            AstroSignal.brand_profile_id == brand_profile_id,
            AstroSignal.signal_date == day_yyyy_mm_dd,
        )
        return db.execute(stmt).scalars().first()

    def upsert(
        self,
        db: Session,
        *,
        brand_profile_id: str,
        day_yyyy_mm_dd: str,
        engine_version: str,
        payload: dict,
    ) -> AstroSignal:
        existing = self.get_by_day(db, brand_profile_id=brand_profile_id, day_yyyy_mm_dd=day_yyyy_mm_dd)
        if existing is not None:
            existing.engine_version = engine_version
            existing.payload = payload
            db.add(existing)
            return existing

        rec = AstroSignal(
            brand_profile_id=brand_profile_id,
            signal_date=day_yyyy_mm_dd,
            engine_version=engine_version,
            payload=payload,
        )
        db.add(rec)
        return rec

