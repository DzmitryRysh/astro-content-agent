"""Minimal reference-driven Catstyle prompts (catstyle_clean_refs_v1)."""
from __future__ import annotations
from typing import Final
from astro_content_agent.content.catstyle.catstyle_planet_reference_identity_lock_v1 import (
    NEPTUNE_PREMIUM_IDENTITY_NEGATIVE_EXTRAS,
    URANUS_FEATURE_NEGATIVE_EXTRAS,
    URANUS_REFERENCE_HARDLOCK_V2,
    pair_includes_uranus,
)
from astro_content_agent.content.catstyle.catstyle_clean_refs_arena_opulence_lock_v1 import (
    CLEAN_REFS_ARENA_OPULENCE_NEGATIVE_EXTRAS,
    CLEAN_REFS_ARENA_OPULENCE_PROMPT_BLOCKS,
)
from astro_content_agent.content.catstyle.catstyle_reference_material_fidelity_v1 import (
    REFERENCE_MATERIAL_FIDELITY_NEGATIVE_EXTRAS,
    build_reference_material_fidelity_block,
)
from astro_content_agent.content.catstyle.catstyle_square_conflict_law_v1 import (
    SQUARE_CONFLICT_LAW_NEGATIVE_EXTRAS,
    build_square_conflict_law_block,
    is_square_conflict_aspect,
)
from astro_content_agent.content.catstyle.catstyle_tense_aspect_choreography_v1 import is_tense_hard_aspect
from astro_content_agent.content.catstyle.catstyle_true_premium_cgi_render_hardlock_v1 import (
    CLEAN_REFS_TRUE_PREMIUM_CGI_RENDER_HARDLOCK_BLOCK,
    TRUE_PREMIUM_CGI_RENDER_NEGATIVE_EXTRAS,
)
from astro_content_agent.content.catstyle.zodiac_arena_floor_lock_v1 import (
    ZODIAC_FLOOR_SCALE_NEGATIVE_EXTRAS,
)
from astro_content_agent.content.catstyle.models import CatstylePromptPack, CatstylePromptRequest
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.render_style_profiles_v1 import (
    get_render_style_profile,
)
CATSTYLE_CLEAN_REFS_PROFILE_KEY: Final[str] = "catstyle_clean_refs_v1"
CLEAN_PROMPT_MAX_CHARS: Final[int] = 4500
CLEAN_REFERENCE_FIDELITY_PRIORITY_BLOCK: Final[str] = (
    "[REFERENCE FIDELITY PRIORITY v1] Approved refs mandatory—stay visually close; no free reinterpretation. "
    "Preserve silhouette, body material, costume, face shape, energy, lighting mood, environment identity from refs. "
    "Priority: Planet A identity → Planet B identity → arena environment/lighting/architecture → aspect choreography → style flavor."
)
CLEAN_REFERENCE_ROLES_BLOCK: Final[str] = (
    "[REFERENCE ROLES] Planet A ref = identity only. Planet B ref = identity only. "
    "No arena or full-scene image refs—colosseum from prompt text only. No archetype substitution."
)
CLEAN_REFERENCE_ROLES_WITH_ARENA_BLOCK: Final[str] = (
    "[REFERENCE ROLES] Planet A/B refs = identity only (silhouette, material, face, costume, aura). "
    "Arena ref = environment, lighting, floor scale, architecture only—never planet identities, poses, or colors. "
    "[BANNERS SAFETY LOCK v1] Prefer blank deep-blue banners over wrong glyphs. "
    "Planet refs must not flatten arena; arena ref must not alter planets."
)
CLEAN_ARENA_SCALE_BLOCK: Final[str] = (
    "[ARENA SCALE] Monumental cosmic zodiac colosseum; ≥3 arch tiers; depth; sky vault; torch-lit; "
    "environment dominant—not small room or shallow backdrop."
)
CLEAN_CAMERA_FRAMING_BLOCK: Final[str] = (
    "[CAMERA / FRAMING] Medium-wide to wide cinematic; full-body planet-cats; visible foreground floor and "
    "upper architecture; arena huge around fighters. Not close-up or character-dominant crop."
)
CLEAN_PREMIUM_CGI_BLOCK: Final[str] = (
    "[PREMIUM CGI] Premium cinematic CGI, high-end 3D key art, PBR, crisp specular, volumetric light, "
    "game-cinematic—not painterly, watercolor, matte painting, storybook."
)
CLEAN_CAMERA_CGI_ARENA_BLOCK: Final[str] = (
    "[CAMERA / FRAMING] Medium-wide cinematic; full-body planet-cats; arena architecture dominant."
)
CLEAN_MERCURY_NEPTUNE_ARENA_COMPACT: Final[str] = (
    "[Mercury vs Neptune contrast] Distinct palettes—not twin mage cats. Neptune equal/larger presence with oceanic weight. "
    "Strong central clash—Mercury signal vs Neptune tide/mist; match approved Mercury and Neptune refs only."
)
CLEAN_ZODIAC_FLOOR_HARDLOCK_V2: Final[str] = (
    "[ZODIAC FLOOR HARDLOCK v2] Only real zodiac glyphs—12 sectors Aries through Pisces; "
    "no fake runes, occult nonsense, or invented symbols. Monumental stone-integrated wheel larger than fighters—"
    "not a neat medallion, not a small magic disc; only ~35–65% visible—extends beyond frame; do not fit entire circle under characters."
)
# Backward-compatible aliases.
CLEAN_ZODIAC_FLOOR_BLOCK = CLEAN_ZODIAC_FLOOR_HARDLOCK_V2
CLEAN_ZODIAC_FLOOR_BLOCK_ARENA_LIT = CLEAN_ZODIAC_FLOOR_HARDLOCK_V2
CLEAN_ARENA_REFERENCE_HARDLOCK_V2: Final[str] = (
    "[ARENA REFERENCE HARDLOCK v2] Arena ref drives golden/amber coliseum identity only—see "
    "[ARENA OPULENCE HARDLOCK v1], [ARENA LIGHTING RICHNESS v1], and [ARENA SCALE DOMINANCE v3] for full arena fidelity."
)
# Alias retained for imports/tests that referenced the v1 lighting block name.
CLEAN_ARENA_LIGHTING_HARDLOCK_BLOCK = CLEAN_ARENA_REFERENCE_HARDLOCK_V2
CLEAN_ARENA_POOL_READABILITY_BLOCK = CLEAN_ARENA_REFERENCE_HARDLOCK_V2
CLEAN_BANNERS_SAFETY_BLOCK: Final[str] = (
    "[BANNERS SAFETY LOCK v1] Arena banners empty/blank/placeholder unless a correct glyph is guaranteed. "
    "Prefer plain deep-blue or dark banners with no symbol over wrong symbols. "
    "Do not invent fake or incorrect planetary glyphs on banners."
)
CLEAN_PLANET_PRESENCE_BALANCE_BLOCK: Final[str] = (
    "[PLANET SIZE / PRESENCE BALANCE v1] Both planet-cats equally important and visually competitive in tense aspects—"
    "do not shrink one fighter irrelevantly. Overwhelm via aura/energy pressure, not by making the other tiny."
)
CLEAN_ENVIRONMENT_BLOCKS_TEXT_ONLY: Final[tuple[str, ...]] = (
    CLEAN_ARENA_SCALE_BLOCK,
    CLEAN_CAMERA_FRAMING_BLOCK,
)
CLEAN_ARENA_LIGHTING_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "underexposed arena",
    "crushed black shadows",
    "shadow-swallowed coliseum",
    "unreadable arch tiers",
    "muddy dark background",
    "barely visible statues",
    "lost zodiac floor detail",
    "black flat architecture",
    "too dark arena",
    "low-visibility coliseum",
    "dim blue-black generic hall",
    "plain empty circular wall",
    "weak architecture",
)
CLEAN_ARENA_POOL_READABILITY_NEGATIVE_EXTRAS = CLEAN_ARENA_LIGHTING_NEGATIVE_EXTRAS
CLEAN_REFERENCE_FIDELITY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "generic blue cat",
    "neptune-like water mage uranus",
    "incorrect banners",
    "fake planetary glyphs on banners",
    "fake zodiac symbols",
    "tiny complete medallion floor",
    "dark muddy arena",
    "over-simplified cat anatomy",
    "generic fantasy costume drift",
    "painterly illustration dominance",
    "watercolor storybook softness",
    "hand-painted fantasy illustration",
)
CLEAN_SQUARE_ACTION_BLOCK: Final[str] = (
    "[SQUARE ACTION] No polite magical exchange or calm face-off. Visible central rupture/clash point—"
    "friction and distortion, not cooperation."
)
# Backward-compatible alias; clean refs use [SQUARE CONFLICT LAW v1] via build_square_conflict_law_block.
CLEAN_SQUARE_ACTION_MERCURY_NEPTUNE_EXTRA: Final[str] = (
    "Mercury signal beam bent, scrambled, or dissolved by Neptune tide/fog."
)
CLEAN_NEPTUNE_PREMIUM_BLOCK: Final[str] = (
    "[NEPTUNE PREMIUM IDENTITY HARDLOCK v2] Match approved Neptune ref: regal oceanic-cosmic PBR—not flat "
    "monochrome blue or water-elemental mascot."
)
CLEAN_NEPTUNE_SCALE_PRESENCE_BLOCK: Final[str] = (
    "[NEPTUNE SCALE / PRESENCE] Neptune not smaller than Mercury—equal/larger presence, oceanic aura, "
    "tall trident, deep weight. Mercury agile/precise; Neptune vast, heavy, mythic."
)
CLEAN_MERCURY_NEPTUNE_SCALE_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "tiny Neptune",
    "small secondary Neptune",
    "Neptune smaller than Mercury",
    "weak Neptune presence",
    "sidekick Neptune",
    "small blue cat",
)
MERCURY_NEPTUNE_CONTRAST_MARKER: Final[str] = "[Mercury vs Neptune contrast]"
MERCURY_NEPTUNE_CONTRAST_CORE: Final[str] = (
    "Not sibling blue-gray mage cats—distinct palette, silhouette, aura. "
    "Mercury: silver/blue signal messenger. Neptune: regal oceanic PBR, not flat blue elemental."
)
MERCURY_NEPTUNE_SQUARE_CONFLICT: Final[str] = (
    "Strong central clash. Mercury = signal, logic, precision—approved Mercury ref. Neptune = tide, mist, "
    "dissolution—not generic blue cat. Signal vs dissolving wave-force. No Mercury as Sun/Mars/fire. "
    "No Neptune as Uranus brute or blue water mascot."
)
MERCURY_NEPTUNE_SQUARE_CONFLICT_COMPACT: Final[str] = (
    "Strong central clash—Mercury signal vs Neptune tide/mist; no Sun/Mars Mercury, no Uranus or blue-mascot Neptune."
)
CLEAN_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    *CLEAN_REFERENCE_FIDELITY_NEGATIVE_EXTRAS,
    "mercury as orange solar fire cat",
    "mercury as sun or mars identity",
    "neptune as uranus electric lightning cat",
    "generic blue electric brute neptune",
    "sibling blue-gray mage cats",
    "matching blue palette on mercury and neptune",
    "fake runes instead of zodiac glyphs",
    "wrong zodiac sign order",
    "random runes on zodiac floor",
    "fake occult magic circle floor",
    "invented pseudo-zodiac floor signs",
    "entire zodiac wheel fitted neatly in frame",
    "decorative magic circle under characters feet",
    *ZODIAC_FLOOR_SCALE_NEGATIVE_EXTRAS,
    *NEPTUNE_PREMIUM_IDENTITY_NEGATIVE_EXTRAS,
    "polite magical exchange",
    "calm ceremonial face-off",
    "small centered magic circle",
    "floor medallion under feet",
    "wrong planet archetype substitution",
    "full-scene generated image as arena reference",
    "generic blue neptune cat",
    "small room arena",
    "shallow backdrop coliseum",
    "close-up character-dominant crop",
    "planet glyphs on arena reference banners",
    "characters copied from arena reference plate",
)
# Per-planet anti-confusion lines (reference-led; clean refs assume approved planet images attached).
_PLANET_IDENTITY_GUARDS: Final[dict[str, str]] = {
    "Mercury": (
        "Planet Mercury: match approved Mercury reference closely—silhouette, material, face, costume; "
        "do not turn Mercury into Sun, Mars, or orange fire identity."
    ),
    "Neptune": (
        "Planet Neptune: match approved Neptune reference closely—regal oceanic PBR; "
        "never flat monochrome blue fur or generic water-elemental cat."
    ),
    "Sun": "Planet Sun: match approved Sun reference closely; never generic orange tabby.",
    "Uranus": (
        "Planet Uranus: match approved Uranus reference closely; never generic blue cat or Neptune mist clone."
    ),
    "Mars": "Planet Mars: match approved Mars reference closely; never generic red tabby brawler.",
    "Venus": "Planet Venus: match approved Venus reference closely; never generic pink house cat.",
    "Saturn": "Planet Saturn: match approved Saturn reference closely; never Mars fire or generic dark boss cat.",
    "Moon": "Planet Moon: match approved Moon reference closely; never generic white plush pet cat.",
    "Jupiter": "Planet Jupiter: match approved Jupiter reference closely; never generic fat orange cat.",
    "Pluto": "Planet Pluto: match approved Pluto reference closely; never generic dark round villain blob.",
}
_PAIR_ASPECT_LINES: Final[dict[tuple[str, str, str], str]] = {
    (
        "Mercury",
        "Neptune",
        "square",
    ): (
        "Mercury square Neptune: signal/logic versus fog/dissolution—visible central rupture between "
        "Mercury glyph/signal and Neptune tide/mist."
    ),
    (
        "Neptune",
        "Mercury",
        "square",
    ): (
        "Neptune square Mercury: fog/dissolution versus signal/logic—visible central rupture between "
        "Neptune tide/mist and Mercury glyph/signal."
    ),
}
def is_catstyle_clean_refs_mode(
    render_style_profile_key: str | None,
    *,
    clean_refs_mode: bool = False,
) -> bool:
    if clean_refs_mode:
        return True
    key = (render_style_profile_key or "").strip().lower().replace("-", "_")
    return key == CATSTYLE_CLEAN_REFS_PROFILE_KEY
