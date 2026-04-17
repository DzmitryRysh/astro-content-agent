from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from astro_content_agent.astro.engine import AstroEngineV0, AstroEngineV1, EngineInput
from astro_content_agent.db.models import AstroSignal
from astro_content_agent.repositories.astro_signals import AstroSignalRepository
from astro_content_agent.repositories.brand_profiles import BrandProfileRepository


@dataclass(frozen=True)
class _Deps:
    engine: AstroEngineV0 | AstroEngineV1
    astro_repo: AstroSignalRepository
    brand_repo: BrandProfileRepository


class AstroSignalService:
    """Service for daily transit signal generation and persistence."""

    class BrandProfileNotFoundError(ValueError):
        pass

    class AstroSignalsNotFoundError(ValueError):
        pass

    def __init__(self, deps: _Deps | None = None) -> None:
        self._deps = deps or _Deps(
            engine=AstroEngineV1(),
            astro_repo=AstroSignalRepository(),
            brand_repo=BrandProfileRepository(),
        )

    def calculate_and_store(self, *, db: Session, brand_profile_id: str, day: date) -> AstroSignal:
        brand = self._deps.brand_repo.get(db, brand_profile_id)
        if brand is None:
            raise self.BrandProfileNotFoundError(f"brand_profile not found: {brand_profile_id}")

        payload_model = self._deps.engine.generate_day(EngineInput(brand_profile_id=brand_profile_id, day=day))
        payload = payload_model.model_dump(mode="json")

        rec = self._deps.astro_repo.upsert(
            db,
            brand_profile_id=brand_profile_id,
            day_yyyy_mm_dd=day.isoformat(),
            engine_version=payload_model.engine_version,
            payload=payload,
        )
        db.commit()
        db.refresh(rec)
        return rec

    def get_or_calculate_today(
        self,
        *,
        db: Session,
        brand_profile_id: str,
        day: date | None,
        generate_if_missing: bool,
    ) -> AstroSignal:
        brand = self._deps.brand_repo.get(db, brand_profile_id)
        if brand is None:
            raise self.BrandProfileNotFoundError(f"brand_profile not found: {brand_profile_id}")

        use_day = day or datetime.now().date()
        existing = self._deps.astro_repo.get_by_day(db, brand_profile_id=brand_profile_id, day_yyyy_mm_dd=use_day.isoformat())
        if existing is not None:
            return existing

        if not generate_if_missing:
            raise self.AstroSignalsNotFoundError(f"astro_signals not found for day={use_day.isoformat()}")

        return self.calculate_and_store(db=db, brand_profile_id=brand_profile_id, day=use_day)

