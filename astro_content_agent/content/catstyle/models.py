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


class CatstylePromptPack(BaseModel):
    image_prompts: list[str]
    animation_prompt: str
    negative_prompt: str
    carousel_idea: str
