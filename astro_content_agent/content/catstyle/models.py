"""Catstyle v0 data models (prompt layer only; no image generation)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PlanetCatProfile(BaseModel):
    planet_name: str
    visual_identity: str
    colors: str
    facial_expression_style: str
    signature_props: str
    emotional_role: str
    stressed_expression: str
    constructive_expression: str


class AspectCatInteraction(BaseModel):
    planet_a: str
    planet_b: str
    core_tension: str
    constructive_channel: str
    scene_ideas: list[str] = Field(min_length=4, max_length=4)
    compensation_scene_ideas: list[str] = Field(min_length=2, max_length=2)
    avoid_list: list[str]


class CatstylePromptRequest(BaseModel):
    planet_a: str
    planet_b: str
    aspect_type: str
    mode: Literal["tension", "compensation", "mixed"]
    variants_count: int = Field(default=4, ge=1, le=8)
    skin_a: str | None = Field(
        default=None,
        description="Optional character skin key for planet_a (v0: Mars, Jupiter, Saturn skins only).",
    )
    skin_b: str | None = Field(
        default=None,
        description="Optional character skin key for planet_b (v0: Mars, Jupiter, Saturn skins only).",
    )


class CatstylePromptPack(BaseModel):
    image_prompts: list[str]
    animation_prompt: str
    negative_prompt: str
    carousel_idea: str


class CatstyleCandidate(BaseModel):
    """Ranked Catstyle visual candidate (deep library, transit seed, or fallback)."""

    planet_a: str
    planet_b: str
    aspect_type: str
    mode_recommendation: Literal["tension", "compensation", "mixed"]
    visual_score: int = Field(ge=1, le=10)
    emotional_score: int = Field(ge=1, le=10)
    comedy_score: int = Field(ge=1, le=10)
    clarity_score: int = Field(ge=1, le=10)
    total_score: int = Field(ge=4, le=80)
    reason: str
    recommended_scene_angle: str
    orb: float | None = None
    orb_bonus: int = Field(default=0, ge=0, le=10)
    source: Literal["deep", "seed", "fallback"] = "deep"
    # Full-day window scan (v1); unset for noon-only / manual candidates
    closest_hour_utc: int | None = None
    window_first_seen_hour_utc: int | None = None
    window_last_seen_hour_utc: int | None = None
    window_samples_seen: int | None = None
    is_moon_aspect: bool = False


class CatstyleUnsupportedCandidate(BaseModel):
    """Input row that cannot be ranked (unknown planets or not outer-to-personal transit)."""

    planet_a: str
    planet_b: str
    aspect_type: str
    reason: str


class CatstyleCandidateRankingResult(BaseModel):
    ranked: list[CatstyleCandidate]
    unsupported: list[CatstyleUnsupportedCandidate] = Field(default_factory=list)


class CatstyleDailyPackResult(BaseModel):
    """Daily Catstyle scan + top prompt packs (text only)."""

    date: str
    scan_mode: str
    step_hours: int | None = None
    editorial_profile: Literal["charged", "balanced", "supportive"] = "charged"
    ranked_candidates_count: int
    selected_count: int
    ranked_candidates: list[dict] = Field(
        default_factory=list,
        description="Intrinsic rank_catstyle_candidates order (total_score + aspect/orb v1).",
    )
    selected_candidates: list[dict]
    prompt_packs: list[dict]
    primary_candidate: dict | None = None
    secondary_supportive_candidate: dict | None = None
