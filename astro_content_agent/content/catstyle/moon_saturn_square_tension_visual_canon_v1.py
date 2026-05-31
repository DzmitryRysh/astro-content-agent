"""Pair-specific premium visual canon: Moon square Saturn (tension).

Encodes sickle-forward Moon, cold-iron Saturn (anti fire-drift), square psychological choreography,
and brighter coliseum statue/arcade beats—compatible with premium environment and arena reference.
"""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name


def is_moon_saturn_square_tension(planet_a: str, planet_b: str, aspect_type: str, mode: str) -> bool:
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    if {pa, pb} != {"Moon", "Saturn"}:
        return False
    if (aspect_type or "").strip().lower() != "square":
        return False
    return (mode or "").strip().lower() == "tension"


MOON_SATURN_SATURN_IDENTITY_HARD_LOCK: Final[str] = (
    "[MOON-SATURN SATURN IDENTITY HARD LOCK v1] **Saturn must NOT read as Sun, Mars, or fire antagonist.** "
    "Reject **orange** Saturn body, **fiery** rim, **solar** gold-orange glow, **Mars-like** rage-warrior staging, "
    "**flame-coded** aura, **magma-coded** cracks, **rage-fire** eyes, or **screaming fire warrior** energy. "
    "Saturn = **cold, dark, heavy** cat-planet—**lead / iron / stone** authority: **charcoal**, **black**, "
    "**lead-gray**, **muted brown**, **cold steel**, **cold gold** accents only—**no orange fire aura** around Saturn. "
    "**Heavy iron/stone planetary body** with **restrained gravity / time / law / judgment** aura—**not** flame aura. "
    "**Archetype:** **cold lecturer / strategist / psychological enforcer**—calm, controlled, **polite, terrifying, "
    "strategic** (Hannibal Lecter / Gustavo Fring read: immaculate composure, not parody)—**not** a generic fantasy "
    "villain, **not** a shouting fire antagonist. **Silhouette & props:** **chain** as **main** pressure/control symbol; "
    "optional **cane**, **timekeeper**, or **pocket watch** accent; **severe structured coat** or formal authoritarian "
    "silhouette—refined, not goofy."
)

MOON_SATURN_ARENA_PAIR_LOCK: Final[str] = (
    "[MOON-SATURN ARENA PAIR LOCK v1] Preserve **approved arena reference** + premium environment workflow—"
    "arena must be **brighter and more luminous** than a dark semicircle shell: **warm golden arcade lights clearly visible**, "
    "**slight asymmetry / uneven tiers clearly visible**, illuminated arches, readable depth. "
    "Two **background niche statues must be clearly visible** behind the action: (1) **moon / sleep / dream** statue "
    "(lunar serenity, crescent or rest motif) and (2) **time / law / fate** statue (Saturnian measure—scroll, scales, "
    "hourglass, or law motif)—monumental, integrated into coliseum niches, **not** lost in shadow."
)

MOON_SATURN_SQUARE_TENSION_VISUAL_CANON: Final[str] = (
    "[MOON-SATURN SQUARE TENSION VISUAL CANON v1] "
    "**Premium CG key-art** Moon square Saturn in the **cosmic zodiac coliseum** (epic arena showdown scale). "
    "Stack with **[COSMIC ZODIAC ARENA PREMIUM ENVIRONMENT v1]** and approved **arena reference** when active. "
    f"{MOON_SATURN_ARENA_PAIR_LOCK} "
    f"{MOON_SATURN_SATURN_IDENTITY_HARD_LOCK} "
    "**Moon planet-cat:** soft **silver-blue / pale-blue** cat-planet—**vulnerable but emotionally intense**; "
    "**not a brute warrior**. **Main weapon = glowing crescent sickle**—elegant, lunar, magical, **silver-blue**, "
    "slightly curved, **readable and iconic**; sickle is the **primary** action read. A **small sleep relic / moon "
    "cushion** may appear as a **secondary** symbol near Moon—**optional, not the main focus**, never replacing the sickle. "
    "Moon resists pressure with **emotional force**, **lunar instinct**, and **defensive courage**—protective, sensitive, "
    "defensive, emotionally overwhelmed yet standing ground. Soft moonlight glow, dreamlike highlights, subtle emotional "
    "electricity around Moon. "
    "**Saturn planet-cat (reinforce hard lock):** bears down with **cold authority**—**iron discipline**, **criticism**, "
    "**obligation**, **judgment**, **repression**; chain-forward control read; **never** orange/fire/solar/Mars-coded. "
    "**Square tension choreography:** **confrontation**, **pressure**, **blocked flow**—Saturn **bears down** on Moon; "
    "Moon **resists** with **vulnerability** and **defensive courage**. **Not a generic brawl**—**emotional pressure "
    "versus rigid control**, **tenderness versus judgment**, **vulnerability versus repression**. "
    "No MMA body-on-body duel; psychological conflict readable at poster scale. "
    "**Glyph / flag hard-lock:** **left/port banner = Moon glyph only**; **right/starboard banner = Saturn glyph only**—"
    "canonical heraldic gold integrated into cloth per banner-only discipline; **no glyph clutter on bodies**, collars, or props. "
    "**Drift negatives (this pair):** reject **orange/fire/solar/Mars-like Saturn**, **brute-warrior Moon**, "
    "pillow-as-primary-weapon dominance, generic action-hero brawl, goofy lecturer parody, **invisible or missing niche "
    "statues**, **dark flat semicircle** coliseum, weak empty sky, **muted invisible arcade lights**."
)


MOON_SATURN_SQUARE_TENSION_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "Moon as brute warrior or MMA fighter dominant read",
    "pillow strike or cushion as Moon primary weapon instead of crescent sickle",
    "generic brawl or body-on-body martial duel as dominant choreography",
    "Saturn depicted orange fiery solar or Mars-like",
    "Saturn with orange fire aura magma cracks or rage-fire antagonist energy",
    "Saturn as screaming fire warrior or generic fantasy villain",
    "Saturn warm solar gold-orange body glow instead of cold lead iron stone",
    "goofy lecturer parody or cartoonish strict teacher gag",
    "flat dark semicircle coliseum wall without tier depth or visible arcade lights",
    "arena too dark to read two background niche statues",
    "missing visible moon sleep dream and time law fate niche statues",
    "glyph clutter on Moon or Saturn bodies instead of banner cloth only",
)


__all__ = [
    "MOON_SATURN_ARENA_PAIR_LOCK",
    "MOON_SATURN_SATURN_IDENTITY_HARD_LOCK",
    "MOON_SATURN_SQUARE_TENSION_NEGATIVE_EXTRAS",
    "MOON_SATURN_SQUARE_TENSION_VISUAL_CANON",
    "is_moon_saturn_square_tension",
]
