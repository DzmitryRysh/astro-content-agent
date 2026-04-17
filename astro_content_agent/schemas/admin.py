from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Brand profile
# ---------------------------------------------------------------------------


class BrandProfileCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    tone_preset: str | None = None
    banned_terms: list[str] = Field(default_factory=list)
    default_hashtags: list[str] = Field(default_factory=list)
    face_led_preferred: bool = Field(
        default=False,
        description="If true, the planner will prefer face-led / talking-head content angles.",
    )
    content_language: str = Field(
        default="ru",
        description="Primary language for generated content. 'ru' = Russian (default), 'en' = English.",
    )


class BrandProfileResponse(BaseModel):
    id: str
    name: str
    description: str | None
    tone_preset: str | None
    banned_terms: list[str]
    default_hashtags: list[str]
    face_led_preferred: bool
    content_language: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, bp: Any) -> "BrandProfileResponse":
        return cls(
            id=bp.id,
            name=bp.name,
            description=bp.description,
            tone_preset=bp.tone_preset,
            banned_terms=bp.banned_terms or [],
            default_hashtags=bp.default_hashtags or [],
            face_led_preferred=bool(getattr(bp, "face_led_preferred", False)),
            content_language=getattr(bp, "content_language", "ru") or "ru",
            created_at=bp.created_at,
            updated_at=bp.updated_at,
        )


class BrandProfileListResponse(BaseModel):
    items: list[BrandProfileResponse]
    total: int


# ---------------------------------------------------------------------------
# Content pillars
# ---------------------------------------------------------------------------


class ContentPillarCreateRequest(BaseModel):
    brand_profile_id: str
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ContentPillarsBulkCreateRequest(BaseModel):
    brand_profile_id: str
    pillars: list[ContentPillarCreateRequest]
    reset: bool = Field(
        default=False,
        description="If true, delete existing pillars for this brand before creating.",
    )


class ContentPillarResponse(BaseModel):
    id: str
    brand_profile_id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, cp: Any) -> "ContentPillarResponse":
        return cls(
            id=cp.id,
            brand_profile_id=cp.brand_profile_id,
            name=cp.name,
            description=cp.description,
            created_at=cp.created_at,
            updated_at=cp.updated_at,
        )


class ContentPillarListResponse(BaseModel):
    items: list[ContentPillarResponse]
    total: int
