from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from astro_content_agent.db.models import BrandProfile, ContentPlan, Draft
from astro_content_agent.repositories.brand_profiles import BrandProfileRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.schemas.astro import AstroDayPayload
from astro_content_agent.schemas.drafts import PostDraftPayload
from astro_content_agent.schemas.strategy import DayPlanPayload, DayPlanItem
from astro_content_agent.services.ai.responses_runner import PromptRef, ResponsesRunner, prompt_ref_for_language
from astro_content_agent.services.astro.signals import AstroSignalService
from astro_content_agent.services.content.anti_repeat import AntiRepeatContext
from astro_content_agent.services.content.aspect_behavior_cards import AspectBehaviorCardsContext
from astro_content_agent.services.content.live_astrology_rules import LiveAstrologyContext
from astro_content_agent.services.content.money_astrology import MoneyAstrologyContext, MoneyKnowledgeBase
from astro_content_agent.services.content.persona import PersonaContext
from astro_content_agent.services.content.venus_aspect_overlay import VenusAspectOverlayContext
from astro_content_agent.services.content.venus_sign_climate import VenusSignClimateContext


@dataclass(frozen=True)
class _Deps:
    brand_repo: BrandProfileRepository
    drafts_repo: DraftRepository
    astro_signal_service: AstroSignalService


class CaptionService:
    """Generates and persists Instagram post drafts.

    Phase 10 enhancements:
    - Injects PersonaContext to drive tone/voice consistency.
    - Injects AntiRepeatContext to prevent repeated hooks/CTAs/angles.
    """

    class BrandProfileNotFoundError(ValueError):
        pass

    class ContentPlanMissingError(ValueError):
        pass

    def __init__(self, *, runner: ResponsesRunner, deps: _Deps | None = None) -> None:
        self._runner = runner
        self._deps = deps or _Deps(
            brand_repo=BrandProfileRepository(),
            drafts_repo=DraftRepository(),
            astro_signal_service=AstroSignalService(),
        )

    def generate_post_draft(
        self,
        *,
        db: Session,
        brand_profile_id: str,
        day: date,
        content_plan: ContentPlan | None,
        plan_slot: int | None,
    ) -> Draft:
        brand: BrandProfile | None = self._deps.brand_repo.get(db, brand_profile_id)
        if brand is None:
            raise self.BrandProfileNotFoundError(f"brand_profile not found: {brand_profile_id}")

        astro_rec = self._deps.astro_signal_service.get_or_calculate_today(
            db=db,
            brand_profile_id=brand_profile_id,
            day=day,
            generate_if_missing=True,
        )
        astro_day = AstroDayPayload.model_validate(astro_rec.payload)

        plan_item: DayPlanItem | None = None
        if content_plan is not None:
            plan_payload = DayPlanPayload.model_validate(content_plan.payload)
            if plan_slot is not None:
                plan_item = next((i for i in plan_payload.items if i.slot == plan_slot), None)
            plan_item = plan_item or (plan_payload.items[0] if plan_payload.items else None)

        language = getattr(brand, "content_language", "ru") or "ru"

        # Phase 10: persona + anti-repeat context (language-aware)
        persona = PersonaContext.from_brand(brand, language=language)
        anti_repeat = AntiRepeatContext.from_recent_drafts(db, brand_profile_id, limit=7)

        input_payload: dict[str, Any] = {
            "brand_profile": {
                "id": brand.id,
                "name": brand.name,
                "description": brand.description,
                "tone_preset": brand.tone_preset,
                "banned_terms": brand.banned_terms or [],
                "default_hashtags": brand.default_hashtags or [],
                "face_led_preferred": bool(getattr(brand, "face_led_preferred", False)),
                "content_language": language,
            },
            "astro_day": astro_day.model_dump(mode="json"),
            "plan_item": plan_item.model_dump(mode="json") if plan_item else None,
            "persona_context": persona.to_prompt_hint(),
            "anti_repeat_context": anti_repeat.to_prompt_hint(),
            "money_astrology_context": MoneyAstrologyContext.from_astro_day(astro_day).to_dict(),
            "money_knowledge_v2": MoneyKnowledgeBase.to_dict(),
            "live_astrology_context": LiveAstrologyContext.to_dict(),
            "aspect_behavior_cards_context": (_cards_ctx := AspectBehaviorCardsContext.from_astro_day(astro_day)).to_dict(),
            "venus_sign_climate_context": (_venus_ctx := VenusSignClimateContext.from_astro_day(astro_day)).to_dict(),
            "venus_aspect_overlay_context": VenusAspectOverlayContext.from_contexts(_venus_ctx, _cards_ctx).to_dict(),
        }

        payload = self._runner.run_json(
            db=db,
            prompt_ref=prompt_ref_for_language("copywriter", language),
            schema=PostDraftPayload,
            input_payload=input_payload,
            metadata={"kind": "draft_post", "day": day.isoformat(), "brand_profile_id": brand_profile_id},
        )

        rec = self._deps.drafts_repo.create(
            db,
            brand_profile_id=brand_profile_id,
            content_plan_id=content_plan.id if content_plan else None,
            draft_type="post",
            text=payload.caption,
            payload=payload.model_dump(mode="json"),
        )
        db.commit()
        db.refresh(rec)
        return rec
