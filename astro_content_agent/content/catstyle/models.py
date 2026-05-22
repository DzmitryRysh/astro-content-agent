"""Catstyle v0 data models (prompt layer only; no image generation)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PlanetCatProfile(BaseModel):
    planet_name: str
    visual_identity: str
    colors: str
    facial_expression_style: str
    signature_props: str
    emotional_role: str
    stressed_expression: str
    constructive_expression: str


class PlanetIdentityMarkerProfile(BaseModel):
    """Deterministic symbol/prop placement cues so each planet-cat stays recognizable (markers v1)."""

    planet_name: str
    planet_symbol: str = Field(description="Glyph or compact symbol cue (flat icon, not readable words).")
    symbol_name: str = Field(description="Spelled-out name for prompts.")
    primary_marker: str
    secondary_marker: str
    signature_prop: str
    placement_rules: list[str] = Field(default_factory=list)
    must_show_markers: list[str] = Field(default_factory=list)
    optional_label_ideas: list[str] = Field(default_factory=list)
    visual_read_rule: str
    avoid_marker_mistakes: list[str] = Field(default_factory=list)
    short_prompt_line: str


class PlanetCatCanon(BaseModel):
    """Immutable core visual identity for a round planet-cat (Catstyle canon v1 — prompt layer)."""

    planet_name: str
    role_archetype: str
    silhouette_notes: str
    core_shape_language: str
    core_palette: str
    facial_expression_language: str
    body_language: str
    signature_props: str
    signature_details: str
    emotional_tone: str
    motion_style: str
    visual_do: str
    visual_avoid: str
    recognizability_rule: str
    short_prompt_line: str


class AspectCatInteraction(BaseModel):
    planet_a: str
    planet_b: str
    core_tension: str
    constructive_channel: str
    scene_ideas: list[str] = Field(min_length=4, max_length=4)
    compensation_scene_ideas: list[str] = Field(min_length=2, max_length=2)
    avoid_list: list[str]


CatstyleTemplateEnergy = Literal["charged", "supportive", "balanced"]


class CatstyleWorldTemplate(BaseModel):
    """Shared universe shell for Catstyle aspect scenes (world templates v1)."""

    template_key: str
    display_name: str
    description: str
    environment_type: str
    energy_default: CatstyleTemplateEnergy
    setting_line: str
    composition_line: str
    horizon_line: str
    floor_line: str
    background_line: str
    lighting_line: str
    zodiac_ring_line: str
    interaction_read_charged: str
    interaction_read_supportive: str
    interaction_read_balanced: str
    optional_variants: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    short_prompt_line: str


class CatstyleRenderStyleProfile(BaseModel):
    """Deterministic render finish / illustration quality targets (render style profiles v1)."""

    key: str
    label: str
    description: str
    image_prompt_opening_line: str = Field(
        ...,
        description="First visual instruction for image prompts; must lead render priority before canon/world/scene.",
    )
    style_core_line: str
    composition_line: str
    linework_line: str
    shading_line: str
    lighting_line: str
    environment_line: str
    detail_line: str
    color_line: str
    facial_expression_line: str
    must_have_lines: list[str] = Field(default_factory=list, min_length=1)
    avoid_lines: list[str] = Field(default_factory=list, min_length=1)
    negative_prompt_additions: list[str] = Field(default_factory=list, min_length=1)
    short_prompt_line: str
    style_hardlock_block: str | None = Field(
        default=None,
        description="Optional high-priority mandate paragraph injected after opening (e.g. premium_comic_poster_v2).",
    )


class CatstyleSceneTemplate(BaseModel):
    """Deterministic hero beat / camera frame layered on world + canon (scene templates v1)."""

    template_key: str
    display_name: str
    compatible_planets: list[str] = Field(
        default_factory=list,
        description="If non-empty, every listed planet must appear in the pair (unordered).",
    )
    compatible_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="If non-empty, planet pair must match one tuple (either order).",
    )
    compatible_aspects: list[str] | None = Field(
        default=None,
        description="If set, aspect_type must match one entry (case-insensitive). None = any aspect.",
    )
    compatible_skins: list[str] | None = Field(
        default=None,
        description="If set, boosts rank when any applied skin matches (normalized keys). None = skin optional.",
    )
    energy: CatstyleTemplateEnergy
    primary_action: str
    composition: str
    camera_angle: str
    foreground_elements: str
    background_elements: str
    emotional_read: str
    required_markers: list[str] = Field(default_factory=list)
    optional_props: list[str] = Field(default_factory=list)
    text_overlay_ideas: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    short_prompt_line: str


class CatstylePromptRequest(BaseModel):
    planet_a: str
    planet_b: str
    aspect_type: str
    mode: Literal["tension", "compensation", "mixed", "flow"]
    variants_count: int = Field(default=2, ge=1, le=8)
    skin_a: str | None = Field(
        default=None,
        description="Optional character skin key for planet_a (v0: Mars, Jupiter, Saturn skins only).",
    )
    skin_b: str | None = Field(
        default=None,
        description="Optional character skin key for planet_b (v0: Mars, Jupiter, Saturn skins only).",
    )
    editorial_profile: Literal["charged", "balanced", "supportive"] | None = Field(
        default=None,
        description="Optional editorial lens for deterministic premium art-direction (daily pack sets this).",
    )
    premium_art_direction: bool = Field(
        default=True,
        description="When True, append deterministic premium comic-direction blocks (no LLM).",
    )
    world_template_key: str | None = Field(
        default=None,
        description="Explicit world template (defaults to cosmic arena when premium_art_direction is True).",
    )
    scene_template_key: str | None = Field(
        default=None,
        description="Optional scene beat template (identity markers and canon still apply).",
    )
    render_style_profile_key: str = Field(
        default="premium_comic_poster_v2",
        description=(
            "Catstyle render finish profile key (empty string resolves to DEFAULT_RENDER_STYLE_PROFILE_KEY in generator). "
            "Default v2 is strongest premium battle-poster hardlock; use premium_comic_poster_v1 for legacy parity."
        ),
    )
    shot_mode: Literal["hero_pair", "standard", "epic_arena_showdown"] = Field(
        default="hero_pair",
        description=(
            "hero_pair: deterministic hero_poster / alternate_action_angle framing when variants_count>=1; "
            "epic_arena_showdown: same role cadence plus explicit wide arena spectacle composition guidance."
        ),
    )
    mars_heavy_style_reference_finisher: bool = Field(
        default=False,
        description=(
            "When True with a non-Mars pair, inject prompt guard: Mars-heavy reference anchors illustration finish only—"
            "do not copy Mars combat choreography onto these planet-cats (Catstyle v1)."
        ),
    )
    disable_approved_reference_prompt_lock: bool = Field(
        default=False,
        description=(
            "When True, skip [APPROVED CATSTYLE REFERENCE LOCK] prompt blocks even if an approved registry entry exists. "
            "Typically aligned with disable_approved_reference_auto on image job builds."
        ),
    )


class CatstylePromptPack(BaseModel):
    image_prompts: list[str]
    animation_prompt: str
    negative_prompt: str
    carousel_idea: str
    art_direction_profile: dict | None = Field(
        default=None,
        description="Metadata from catstyle_art_direction v0 when premium enrichment applied.",
    )
    world_template_profile: dict | None = Field(
        default=None,
        description="Serialized CatstyleWorldTemplate when a world shell was applied.",
    )
    scene_template_profile: dict | None = Field(
        default=None,
        description="Serialized CatstyleSceneTemplate when a scene beat was applied.",
    )
    render_style_profile: dict | None = Field(
        default=None,
        description="Serialized CatstyleRenderStyleProfile applied to image prompts and negative prompt.",
    )
    image_prompt_shot_roles: list[str | None] = Field(
        default_factory=list,
        description="Parallel shot_role labels (hero_poster / alternate_action_angle) per image_prompt index.",
    )

    @model_validator(mode="after")
    def _shot_roles_align_with_prompts(self) -> CatstylePromptPack:
        if self.image_prompt_shot_roles and len(self.image_prompt_shot_roles) != len(self.image_prompts):
            raise ValueError("image_prompt_shot_roles length must match image_prompts when non-empty.")
        return self


class CatstyleCandidate(BaseModel):
    """Ranked Catstyle visual candidate (deep library, transit seed, or fallback)."""

    planet_a: str
    planet_b: str
    aspect_type: str
    mode_recommendation: Literal["tension", "compensation", "mixed", "flow"]
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


CatstyleAspectTimingPhase = Literal["applying", "exact", "separating", "unknown"]

CatstyleAspectTimingStatus = Literal[
    "sky_window_utc",
    "orb_only_estimate",
    "missing_exact_window",
    "estimated",
]


class CatstyleAspectTimingMetadata(BaseModel):
    """UTC timing slice for Catstyle posts, derived from manifest scan fields only."""

    timing_status: CatstyleAspectTimingStatus
    window_start_utc: str | None = None
    peak_at_utc: str | None = None
    exact_at_utc: str | None = Field(
        default=None,
        description="Same instant as peak_at_utc when peak comes from closest_hour_utc in scan data.",
    )
    window_end_utc: str | None = None
    orb_at_post_date: float | None = None
    phase: CatstyleAspectTimingPhase = "unknown"
    timezone_note: str = Field(default="UTC", description="All instants are UTC unless a downstream channel localizes.")
    sky_scan_mode: str | None = None
    sky_scan_step_hours_utc: int | None = None
    data_source: str = Field(
        default="manifest_selected_candidate_v1",
        description=(
            "Provenance: manifest_selected_candidate_v1 | manual_override_with_timing_v1 | "
            "manual_override_no_sky_match_v1 | manifest_manual_override_v1."
        ),
    )