def _planet_identity_line(planet: str) -> str:
    name = normalize_planet_name(planet)
    return _PLANET_IDENTITY_GUARDS.get(
        name,
        f"Planet {name}: match approved {name} reference closely; do not substitute another planet archetype.",
    )
def build_clean_refs_planet_identity_block(planet_a: str, planet_b: str) -> str:
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    return f"[PLANET IDENTITY] {_planet_identity_line(pa)} {_planet_identity_line(pb)}"
def build_clean_refs_uranus_reference_block(planet_a: str, planet_b: str) -> str:
    """Approved Uranus reference fidelity (clean refs; planet refs assumed active)."""
    if not pair_includes_uranus(planet_a, planet_b):
        return ""
    return URANUS_REFERENCE_HARDLOCK_V2
def build_clean_refs_uranus_feature_block(planet_a: str, planet_b: str) -> str:
    """Backward-compatible alias for ``build_clean_refs_uranus_reference_block``."""
    return build_clean_refs_uranus_reference_block(planet_a, planet_b)
def _pair_includes_mercury_and_neptune(planet_a: str, planet_b: str) -> bool:
    pair = {normalize_planet_name(planet_a), normalize_planet_name(planet_b)}
    return pair == {"Mercury", "Neptune"}
def _pair_includes_neptune(planet_a: str, planet_b: str) -> bool:
    pair = {normalize_planet_name(planet_a), normalize_planet_name(planet_b)}
    return "Neptune" in pair
