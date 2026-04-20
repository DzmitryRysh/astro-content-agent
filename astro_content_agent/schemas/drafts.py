from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from astro_content_agent.schemas.diagnostics import CheckResult, PublishSimulationPreview


# ---------------------------------------------------------------------------
# AI-output payload schemas (used as structured model outputs)
# ---------------------------------------------------------------------------


class PostDraftPayload(BaseModel):
    title: str
    hook: str
    caption: str
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    voice_note: str | None = Field(
        default=None,
        description="Optional tone/persona note from the model explaining the voice choices made.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReelDraftPayload(BaseModel):
    hook_0_3s: str = Field(
        description="The critical opening 0–3 second hook — must stop the scroll immediately.",
    )
    hook: str = Field(
        description="Full spoken hook line (may be longer than hook_0_3s).",
    )
    reel_type: Literal["talking_head", "text_overlay", "b_roll", "green_screen"]
    on_screen_text: list[str] = Field(default_factory=list)
    script: str
    cta: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Generation request / response (Phase 3)
# ---------------------------------------------------------------------------


class DraftGeneratePostRequest(BaseModel):
    brand_profile_id: str
    day: date
    content_plan_id: str | None = None
    plan_slot: int | None = None


class DraftGeneratePostResponse(BaseModel):
    draft_id: str
    brand_profile_id: str
    day: date
    payload: PostDraftPayload


class DraftGenerateReelRequest(BaseModel):
    brand_profile_id: str
    day: date
    content_plan_id: str | None = None
    plan_slot: int | None = None


class DraftGenerateReelResponse(BaseModel):
    draft_id: str
    brand_profile_id: str
    day: date
    payload: ReelDraftPayload


# ---------------------------------------------------------------------------
# Draft list / detail (Phase 4)
# ---------------------------------------------------------------------------


class DraftSummary(BaseModel):
    id: str
    brand_profile_id: str
    content_plan_id: str | None
    draft_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, rec: Any) -> "DraftSummary":
        return cls(
            id=rec.id,
            brand_profile_id=rec.brand_profile_id,
            content_plan_id=rec.content_plan_id,
            draft_type=rec.draft_type,
            status=rec.status,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
        )


class DraftDetail(DraftSummary):
    text: str | None
    payload: dict[str, Any] | None
    approved_at: datetime | None
    rejected_at: datetime | None
    rejection_reason: str | None

    @classmethod
    def from_orm_model(cls, rec: Any) -> "DraftDetail":  # type: ignore[override]
        return cls(
            id=rec.id,
            brand_profile_id=rec.brand_profile_id,
            content_plan_id=rec.content_plan_id,
            draft_type=rec.draft_type,
            status=rec.status,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            text=rec.text,
            payload=rec.payload,
            approved_at=rec.approved_at,
            rejected_at=rec.rejected_at,
            rejection_reason=rec.rejection_reason,
        )


class DraftListResponse(BaseModel):
    items: list[DraftSummary]
    total: int


# ---------------------------------------------------------------------------
# Approval / rejection / regeneration (Phase 4)
# ---------------------------------------------------------------------------


class DraftApproveResponse(BaseModel):
    draft_id: str
    status: str
    approved_at: datetime | None


class DraftRejectRequest(BaseModel):
    reason: str = Field(min_length=1)


class DraftRejectResponse(BaseModel):
    draft_id: str
    status: str
    rejected_at: datetime | None
    rejection_reason: str | None


class DraftRegenerateRequest(BaseModel):
    day: date
    plan_slot: int | None = None


# ---------------------------------------------------------------------------
# Operator review surface (single payload for review + readiness + dry-run)
# ---------------------------------------------------------------------------


class OperatorReviewActionLinks(BaseModel):
    """Resolved API paths for the current draft (substituted draft_id)."""

    approve: str
    reject: str
    publish_dry_run: str
    admin_publish_readiness: str


class DraftOperatorReview(BaseModel):
    """One-screen read model: copy for review, readiness, and dry-run preview."""

    draft_id: str
    brand_profile_id: str
    draft_type: str
    status: str
    title: str | None = None
    hook: str | None = None
    caption: str | None = None
    cta: str | None = None
    hashtags_preview: list[str] = Field(default_factory=list)
    text_fallback: str | None = Field(
        default=None,
        description="Raw draft.text when structured payload fields are missing.",
    )
    primary_asset_storage_key: str | None = None
    primary_image_public_url: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    publish_readiness_ready: bool
    publish_readiness_checks: list[CheckResult]
    dry_run: PublishSimulationPreview | None = None
    actions: OperatorReviewActionLinks
