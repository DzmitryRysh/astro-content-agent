"""Catstyle shared universe templates v1 (cosmic arena shell)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstyleWorldTemplate

DEFAULT_WORLD_TEMPLATE_KEY = "cosmic_zodiac_arena"

WORLD_TEMPLATES: dict[str, CatstyleWorldTemplate] = {
    "cosmic_zodiac_arena": CatstyleWorldTemplate(
        template_key="cosmic_zodiac_arena",
        display_name="Cosmic Zodiac Arena",
        description=(
            "Original Catstyle cosmic duel-and-cooperation shell: disc arena floating in void with perimeter "
            "zodiac wheel read - tournament-ring vibe without copying any franchise."
        ),
        environment_type="cosmic_arena_disc",
        energy_default="balanced",
        setting_line=(
            "Shared universe shell: a stylized comic-fantasy COSMIC ARENA - circular battleground disc/platform "
            "floating in deep space, slight dramatic tilted perspective, readable outer rim."
        ),
        composition_line=(
            "Frame both planet-cats ON the arena disc with strong depth - foreground bodies crisp, midground disc edge "
            "readable, background opens into star nebula void."
        ),
        horizon_line=(
            "Low cosmic horizon follows disc curvature - void drops away beyond rim glow; no earth-bound skyline."
        ),
        floor_line=(
            "Arena floor reads as one continuous comic disc - subtle rings or paving tiles OK if flat graphic; "
            "avoid hyper-real marble noise."
        ),
        background_line=(
            "Background is cosmic void with layered stars, soft nebula milk, void gradients - premium comic poster sky "
            "not photographic NASA clutter."
        ),
        lighting_line=(
            "Rim light picks silhouette edges; key light favors focal duel/cooperation; simple volumetric glow cones OK "
            "if cartoon-readable."
        ),
        zodiac_ring_line=(
            "Outer perimeter carries a ZODIAC WHEEL band - twelve simplified constellation glyphs as flat icons "
            "(no readable words), repeating torus feel around arena lip."
        ),
        interaction_read_charged=(
            "Energy read: SHOWDOWN / DUEL / kinetic clash - arena frames conflict like an iconic tournament beat "
            "(original staging only)."
        ),
        interaction_read_supportive=(
            "Energy read: ALLIANCE / CO-CREATION / shared spotlight - same arena reads as collaboration stage, "
            "not war theater."
        ),
        interaction_read_balanced=(
            "Energy read: MODERATED STAGE / negotiated space - balanced comic tension with clear focal hierarchy."
        ),
        optional_variants=[
            "subtle aurora curtain behind rim",
            "sparse floating rock shards far background",
            "simple energy ribbon linking both cats toward center disc",
        ],
        avoid=[
            "copying recognizable franchise arenas or logos",
            "readable spell text on ring",
            "photoreal stadium crowds",
            "busy HUD sci-fi clutter",
        ],
        short_prompt_line=(
            "Cosmic zodiac arena - tilted disc duel stage in star void with perimeter glyph ring (flat comic icons)."
        ),
    ),
}


def normalize_world_template_key(raw: str) -> str:
    key = (raw or "").strip().lower().replace("-", "_")
    if key not in WORLD_TEMPLATES:
        known = ", ".join(sorted(WORLD_TEMPLATES))
        raise ValueError(f"Unknown Catstyle world template {raw!r}. Known keys: {known}.")
    return key


def get_world_template(template_key: str) -> CatstyleWorldTemplate:
    return WORLD_TEMPLATES[normalize_world_template_key(template_key)]


def list_world_templates() -> list[CatstyleWorldTemplate]:
    return [WORLD_TEMPLATES[k] for k in sorted(WORLD_TEMPLATES)]


def format_world_template_prompt_block(
    wt: CatstyleWorldTemplate,
    *,
    scene_energy: str,
) -> str:
    """High-priority shared-universe directions keyed off editorial/mode energy."""
    en = (scene_energy or "balanced").strip().lower()
    if en == "charged":
        interaction = wt.interaction_read_charged
    elif en == "supportive":
        interaction = wt.interaction_read_supportive
    else:
        interaction = wt.interaction_read_balanced
    optional = " | ".join(wt.optional_variants) if wt.optional_variants else "none"
    avoid = " | ".join(wt.avoid)
    return (
        f"[WORLD TEMPLATE v1 - high-priority setting direction] {wt.template_key} ({wt.display_name}): "
        f"{wt.setting_line} "
        f"{wt.composition_line} "
        f"Horizon: {wt.horizon_line} "
        f"Floor: {wt.floor_line} "
        f"Background: {wt.background_line} "
        f"Lighting: {wt.lighting_line} "
        f"Zodiac ring: {wt.zodiac_ring_line} "
        f"Interaction read for this pack: {interaction} "
        f"Optional variants: {optional}. "
        f"Avoid: {avoid}. "
        f"Compact cue: {wt.short_prompt_line}"
    )


__all__ = [
    "DEFAULT_WORLD_TEMPLATE_KEY",
    "WORLD_TEMPLATES",
    "format_world_template_prompt_block",
    "get_world_template",
    "list_world_templates",
    "normalize_world_template_key",
]