def build_clean_refs_neptune_premium_block(planet_a: str, planet_b: str) -> str:
    """Neptune premium CGI fidelity when Neptune is in the pair (clean refs assume planet refs active)."""
    if not _pair_includes_neptune(planet_a, planet_b):
        return ""
    if _pair_includes_mercury_and_neptune(planet_a, planet_b):
        return ""
    return CLEAN_NEPTUNE_PREMIUM_BLOCK
def build_clean_refs_mercury_neptune_scale_block(planet_a: str, planet_b: str) -> str:
    if not _pair_includes_mercury_and_neptune(planet_a, planet_b):
        return ""
    return CLEAN_NEPTUNE_SCALE_PRESENCE_BLOCK
def build_clean_refs_mercury_neptune_contrast_block(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    *,
    arena_reference_attached: bool = False,
    arena_lighting_active: bool | None = None,
) -> str:
    """Strong visual separation when Mercury and Neptune share a clean-ref frame."""
    arena_active = arena_reference_attached or bool(arena_lighting_active)
    if not _pair_includes_mercury_and_neptune(planet_a, planet_b):
        return ""
    asp = (aspect_type or "").strip().lower()
    if asp == "square":
        return (
            f"{MERCURY_NEPTUNE_CONTRAST_MARKER} {MERCURY_NEPTUNE_CONTRAST_CORE} "
            f"{MERCURY_NEPTUNE_SQUARE_CONFLICT_COMPACT}"
        )
    return (
        f"{MERCURY_NEPTUNE_CONTRAST_MARKER} {MERCURY_NEPTUNE_CONTRAST_CORE} "
        "Keep signal versus fog distinct—never twin mage cats."
    )
