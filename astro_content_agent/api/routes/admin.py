from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from astro_content_agent.core.admin_guard import require_admin_key
from astro_content_agent.core.config import Settings, get_settings
from astro_content_agent.db.session import get_db
from astro_content_agent.repositories.brand_profiles import BrandProfileRepository
from astro_content_agent.repositories.content_pillars import ContentPillarRepository
from astro_content_agent.schemas.admin import (
    BrandProfileCreateRequest,
    BrandProfileListResponse,
    BrandProfileResponse,
    ContentPillarListResponse,
    ContentPillarResponse,
    ContentPillarsBulkCreateRequest,
)
from astro_content_agent.schemas.drafts import DraftOperatorReview
from astro_content_agent.schemas.diagnostics import DiagnosticsReport, PublishReadinessReport
from astro_content_agent.services.diagnostics.checker import DiagnosticsService
from astro_content_agent.services.drafts.review_surface import build_draft_operator_review

router = APIRouter(dependencies=[Depends(require_admin_key)])


# ---------------------------------------------------------------------------
# Brand profiles
# ---------------------------------------------------------------------------


@router.post("/brand-profile", response_model=BrandProfileResponse, status_code=201)
def create_brand_profile(
    body: BrandProfileCreateRequest,
    db: Session = Depends(get_db),
) -> BrandProfileResponse:
    repo = BrandProfileRepository()
    bp = repo.create(
        db,
        name=body.name,
        description=body.description,
        tone_preset=body.tone_preset,
        banned_terms=body.banned_terms,
        default_hashtags=body.default_hashtags,
        face_led_preferred=body.face_led_preferred,
        content_language=body.content_language,
    )
    db.commit()
    db.refresh(bp)
    return BrandProfileResponse.from_orm_model(bp)


@router.get("/brand-profile", response_model=BrandProfileListResponse)
def list_brand_profiles(db: Session = Depends(get_db)) -> BrandProfileListResponse:
    repo = BrandProfileRepository()
    items = repo.list_all(db)
    return BrandProfileListResponse(
        items=[BrandProfileResponse.from_orm_model(bp) for bp in items],
        total=len(items),
    )


@router.get("/brand-profile/{brand_profile_id}", response_model=BrandProfileResponse)
def get_brand_profile(brand_profile_id: str, db: Session = Depends(get_db)) -> BrandProfileResponse:
    repo = BrandProfileRepository()
    bp = repo.get(db, brand_profile_id)
    if bp is None:
        raise HTTPException(status_code=404, detail=f"brand_profile not found: {brand_profile_id}")
    return BrandProfileResponse.from_orm_model(bp)


# ---------------------------------------------------------------------------
# Content pillars
# ---------------------------------------------------------------------------


@router.post("/content-pillars", response_model=ContentPillarListResponse, status_code=201)
def create_content_pillars(
    body: ContentPillarsBulkCreateRequest,
    db: Session = Depends(get_db),
) -> ContentPillarListResponse:
    brand_repo = BrandProfileRepository()
    if brand_repo.get(db, body.brand_profile_id) is None:
        raise HTTPException(status_code=404, detail=f"brand_profile not found: {body.brand_profile_id}")

    pillar_repo = ContentPillarRepository()
    if body.reset:
        pillar_repo.delete_for_brand(db, body.brand_profile_id)

    created = []
    for p in body.pillars:
        cp = pillar_repo.create(
            db,
            brand_profile_id=body.brand_profile_id,
            name=p.name,
            description=p.description,
        )
        created.append(cp)

    db.commit()
    for cp in created:
        db.refresh(cp)

    return ContentPillarListResponse(
        items=[ContentPillarResponse.from_orm_model(cp) for cp in created],
        total=len(created),
    )


@router.get("/content-pillars", response_model=ContentPillarListResponse)
def list_content_pillars(
    brand_profile_id: str = Query(...),
    db: Session = Depends(get_db),
) -> ContentPillarListResponse:
    repo = ContentPillarRepository()
    items = repo.list_for_brand(db, brand_profile_id)
    return ContentPillarListResponse(
        items=[ContentPillarResponse.from_orm_model(cp) for cp in items],
        total=len(items),
    )


# ---------------------------------------------------------------------------
# Operator: draft review surface (content + readiness + dry-run preview)
# ---------------------------------------------------------------------------


@router.get("/drafts/{draft_id}/review", response_model=DraftOperatorReview)
def get_draft_operator_review(
    draft_id: str,
    instagram_account_id: str | None = Query(
        default=None,
        description="Optional Instagram account UUID — includes account checks and ig_user_id on dry-run preview.",
    ),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DraftOperatorReview:
    """Single payload for operators: hook/caption/CTA, asset URL, approval state, publish readiness, dry-run simulation.

    Approve or reject via ``POST /api/v1/drafts/{draft_id}/approve`` and ``.../reject`` (no change to those routes).
    """
    body = build_draft_operator_review(
        db,
        draft_id=draft_id,
        settings=settings,
        instagram_account_id=instagram_account_id,
    )
    if body is None:
        raise HTTPException(status_code=404, detail=f"draft not found: {draft_id}")
    return body


# ---------------------------------------------------------------------------
# Phase 9: diagnostics
# ---------------------------------------------------------------------------


@router.get("/diagnostics", response_model=DiagnosticsReport)
def get_diagnostics(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DiagnosticsReport:
    """Return a full runtime readiness report.

    Checks config, credentials, DB state, and asset URL generation.
    No writes or external network calls are performed.
    """
    svc = DiagnosticsService()
    return svc.run_config_checks(settings, db)


@router.get("/publish-readiness/{draft_id}", response_model=PublishReadinessReport)
def get_publish_readiness(
    draft_id: str,
    instagram_account_id: str | None = Query(
        default=None,
        description="When set, validates the Instagram account row (active, ig_user_id).",
    ),
    simulate: bool = Query(
        default=False,
        description="When true, includes image_url/caption preview (no Meta API calls).",
    ),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PublishReadinessReport:
    """Dry-run validation for a specific draft.

    Checks all preconditions for publishing without performing any publish attempt.
    """
    svc = DiagnosticsService()
    return svc.run_publish_readiness(
        db,
        draft_id=draft_id,
        settings=settings,
        instagram_account_id=instagram_account_id,
        include_simulation=simulate,
    )
