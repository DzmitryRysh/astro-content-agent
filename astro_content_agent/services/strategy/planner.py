from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from astro_content_agent.db.models import BrandProfile, ContentPlan
from astro_content_agent.repositories.brand_profiles import BrandProfileRepository
from astro_content_agent.repositories.content_pillars import ContentPillarRepository
from astro_content_agent.repositories.content_plans import ContentPlanRepository
from astro_content_agent.schemas.astro import AstroDayPayload
from astro_content_agent.schemas.strategy import DayPlanPayload
from astro_content_agent.services.ai.responses_runner import PromptRef, ResponsesRunner, prompt_ref_for_language
from astro_content_agent.services.astro.signals import AstroSignalService
from astro_content_agent.services.content.aspect_behavior_cards import AspectBehaviorCardsContext
from astro_content_agent.services.content.live_astrology_rules import LiveAstrologyContext
from astro_content_agent.services.content.money_astrology import MoneyAstrologyContext, MoneyKnowledgeBase
from astro_content_agent.services.content.pillar_balancer import ContentPillarBalancer
from astro_content_agent.services.content.venus_aspect_overlay import VenusAspectOverlayContext
from astro_content_agent.services.content.venus_sign_climate import VenusSignClimateContext


@dataclass(frozen=True)
class _Deps:
    brand_repo: BrandProfileRepository
    astro_signal_service: AstroSignalService
    plan_repo: ContentPlanRepository
    pillar_repo: ContentPillarRepository
    pillar_balancer: ContentPillarBalancer


class StrategyPlannerService:
    """Generates and persists daily content plans from astro signals + brand context.

    Phase 10 enhancements:
    - Injects content pillar usage history so the AI can balance pillars over time.
    - Passes face_led_preferred brand flag so the AI can tag face-led angles.
    """

    class BrandProfileNotFoundError(ValueError):
        pass

    class AstroSignalsNotFoundError(ValueError):
        pass

    def __init__(self, *, runner: ResponsesRunner, deps: _Deps | None = None) -> None:
        self._runner = runner
        self._deps = deps or _Deps(
            brand_repo=BrandProfileRepository(),
            astro_signal_service=AstroSignalService(),
            plan_repo=ContentPlanRepository(),
            pillar_repo=ContentPillarRepository(),
            pillar_balancer=ContentPillarBalancer(),
        )

    def generate_day_plan(
        self,
        *,
        db: Session,
        brand_profile_id: str,
        day: date,
        generate_astro_if_missing: bool,
    ) -> ContentPlan:
        brand: BrandProfile | None = self._deps.brand_repo.get(db, brand_profile_id)
        if brand is None:
            raise self.BrandProfileNotFoundError(f"brand_profile not found: {brand_profile_id}")

        astro_rec = self._deps.astro_signal_service.get_or_calculate_today(
            db=db,
            brand_profile_id=brand_profile_id,
            day=day,
            generate_if_missing=generate_astro_if_missing,
        )
        astro_day = AstroDayPayload.model_validate(astro_rec.payload)

        # Content pillar context
        pillars = self._deps.pillar_repo.list_for_brand(db, brand_profile_id)
        pillar_names = [p.name for p in pillars]
        recent_usage = self._deps.pillar_balancer.get_recent_pillar_usage(
            db, brand_profile_id, days=14
        )
        pillar_hint = self._deps.pillar_balancer.to_prompt_hint(recent_usage, pillar_names)

        face_led = bool(getattr(brand, "face_led_preferred", False))

        language = getattr(brand, "content_language", "ru") or "ru"

        input_payload: dict[str, Any] = {
            "day": day.isoformat(),
            "brand_profile": {
                "id": brand.id,
                "name": brand.name,
                "description": brand.description,
                "tone_preset": brand.tone_preset,
                "banned_terms": brand.banned_terms or [],
                "default_hashtags": brand.default_hashtags or [],
                "face_led_preferred": face_led,
                "content_language": language,
            },
            "astro_day": astro_day.model_dump(mode="json"),
            "content_pillars": pillar_names,
            "pillar_balance_hint": pillar_hint,
            "money_astrology_context": MoneyAstrologyContext.from_astro_day(astro_day).to_dict(),
            "money_knowledge_v2": MoneyKnowledgeBase.to_dict(),
            "live_astrology_context": LiveAstrologyContext.to_dict(),
            "aspect_behavior_cards_context": (_cards_ctx := AspectBehaviorCardsContext.from_astro_day(astro_day)).to_dict(),
            "venus_sign_climate_context": (_venus_ctx := VenusSignClimateContext.from_astro_day(astro_day)).to_dict(),
            "venus_aspect_overlay_context": VenusAspectOverlayContext.from_contexts(_venus_ctx, _cards_ctx).to_dict(),
        }

        plan_payload = self._runner.run_json(
            db=db,
            prompt_ref=prompt_ref_for_language("strategist", language),
            schema=DayPlanPayload,
            input_payload=input_payload,
            metadata={"kind": "strategy_plan", "day": day.isoformat(), "brand_profile_id": brand_profile_id},
        )

        rec = self._deps.plan_repo.upsert(
            db,
            brand_profile_id=brand_profile_id,
            day_yyyy_mm_dd=day.isoformat(),
            astro_signal_id=astro_rec.id,
            payload=plan_payload.model_dump(mode="json"),
        )
        db.commit()
        db.refresh(rec)
        return rec