def build_clean_reference_roles_block(*, arena_environment_reference_attached: bool) -> str:
    if arena_environment_reference_attached:
        return CLEAN_REFERENCE_ROLES_WITH_ARENA_BLOCK
    return CLEAN_REFERENCE_ROLES_BLOCK
def _arena_reference_lighting_active(*, arena_environment_reference_attached: bool) -> bool:
    """Arena pool or explicit arena reference image attached in clean refs."""
    return arena_environment_reference_attached
def build_clean_refs_square_action_block(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str | None,
) -> str:
    """Square conflict law (clean refs)—replaces legacy [SQUARE ACTION] block."""
    return build_square_conflict_law_block(planet_a, planet_b, aspect_type, mode)
def build_clean_refs_aspect_block(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str | None,
) -> str:
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    asp = (aspect_type or "").strip().lower()
    if is_square_conflict_aspect(aspect_type, mode):
        return ""
    if _pair_includes_mercury_and_neptune(pa, pb) and asp == "square":
        return ""
    pair_key = (pa, pb, asp)
    if pair_key in _PAIR_ASPECT_LINES:
        return f"[ASPECT] {_PAIR_ASPECT_LINES[pair_key]}"
    if is_tense_hard_aspect(aspect_type, mode):
        if asp == "opposition":
            rel = (
                f"{pa} opposition {pb}: equal-force polarity duel—active clash between {pa} and {pb} forces only; "
                "describe relationship and action, not identity redesign."
            )
        else:
            rel = (
                f"{pa} square {pb}: angular clash between {pa} and {pb} forces—active conflict choreography only; "
                "describe relationship and action, not identity redesign."
            )
        return f"[ASPECT] {rel}"
    return (
        f"[ASPECT] {pa} {aspect_type} {pb}: express the relationship between {pa} and {pb} through pose and "
        f"interaction only—no planet identity substitution."
    )
