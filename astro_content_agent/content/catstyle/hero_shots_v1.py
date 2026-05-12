"""Deterministic premium hero image shot roles (paired poster frames)."""
from __future__ import annotations

from typing import Literal

SHOT_ROLE_HERO_POSTER = "hero_poster"
SHOT_ROLE_ALTERNATE_ACTION_ANGLE = "alternate_action_angle"

HeroShotMode = Literal["hero_pair", "standard", "epic_arena_showdown"]


def shot_roles_for_variant_indices(count: int, shot_mode: str) -> list[str | None]:
    """Return parallel shot_role labels (or None) for each image prompt index."""
    mode = (shot_mode or "hero_pair").strip().lower()
    if mode == "standard":
        return [None] * max(0, int(count))
    if mode not in {"hero_pair", "epic_arena_showdown"}:
        raise ValueError(
            f"Unknown shot_mode {shot_mode!r}. Use 'hero_pair', 'epic_arena_showdown', or 'standard'."
        )
    n = max(0, int(count))
    roles: list[str | None] = []
    for i in range(n):
        roles.append(SHOT_ROLE_HERO_POSTER if i % 2 == 0 else SHOT_ROLE_ALTERNATE_ACTION_ANGLE)
    return roles


def format_hero_shot_prompt_block(shot_role: str | None, *, flow_mode: bool = False) -> str:
    """High-priority framing cue inserted before Scene beat (deterministic v1)."""
    if shot_role is None:
        return ""
    if shot_role == SHOT_ROLE_HERO_POSTER:
        return (
            "[SHOT ROLE v1 - premium hero framing] hero_poster: "
            "Primary collectible comic-cover framing - iconic poster-balanced composition with the strongest combined "
            "silhouette read for both planet-cats; decisive focal hierarchy sized like a printed splash cover with "
            "foreground emphasis (reject symmetric mascot-sticker dead centers)."
        )
    if shot_role == SHOT_ROLE_ALTERNATE_ACTION_ANGLE:
        if flow_mode:
            return (
                "[SHOT ROLE v1 - premium hero framing] alternate_action_angle: "
                "Alternate premium cinematic staging—diagonal discovery plane or gentle heroic tilt with overlapping "
                "foreground bodies co-facing a shared objective (atlas/portal/horizon band) compared to the hero_poster frame; "
                "same identities and locked scene/world beats, distinct camera grammar and depth layering—avoid "
                "squared-off adversarial stance or confrontational combat symmetry."
            )
        return (
            "[SHOT ROLE v1 - premium hero framing] alternate_action_angle: "
            "Alternate premium cinematic staging - diagonal kinetic plane or lower heroic tilt / sidewinder tension "
            "with overlapping foreground bodies versus the hero_poster frame; same identities and locked scene/world "
            "beats, distinct camera grammar and depth layering."
        )
    raise ValueError(f"Unknown shot_role {shot_role!r}.")


__all__ = [
    "SHOT_ROLE_ALTERNATE_ACTION_ANGLE",
    "SHOT_ROLE_HERO_POSTER",
    "HeroShotMode",
    "format_hero_shot_prompt_block",
    "shot_roles_for_variant_indices",
]
