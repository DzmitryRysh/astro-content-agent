from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.models import ContentPlan
from astro_content_agent.db.session import get_db
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.schemas.assets import AssetResponse
from astro_content_agent.schemas.drafts import (
    DraftApproveResponse,
    DraftDetail,
    DraftGeneratePostRequest,
    DraftGeneratePostResponse,
    DraftGenerateReelRequest,
    DraftGenerateReelResponse,
    DraftListResponse,
    DraftRejectRequest,
    DraftRejectResponse,
    DraftRegenerateRequest,
    DraftSummary,
    PostDraftPayload,
    ReelDraftPayload,
)
from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.services.content.caption_service import CaptionService
from astro_content_agent.services.content.reel_script_service import ReelScriptService
from astro_content_agent.services.drafts.approval import DraftApprovalService
from astro_content_agent.services.image.image_service import ImageGenerationService
from astro_content_agent.services.media.storage import LocalFileStorage
from astro_content_agent.services.media.url_builder import get_local_storage

router = APIRouter()


def get_runner() -> ResponsesRunner:
    return ResponsesRunner.from_settings()


def get_storage() -> LocalFileStorage:
    """FastAPI dependency: returns a LocalFileStorage configured from app settings."""
    return get_local_storage(get_settings())


# ---------------------------------------------------------------------------
# Phase 3: generation endpoints
# ---------------------------------------------------------------------------


@router.post("/generate-post", response_model=DraftGeneratePostResponse)
def generate_post(
    req: DraftGeneratePostRequest,
    db: Session = Depends(get_db),
    runner: ResponsesRunner = Depends(get_runner),
) -> DraftGeneratePostResponse:
    content_plan = db.get(ContentPlan, req.content_plan_id) if req.content_plan_id else None
    svc = CaptionService(runner=runner)
    try:
        draft = svc.generate_post_draft(
            db=db,
            brand_profile_id=req.brand_profile_id,
            day=req.day,
            content_plan=content_plan,
            plan_slot=req.plan_slot,
        )
    except CaptionService.BrandProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    payload = PostDraftPayload.model_validate(draft.payload or {})
    return DraftGeneratePostResponse(draft_id=draft.id, brand_profile_id=draft.brand_profile_id, day=req.day, payload=payload)


@router.post("/generate-reel", response_model=DraftGenerateReelResponse)
def generate_reel(
    req: DraftGenerateReelRequest,
    db: Session = Depends(get_db),
    runner: ResponsesRunner = Depends(get_runner),
) -> DraftGenerateReelResponse:
    content_plan = db.get(ContentPlan, req.content_plan_id) if req.content_plan_id else None
    svc = ReelScriptService(runner=runner)
    try:
        draft = svc.generate_reel_draft(
            db=db,
            brand_profile_id=req.brand_profile_id,
            day=req.day,
            content_plan=content_plan,
            plan_slot=req.plan_slot,
        )
    except ReelScriptService.BrandProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    payload = ReelDraftPayload.model_validate(draft.payload or {})
    return DraftGenerateReelResponse(draft_id=draft.id, brand_profile_id=draft.brand_profile_id, day=req.day, payload=payload)


# ---------------------------------------------------------------------------
# Phase 4: list / detail
# ---------------------------------------------------------------------------


@router.get("", response_model=DraftListResponse)
def list_drafts(
    brand_profile_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    draft_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> DraftListResponse:
    repo = DraftRepository()
    items = repo.list_drafts(
        db,
        brand_profile_id=brand_profile_id,
        status=status,
        draft_type=draft_type,
        limit=limit,
        offset=offset,
    )
    return DraftListResponse(
        items=[DraftSummary.from_orm_model(d) for d in items],
        total=len(items),
    )


@router.get("/{draft_id}", response_model=DraftDetail)
def get_draft(draft_id: str, db: Session = Depends(get_db)) -> DraftDetail:
    repo = DraftRepository()
    draft = repo.get_by_id(db, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"draft not found: {draft_id}")
    return DraftDetail.from_orm_model(draft)


# ---------------------------------------------------------------------------
# Phase 4: approval flow
# ---------------------------------------------------------------------------


@router.post("/{draft_id}/approve", response_model=DraftApproveResponse)
def approve_draft(draft_id: str, db: Session = Depends(get_db)) -> DraftApproveResponse:
    svc = DraftApprovalService()
    try:
        draft = svc.approve(db, draft_id)
    except DraftApprovalService.DraftNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DraftApprovalService.InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    return DraftApproveResponse(draft_id=draft.id, status=draft.status, approved_at=draft.approved_at)


@router.post("/{draft_id}/reject", response_model=DraftRejectResponse)
def reject_draft(
    draft_id: str,
    body: DraftRejectRequest,
    db: Session = Depends(get_db),
) -> DraftRejectResponse:
    svc = DraftApprovalService()
    try:
        draft = svc.reject(db, draft_id, reason=body.reason)
    except DraftApprovalService.DraftNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DraftApprovalService.InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    return DraftRejectResponse(
        draft_id=draft.id,
        status=draft.status,
        rejected_at=draft.rejected_at,
        rejection_reason=draft.rejection_reason,
    )


@router.post("/{draft_id}/regenerate", response_model=DraftDetail)
def regenerate_draft(
    draft_id: str,
    body: DraftRegenerateRequest,
    db: Session = Depends(get_db),
    runner: ResponsesRunner = Depends(get_runner),
) -> DraftDetail:
    repo = DraftRepository()
    original = repo.get_by_id(db, draft_id)
    if original is None:
        raise HTTPException(status_code=404, detail=f"draft not found: {draft_id}")

    content_plan = (
        db.get(ContentPlan, original.content_plan_id) if original.content_plan_id else None
    )

    if original.draft_type == "post":
        svc = CaptionService(runner=runner)
        try:
            new_draft = svc.generate_post_draft(
                db=db,
                brand_profile_id=original.brand_profile_id,
                day=body.day,
                content_plan=content_plan,
                plan_slot=body.plan_slot,
            )
        except CaptionService.BrandProfileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
    elif original.draft_type == "reel":
        reel_svc = ReelScriptService(runner=runner)
        try:
            new_draft = reel_svc.generate_reel_draft(
                db=db,
                brand_profile_id=original.brand_profile_id,
                day=body.day,
                content_plan=content_plan,
                plan_slot=body.plan_slot,
            )
        except ReelScriptService.BrandProfileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
    else:
        raise HTTPException(status_code=400, detail=f"regenerate not supported for draft_type '{original.draft_type}' in MVP")

    return DraftDetail.from_orm_model(new_draft)


# ---------------------------------------------------------------------------
# Phase 4/8: image generation
# ---------------------------------------------------------------------------


@router.post("/{draft_id}/generate-image", response_model=AssetResponse)
def generate_image(
    draft_id: str,
    db: Session = Depends(get_db),
    storage: LocalFileStorage = Depends(get_storage),
) -> AssetResponse:
    repo = DraftRepository()
    draft = repo.get_by_id(db, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"draft not found: {draft_id}")

    svc = ImageGenerationService()
    asset = svc.generate_placeholder(db=db, draft=draft, storage=storage)
    return AssetResponse.from_orm_model(asset, public_url=storage.url(asset.storage_path))