def _banners_safety_block(*, arena_attached: bool) -> str:
    """Banner lock is merged into arena reference roles; not duplicated in the prompt stack."""
    return ""


def build_clean_refs_image_prompt(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str | None,
    *,
    arena_environment_reference_attached: bool = False,
    arena_pool_key: str | None = None,
) -> str:
    """Short reference-first prompt without legacy canon or hardlock stacks."""
    arena_attached = arena_environment_reference_attached
    mn_pair = _pair_includes_mercury_and_neptune(planet_a, planet_b)
    blocks: list[str] = [
        CLEAN_REFERENCE_FIDELITY_PRIORITY_BLOCK,
        build_clean_reference_roles_block(arena_environment_reference_attached=arena_attached),
        build_clean_refs_planet_identity_block(planet_a, planet_b),
        build_reference_material_fidelity_block(planet_a, planet_b),
        build_clean_refs_uranus_reference_block(planet_a, planet_b),
    ]
    if mn_pair and arena_attached:
        blocks.append(CLEAN_MERCURY_NEPTUNE_ARENA_COMPACT)
    else:
        blocks.extend(
            [
                build_clean_refs_mercury_neptune_contrast_block(
                    planet_a,
                    planet_b,
                    aspect_type,
                    arena_reference_attached=arena_attached,
                ),
                build_clean_refs_mercury_neptune_scale_block(planet_a, planet_b),
            ]
        )
    blocks.append(_banners_safety_block(arena_attached=arena_attached))
    blocks.append(CLEAN_ZODIAC_FLOOR_HARDLOCK_V2)
    blocks.extend(CLEAN_REFS_ARENA_OPULENCE_PROMPT_BLOCKS)
    if is_tense_hard_aspect(aspect_type, mode) and not mn_pair and not arena_attached:
        blocks.append(CLEAN_PLANET_PRESENCE_BALANCE_BLOCK)
    blocks.extend(
        [
            build_clean_refs_square_action_block(planet_a, planet_b, aspect_type, mode),
            build_clean_refs_aspect_block(planet_a, planet_b, aspect_type, mode),
        ]
    )
    blocks.append(CLEAN_REFS_TRUE_PREMIUM_CGI_RENDER_HARDLOCK_BLOCK)
    if not _pair_includes_mercury_and_neptune(planet_a, planet_b):
        blocks.append(build_clean_refs_neptune_premium_block(planet_a, planet_b))
    prompt = " ".join(b for b in blocks if b).strip()
    if len(prompt) > CLEAN_PROMPT_MAX_CHARS:
        raise ValueError(
            f"Clean refs prompt exceeded {CLEAN_PROMPT_MAX_CHARS} chars ({len(prompt)}); shorten blocks."
        )
    return prompt
