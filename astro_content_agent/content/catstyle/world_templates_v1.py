"""Catstyle shared universe templates v1 (cosmic arena shell)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstyleWorldTemplate

DEFAULT_WORLD_TEMPLATE_KEY = "cosmic_zodiac_arena"

WORLD_TEMPLATES: dict[str, CatstyleWorldTemplate] = {
    "cosmic_zodiac_arena": CatstyleWorldTemplate(
        template_key="cosmic_zodiac_arena",
        display_name="Cosmic Zodiac Arena",
        description=(
            "Monumental cosmic coliseum shell: floating celestial battle arena disk with architectural zodiac ring "
            "integration—tournament battle-ground scale (not toy sandbox platform); mythic consequential framing "
            "without copying any franchise."
        ),
        environment_type="cosmic_arena_disc",
        energy_default="balanced",
        setting_line=(
            "Shared universe shell: a monumental COSMIC COLISEUM - floating celestial BATTLE ARENA disk in deep space "
            "(grand duel-ring energy, not playground sandbox); dramatic tilted perspective so rim and buttresses read "
            "epic; zodiac architecture integrated into the arena masonry lip."
        ),
        composition_line=(
            "Frame planet-cats as heroic duelists ON the arena disk—foreground bodies mass large with authoritative "
            "silhouettes; midground carries monumental curved coliseum rim + integrated zodiac band; background plunges "
            "into layered star/nebula void for mythic scale (abstract constellation sparks may suggest cosmic spectacle "
            "—never photoreal crowds)."
        ),
        horizon_line=(
            "Low cosmic horizon hugs monumental disk curvature—void plummets beyond rim glow into consequential depth; "
            "no earth-bound skyline unless optional cue explicitly asks for distant Earth disk far background."
        ),
        floor_line=(
            "Arena floor reads as one heroic battle-scar comic disk—subtle rings, gouges, or paving tiles OK as graphic "
            "reads; avoid hyper-real marble noise or toy playmat blandness."
        ),
        background_line=(
            "Background is a **rich cosmic vault**: layered starfield, **colorful Milky Way / galaxy band**, nebula dust "
            "and depth—premium poster sky (not photographic NASA clutter); optional distant Earth disk when framing needs it."
        ),
        lighting_line=(
            "Rim light picks silhouette edges; key light favors focal duel/cooperation; simple volumetric glow cones OK "
            "if cartoon-readable."
        ),
        zodiac_ring_line=(
            "Outer perimeter reads as architectural ZODIAC COLOSSEUM BAND—twelve bold constellation glyphs locked into "
            "arena masonry (flat comic icons, no readable words), torus integrated into coliseum lip like monumental ring "
            "crown."
        ),
        interaction_read_charged=(
            "Energy read: COSMIC COLOSSEUM SHOWDOWN—heroic kinetic duel climax framed like collectible battle-cover splash "
            "with monumental arena scale (original staging only)."
        ),
        interaction_read_supportive=(
            "Energy read: ALLIANCE / CO-CREATION / shared spotlight - same arena reads as collaboration stage, "
            "not war theater."
        ),
        interaction_read_balanced=(
            "Energy read: MODERATED STAGE / negotiated space - balanced comic tension with clear focal hierarchy."
        ),
        optional_variants=[
            "subtle aurora curtain behind monumental rim",
            "sparse floating rock shards far background suggesting cosmic siege debris",
            "simple energy ribbon linking both cats toward center disc focal point",
            "tiny Earth disk distant in void when framing calls for mortal-stakes gravitas",
            "colossal buttress silhouettes supporting outer rim for mythic architecture read",
        ],
        avoid=[
            "copying recognizable franchise arenas or logos",
            "readable spell text on ring",
            "photoreal stadium crowds",
            "busy HUD sci-fi clutter",
        ],
        short_prompt_line=(
            "Monumental cosmic zodiac coliseum—floating celestial battle disk + architectural perimeter glyph ring."
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
