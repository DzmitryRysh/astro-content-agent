from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


class DayPlanItem(BaseModel):
    slot: int = Field(ge=1, le=10)
    format: Literal["post", "reel"]
    primary_angle: str
    creative_brief: str
    signal_keys: list[str] = Field(default_factory=list)
    content_pillar: str | None = Field(
        default=None,
        description="The content pillar this slot belongs to (e.g. 'Education', 'Motivation').",
    )
    face_led_preference: bool | None = Field(
        default=None,
        description="True if this angle is best delivered as a talking-head / face-led format.",
    )


class DayPlanPayload(BaseModel):
    day: date
    items: list[DayPlanItem]
    notes: list[str] = Field(default_factory=list)


class StrategyGenerateDayPlanRequest(BaseModel):
    brand_profile_id: str
    day: date
    generate_astro_if_missing: bool = True


class StrategyGenerateDayPlanResponse(BaseModel):
    content_plan_id: str
    brand_profile_id: str
    day: date
    payload: DayPlanPayload
    meta: dict[str, Any] = Field(default_factory=dict)