def generate_catstyle_clean_refs_prompt_pack(req: CatstylePromptRequest) -> CatstylePromptPack:
    """Build a minimal prompt pack: planet refs + textual colosseum/zodiac/quality locks only."""
    pa = normalize_planet_name(req.planet_a)
    pb = normalize_planet_name(req.planet_b)
    n = max(1, int(req.variants_count))
    arena_attached = bool(req.arena_environment_reference_attached)
    pool_key = (req.arena_pool_key or "").strip() or None
    image_prompts = [
        build_clean_refs_image_prompt(
            pa,
            pb,
            req.aspect_type,
            req.mode,
            arena_environment_reference_attached=arena_attached,
            arena_pool_key=pool_key,
        )
        for _ in range(n)
    ]
    prof = get_render_style_profile(CATSTYLE_CLEAN_REFS_PROFILE_KEY)
    neg_parts = list(prof.negative_prompt_additions) + list(CLEAN_NEGATIVE_EXTRAS)
    if _pair_includes_mercury_and_neptune(pa, pb):
        neg_parts.extend(CLEAN_MERCURY_NEPTUNE_SCALE_NEGATIVE_EXTRAS)
    if pair_includes_uranus(pa, pb):
        neg_parts.extend(URANUS_FEATURE_NEGATIVE_EXTRAS)
    neg_parts.extend(CLEAN_REFS_ARENA_OPULENCE_NEGATIVE_EXTRAS)
    if arena_attached:
        neg_parts.extend(CLEAN_ARENA_LIGHTING_NEGATIVE_EXTRAS)
    if is_square_conflict_aspect(req.aspect_type, req.mode):
        neg_parts.extend(SQUARE_CONFLICT_LAW_NEGATIVE_EXTRAS)
    neg_parts.extend(TRUE_PREMIUM_CGI_RENDER_NEGATIVE_EXTRAS)
    neg_parts.extend(REFERENCE_MATERIAL_FIDELITY_NEGATIVE_EXTRAS)
    negative_prompt = ", ".join(dict.fromkeys(neg_parts))
    anim = (
        f"Loopable 3–5s: {pa} and {pb} planet-cats, {req.aspect_type} aspect—preserve reference identities; "
        f"subtle combat motion only; premium cinematic CGI finish."
    )
    carousel = f"{pa} vs {pb} ({req.aspect_type}) — reference-locked planet-cats in cosmic coliseum."
    return CatstylePromptPack(
        image_prompts=image_prompts,
        animation_prompt=anim,
        negative_prompt=negative_prompt,
        carousel_idea=carousel,
        render_style_profile=prof.model_dump(mode="json"),
        image_prompt_shot_roles=[None] * len(image_prompts),
    )
