"""Universal tense-aspect (square / opposition) cinematic conflict choreography (v1)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.moon_saturn_square_tension_visual_canon_v1 import (
    is_moon_saturn_square_tension,
)
from astro_content_agent.content.catstyle.catstyle_square_conflict_law_v1 import (
    build_square_conflict_law_block,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

TENSE_HARD_ASPECTS: Final[frozenset[str]] = frozenset({"square", "opposition"})

TENSE_SQUARE_CHOREOGRAPHY_BLOCK: Final[str] = (
    "[TENSE ASPECT CHOREOGRAPHY v2 - square] Explosive angular clash: active collision, attack/block/counterattack, "
    "visible impact point, mid-battle split-second capture—one planet-cat attacks while the other blocks or "
    "counterattacks. Shockwave, sparks, debris, cracked zodiac floor, dust burst, distorted air ripples; dynamic "
    "diagonals, body momentum, and force trails—no static posing. Each planet expresses force through its own "
    "planetary physics, never generic MMA."
)

TENSE_OPPOSITION_CHOREOGRAPHY_BLOCK: Final[str] = (
    "[TENSE ASPECT CHOREOGRAPHY v2 - opposition] Equal-force duel: active polarity clash—not passive face-off. "
    "Central axis clash with beam/force/pressure collision, mirrored rivals, chain tension, space distortion, "
    "debris pushed outward across a clear central axis. Visible dangerous symmetry with pressure between poles—"
    "both lean into clash with reversible momentum."
)

TENSE_ANTI_STATIC_BLOCK: Final[str] = (
    "[TENSE ASPECT ANTI-STATIC v1] Mandatory: do NOT show characters simply standing and posing; do NOT show a calm "
    "ceremonial face-off. This must be active conflict—capture a split-second from combat already in progress. "
    "At least one character must lunge, strike, block, counterattack, or unleash force; include visible momentum in "
    "bodies, paws, tails, garments, and energy trails."
)

TENSE_PREMIUM_CG_STYLE_BLOCK: Final[str] = (
    "[TENSE ASPECT PREMIUM CG STYLE LOCK v1] Polished premium CG key art, 2.5D/3D hybrid game splash art, crisp "
    "digital finish, clean specular highlights, luminous material surfaces, volumetric cinematic lighting, strong "
    "readable silhouettes, sharp face design—not watercolor, not painterly brush texture, not matte gouache, not "
    "storybook illustration, not flat hand-painted look, not dusty soft illustration rendering. Explicitly reject: "
    "watercolor, painterly wash, soft brushed canvas, dry illustration texture, dry brush, matte painterly fantasy."
)

TENSE_BATTLE_ARENA_BALANCE_BLOCK: Final[str] = (
    "[TENSE ASPECT BATTLE-ARENA BALANCE v1] Prioritize active conflict, character action, planet identity, and aspect "
    "choreography—but the battle must happen inside a gigantic monumental coliseum that stays architecturally "
    "readable. Do not crop away arena scale, tiered arches, upper structure, or zodiac floor for a tight action close-up. "
    "Combat may be explosive, yet the coliseum must remain a major compositional element per "
    "[CATSTYLE ENVIRONMENT DOMINANCE v1] and [CATSTYLE CAMERA / FRAMING LOCK v1]."
)

TENSE_PLANET_REF_COMBAT_IDENTITY_BLOCK: Final[str] = (
    "[TENSE ASPECT PLANET REFERENCE COMBAT IDENTITY v1] Approved per-planet image references anchor face shape, "
    "facial language, archetypal vibe, costume language, color identity, and planetary symbolism during combat—"
    "do not genericize into ordinary cats; combat expression must preserve each referenced planet-cat identity."
)

TENSE_ASPECT_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "static standing pose during hard aspect",
    "calm ceremonial face-off",
    "idle mascot posing with no kinetic tension",
    "two cats merely standing in arena",
    "passive face-off without force clash",
    "watercolor illustration drift",
    "painterly wash dominance",
    "dry illustration texture",
    "soft brushed canvas look",
    "matte gouache storybook finish",
    "dusty soft illustration rendering",
)

_PLANET_COMBAT_LEXICONS: Final[dict[str, str]] = {
    "Sun": (
        "[PLANETARY COMBAT LEXICON v2 - Sun] Radiates dominance, authority, and solar force—corona flare strikes, "
        "commanding forward pressure, golden beam authority, solar crown intensity; never passive spotlight posing."
    ),
    "Moon": (
        "[PLANETARY COMBAT LEXICON v2 - Moon] Fluid intuition, lunar crescent motion, silver force—tidal push, "
        "crescent arc guard/strike, pearlescent defensive burst, emotional flinch/retreat/burst; soft but active."
    ),
    "Mercury": (
        "[PLANETARY COMBAT LEXICON v2 - Mercury] Speed, tricks, scroll/symbol/signal energy—rapid feints, "
        "intellect sparks, messenger dash, glyph-signal flares, misdirection strikes; never static note-taking pose."
    ),
    "Venus": (
        "[PLANETARY COMBAT LEXICON v2 - Venus] Fights through charm, radiance, elegance, magnetism, beauty-force, "
        "luminous defense, seductive misdirection—not passive flower-holding; value-field glow, graceful counter, "
        "alluring force ripple, radiant parry."
    ),
    "Mars": (
        "[PLANETARY COMBAT LEXICON v2 - Mars] Direct aggressive physical attack—charge, strike, flame-trail lunge, "
        "impact-first brawl energy, decisive forward assault; never hesitant standoff."
    ),
    "Jupiter": (
        "[PLANETARY COMBAT LEXICON v2 - Jupiter] Grand authority, expansion, blessing-force, noble dominance—"
        "expansive press, auroral surge, commanding swell, generous-but-overwhelming force; not timid scale shrink."
    ),
    "Saturn": (
        "[PLANETARY COMBAT LEXICON v2 - Saturn] Constrains, blocks, weighs down, restricts, binds, resists with "
        "matter/chains/sand/gravity—stone press, chain bind, gate slam, time-lock freeze, structural downward force; "
        "never fiery reckless Mars aggression."
    ),
    "Uranus": (
        "[PLANETARY COMBAT LEXICON v2 - Uranus] Counters unpredictably with electric disruption—lightning zig, "
        "portal jolt, shockwave twist, asymmetrical counter, rule-break feint; never orderly static dueling."
    ),
    "Neptune": (
        "[PLANETARY COMBAT LEXICON v2 - Neptune] Mist, tides, dream-force, illusion, oceanic magic—wave dissolve, "
        "fog blind, tidal shove, dream-mist misdirection, abyssal shimmer; not blank passive floating."
    ),
    "Pluto": (
        "[PLANETARY COMBAT LEXICON v2 - Pluto] Abyssal force, shadow, transformation, pressure—shadow tendril tug, "
        "underworld weight, spiral-eye lock, transformative crush; not generic dark boss standing."
    ),
}


def is_tense_hard_aspect(aspect_type: str, mode: str | None = None) -> bool:
    """True for square/opposition when flow-mode alliance staging must not inherit battle blocks."""
    asp = (aspect_type or "").strip().lower()
    if asp not in TENSE_HARD_ASPECTS:
        return False
    return (mode or "").strip().lower() != "flow"


def _moon_combat_lexicon(pa: str, pb: str, aspect_type: str, mode: str) -> str:
    if is_moon_saturn_square_tension(pa, pb, aspect_type, mode):
        return (
            "[PLANETARY COMBAT LEXICON v2 - Moon] Prefer glowing crescent sickle strikes/guards, moonlight arc, "
            "protective defensive motion, emotional flinch/retreat/burst—soft but active force; optional sleep relic "
            "as secondary prop only."
        )
    return _PLANET_COMBAT_LEXICONS["Moon"]


def _saturn_combat_lexicon(pa: str, pb: str, aspect_type: str, mode: str) -> str:
    if is_moon_saturn_square_tension(pa, pb, aspect_type, mode):
        return (
            "[PLANETARY COMBAT LEXICON v2 - Saturn] Prefer chain bind as main control read, gravity press, stone block, "
            "freeze field, gate slam, stop gesture, time lock—cold downward structural force. Never orange/fire/solar/"
            "Mars-coded Saturn: no flames, no fire aura, no rage-warrior or martial-arts duel choreography."
        )
    return _PLANET_COMBAT_LEXICONS["Saturn"]


def build_planetary_combat_lexicon_for_pair(
    planet_a: str,
    planet_b: str,
    aspect_type: str = "",
    mode: str = "",
) -> str:
    """Planet-specific combat behavior lexicon for both planets in the pair."""
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    chunks: list[str] = []
    for planet in (pa, pb):
        key = planet.strip()
        if key.lower() == "moon":
            chunk = _moon_combat_lexicon(pa, pb, aspect_type, mode)
        elif key.lower() == "saturn":
            chunk = _saturn_combat_lexicon(pa, pb, aspect_type, mode)
        else:
            chunk = _PLANET_COMBAT_LEXICONS.get(key, "")
        if chunk and chunk not in chunks:
            chunks.append(chunk)
    return " ".join(chunks).strip()


def build_tense_aspect_choreography_layer(
    aspect_type: str,
    mode: str | None,
    planet_a: str,
    planet_b: str,
    *,
    planet_refs_active: bool = False,
) -> str:
    """Reusable tense-aspect block stack for square/opposition (non-flow)."""
    if not is_tense_hard_aspect(aspect_type, mode):
        return ""
    asp = (aspect_type or "").strip().lower()
    blocks: list[str] = []
    if asp == "square":
        conflict = build_square_conflict_law_block(planet_a, planet_b, aspect_type, mode)
        if conflict:
            blocks.append(conflict)
        blocks.append(TENSE_SQUARE_CHOREOGRAPHY_BLOCK)
    elif asp == "opposition":
        blocks.append(TENSE_OPPOSITION_CHOREOGRAPHY_BLOCK)
    blocks.extend(
        [
            TENSE_ANTI_STATIC_BLOCK,
            TENSE_PREMIUM_CG_STYLE_BLOCK,
            TENSE_BATTLE_ARENA_BALANCE_BLOCK,
            build_planetary_combat_lexicon_for_pair(planet_a, planet_b, aspect_type, mode or ""),
        ]
    )
    if planet_refs_active:
        blocks.append(TENSE_PLANET_REF_COMBAT_IDENTITY_BLOCK)
    return " ".join(b for b in blocks if b).strip()


__all__ = [
    "TENSE_ANTI_STATIC_BLOCK",
    "TENSE_ASPECT_NEGATIVE_EXTRAS",
    "TENSE_BATTLE_ARENA_BALANCE_BLOCK",
    "TENSE_HARD_ASPECTS",
    "TENSE_OPPOSITION_CHOREOGRAPHY_BLOCK",
    "TENSE_PLANET_REF_COMBAT_IDENTITY_BLOCK",
    "TENSE_PREMIUM_CG_STYLE_BLOCK",
    "TENSE_SQUARE_CHOREOGRAPHY_BLOCK",
    "build_planetary_combat_lexicon_for_pair",
    "build_tense_aspect_choreography_layer",
    "is_tense_hard_aspect",
]
