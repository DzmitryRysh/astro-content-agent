from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import BrandProfile
from astro_content_agent.repositories.content_plans import ContentPlanRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.schemas.strategy import DayPlanPayload
from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.services.astro.signals import AstroSignalService
from astro_content_agent.services.content.caption_service import CaptionService
from astro_content_agent.services.content.reel_script_service import ReelScriptService
from astro_content_agent.services.strategy.planner import StrategyPlannerService

logger = logging.getLogger(__name__)


def run_daily_generation(
    *,
    db_factory: Callable[[], Session],
    runner: ResponsesRunner,
    day: date | None = None,
) -> dict[str, int]:
    """Generate astro signals, day plan, and initial drafts for all brand profiles.

    Idempotent: skips brands that already have a content plan for `day`.
    Skips individual draft slots that already have a draft linked to the plan.

    Args:
        db_factory: Callable returning a new SQLAlchemy Session.
        runner: ResponsesRunner for AI calls (injectable fake for tests).
        day: Target date; defaults to today.

    Returns:
        Counts dict: brands_processed, plans_created, plans_skipped, drafts_created, errors.
    """
    target_day = day or date.today()
    counts: dict[str, int] = {
        "brands_processed": 0,
        "plans_created": 0,
        "plans_skipped": 0,
        "drafts_created": 0,
        "errors": 0,
    }

    db = db_factory()
    try:
        brand_profiles = db.execute(select(BrandProfile)).scalars().all()
        logger.info("daily_generation: processing %d brand(s) for day=%s", len(brand_profiles), target_day)

        plan_repo = ContentPlanRepository()
        draft_repo = DraftRepository()
        astro_svc = AstroSignalService()
        planner = StrategyPlannerService(runner=runner)
        caption_svc = CaptionService(runner=runner)
        reel_svc = ReelScriptService(runner=runner)

        for brand in brand_profiles:
            counts["brands_processed"] += 1
            try:
                _process_brand(
                    db=db,
                    brand=brand,
                    target_day=target_day,
                    plan_repo=plan_repo,
                    draft_repo=draft_repo,
                    astro_svc=astro_svc,
                    planner=planner,
                    caption_svc=caption_svc,
                    reel_svc=reel_svc,
                    counts=counts,
                )
            except Exception:
                counts["errors"] += 1
                logger.exception("daily_generation: error for brand=%s", brand.id)
    finally:
        db.close()

    logger.info("daily_generation: done counts=%s", counts)
    return counts


def _process_brand(
    *,
    db: Session,
    brand: BrandProfile,
    target_day: date,
    plan_repo: ContentPlanRepository,
    draft_repo: DraftRepository,
    astro_svc: AstroSignalService,
    planner: StrategyPlannerService,
    caption_svc: CaptionService,
    reel_svc: ReelScriptService,
    counts: dict[str, int],
) -> None:
    # Ensure astro signals exist
    astro_svc.get_or_calculate_today(
        db=db,
        brand_profile_id=brand.id,
        day=target_day,
        generate_if_missing=True,
    )

    # Check for existing plan (idempotency)
    existing_plan = plan_repo.get_by_day(
        db,
        brand_profile_id=brand.id,
        day_yyyy_mm_dd=target_day.isoformat(),
    )
    if existing_plan is not None:
        logger.debug("daily_generation: plan already exists for brand=%s day=%s — skipping", brand.id, target_day)
        counts["plans_skipped"] += 1
        return

    # Generate day plan
    plan = planner.generate_day_plan(
        db=db,
        brand_profile_id=brand.id,
        day=target_day,
        generate_astro_if_missing=True,
    )
    counts["plans_created"] += 1
    logger.info("daily_generation: plan created brand=%s plan=%s", brand.id, plan.id)

    # Generate drafts for each plan slot — skip if drafts already exist for this plan
    existing_drafts = draft_repo.list_for_content_plan(db, plan.id)
    if existing_drafts:
        logger.debug("daily_generation: drafts already exist for plan=%s — skipping draft creation", plan.id)
        return

    plan_payload = DayPlanPayload.model_validate(plan.payload)
    for item in plan_payload.items:
        try:
            if item.format == "post":
                caption_svc.generate_post_draft(
                    db=db,
                    brand_profile_id=brand.id,
                    day=target_day,
                    content_plan=plan,
                    plan_slot=item.slot,
                )
                counts["drafts_created"] += 1
            elif item.format == "reel":
                reel_svc.generate_reel_draft(
                    db=db,
                    brand_profile_id=brand.id,
                    day=target_day,
                    content_plan=plan,
                    plan_slot=item.slot,
                )
                counts["drafts_created"] += 1
        except Exception:
            counts["errors"] += 1
            logger.exception("daily_generation: draft error for brand=%s slot=%s", brand.id, item.slot)
