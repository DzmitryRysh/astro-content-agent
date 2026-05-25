"""Reusable premium cosmic zodiac arena environment baseline (approved-reference direction)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.world_templates_v1 import DEFAULT_WORLD_TEMPLATE_KEY

COSMIC_ZODIAC_ARENA_PREMIUM_ENVIRONMENT_LOCK_BLOCK: Final[str] = (
    "[COSMIC ZODIAC ARENA PREMIUM ENVIRONMENT v1] **Default arena/environment target** for Catstyle cosmic zodiac "
    "coliseum generations: **brighter, richer, more premium, more cinematic** fantasy-cosmic poster finish—"
    "**not** dark minimal semicircle walls, **not** empty sky with only Earth. "
    "Honor **[COSMIC ZODIAC ARENA PREMIUM COLISEUM v1]**, **[COSMIC ZODIAC ARENA PREMIUM SKY v1]**, and "
    "**[COSMIC ZODIAC ARENA PREMIUM SPECTACLE v1]** at visible thumbnail strength. "
    "**Zodiac floor** stays readable and beautiful (see zodiac arena floor lock). "
    "Banner heraldic glyphs stay on faction cloth only—avoid body/accessory glyph clutter."
)

COSMIC_ZODIAC_ARENA_PREMIUM_COLISEUM_BLOCK: Final[str] = (
    "[COSMIC ZODIAC ARENA PREMIUM COLISEUM v1] Cosmic zodiac coliseum = **brighter, richer, more spectacular** "
    "monumental tournament architecture—**strong illuminated arches**, **deeper readable tiers**, layered stone depth, "
    "**premium expensive** visual feel. **Elegant asymmetry** and **subtle architectural variation** "
    "(uneven tiers, tasteful ancient wear, irregular arches)—**grand and majestic**, **not** a flat dark semicircle slab, "
    "**not** ruined chaos or rubble apocalypse."
)

COSMIC_ZODIAC_ARENA_PREMIUM_SKY_BLOCK: Final[str] = (
    "[COSMIC ZODIAC ARENA PREMIUM SKY v1] Night vault = **rich starfield** with **many visible stars** at layered depths; "
    "a **colorful Milky Way / galaxy band** sweeping the sky (violet-blue, magenta, gold dust—not monochrome gray); "
    "**cosmic dust rivers**, **nebula color variation**, and depth behind **Earth** above the arena. "
    "Sky feels **alive and saturated**—Earth remains present but is **never** the only sky feature. "
    "Sky stays behind fighters—do not overpower hero silhouettes."
)

COSMIC_ZODIAC_ARENA_PREMIUM_SPECTACLE_BLOCK: Final[str] = (
    "[COSMIC ZODIAC ARENA PREMIUM SPECTACLE v1] **Premium spectacle baseline:** stronger **volumetric light**, "
    "**high-contrast keyed lighting**, **cinematic clarity**, and readable **material separation** across arena, sky, "
    "and fighters. When aspect energy calls for it, paint **strong electric rings / orbit halos / charged debris** "
    "around electric or ice-gas fighters—rich atmosphere, dramatic motion, **not** soft plush or muddy flat backdrop."
)

COSMIC_ZODIAC_ARENA_PREMIUM_ENVIRONMENT_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "dark flat semicircle coliseum wall",
    "perfect flat semicircle coliseum wall",
    "empty sky with only earth",
    "subtle empty sky with only earth",
    "sky without milky way or dust band",
    "weak sparse starfield",
    "monochrome gray milky way only",
    "dark muddy coliseum backdrop",
    "empty sparse night sky",
    "background collapsing into vague darkness",
    "vague background darkness",
)

_RENDER_STYLE_PREMIUM_CG_KEY = "premium_cg_keyart_v1"


def applies_cosmic_zodiac_arena_premium_environment(
    *,
    world_template_key: str | None,
    premium_art_direction: bool = False,
    render_style_profile_key: str | None = None,
    shot_mode: str | None = None,
    mode: str | None = None,
) -> bool:
    """True when the reusable premium arena/environment baseline should attach."""
    if (mode or "").strip().lower() == "flow":
        return False
    world = (world_template_key or DEFAULT_WORLD_TEMPLATE_KEY).strip().lower().replace("-", "_")
    if world != DEFAULT_WORLD_TEMPLATE_KEY:
        return False
    if premium_art_direction:
        return True
    render = (render_style_profile_key or "").strip().lower().replace("-", "_")
    return render == _RENDER_STYLE_PREMIUM_CG_KEY


def cosmic_zodiac_arena_premium_environment_blocks() -> str:
    """Full premium arena/environment direction for cosmic_zodiac_arena shell."""
    return " ".join(
        (
            COSMIC_ZODIAC_ARENA_PREMIUM_ENVIRONMENT_LOCK_BLOCK,
            COSMIC_ZODIAC_ARENA_PREMIUM_COLISEUM_BLOCK,
            COSMIC_ZODIAC_ARENA_PREMIUM_SKY_BLOCK,
            COSMIC_ZODIAC_ARENA_PREMIUM_SPECTACLE_BLOCK,
        )
    ).strip()


__all__ = [
    "COSMIC_ZODIAC_ARENA_PREMIUM_COLISEUM_BLOCK",
    "COSMIC_ZODIAC_ARENA_PREMIUM_ENVIRONMENT_LOCK_BLOCK",
    "COSMIC_ZODIAC_ARENA_PREMIUM_ENVIRONMENT_NEGATIVE_EXTRAS",
    "COSMIC_ZODIAC_ARENA_PREMIUM_SKY_BLOCK",
    "COSMIC_ZODIAC_ARENA_PREMIUM_SPECTACLE_BLOCK",
    "applies_cosmic_zodiac_arena_premium_environment",
    "cosmic_zodiac_arena_premium_environment_blocks",
]