__all__ = [
    "CATSTYLE_CLEAN_REFS_PROFILE_KEY",
    "CLEAN_ARENA_LIGHTING_HARDLOCK_BLOCK",
    "CLEAN_ARENA_LIGHTING_NEGATIVE_EXTRAS",
    "CLEAN_ARENA_POOL_READABILITY_BLOCK",
    "CLEAN_ARENA_POOL_READABILITY_NEGATIVE_EXTRAS",
    "CLEAN_ARENA_REFERENCE_HARDLOCK_V2",
    "CLEAN_ARENA_SCALE_BLOCK",
    "CLEAN_BANNERS_SAFETY_BLOCK",
    "CLEAN_CAMERA_FRAMING_BLOCK",
    "CLEAN_PLANET_PRESENCE_BALANCE_BLOCK",
    "CLEAN_REFERENCE_FIDELITY_PRIORITY_BLOCK",
    "CLEAN_REFERENCE_FIDELITY_NEGATIVE_EXTRAS",
    "CLEAN_PREMIUM_CGI_BLOCK",
    "CLEAN_ZODIAC_FLOOR_BLOCK",
    "CLEAN_ZODIAC_FLOOR_HARDLOCK_V2",
    "CLEAN_NEGATIVE_EXTRAS",
    "CLEAN_REFERENCE_ROLES_BLOCK",
    "CLEAN_REFERENCE_ROLES_WITH_ARENA_BLOCK",
    "build_clean_reference_roles_block",
    "CLEAN_PROMPT_MAX_CHARS",
    "CLEAN_NEPTUNE_SCALE_PRESENCE_BLOCK",
    "CLEAN_MERCURY_NEPTUNE_SCALE_NEGATIVE_EXTRAS",
    "MERCURY_NEPTUNE_CONTRAST_MARKER",
    "build_clean_refs_aspect_block",
    "build_clean_refs_square_action_block",
    "build_clean_refs_image_prompt",
    "build_clean_refs_mercury_neptune_scale_block",
    "build_clean_refs_mercury_neptune_contrast_block",
    "build_clean_refs_neptune_premium_block",
    "build_clean_refs_planet_identity_block",
    "build_clean_refs_uranus_feature_block",
    "build_clean_refs_uranus_reference_block",
    "build_reference_material_fidelity_block",
    "CLEAN_REFS_ARENA_OPULENCE_PROMPT_BLOCKS",
    "generate_catstyle_clean_refs_prompt_pack",
    "is_catstyle_clean_refs_mode",
]
