"""Reference render/material fidelity for approved planet refs (clean refs v1)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

REFERENCE_MATERIAL_FIDELITY_MARKER: Final[str] = "[REFERENCE MATERIAL FIDELITY v1]"

REFERENCE_MATERIAL_FIDELITY_BLOCK: Final[str] = (
    "[REFERENCE MATERIAL FIDELITY v1] Approved planet references define not only identity, but also render quality "
    "and material treatment. Preserve the premium 3D material feel from the refs: sculpted fur, glossy eyes, "
    "metallic accessories, jewelry, gems, layered costume fabric, armor, chains, weapons, crisp specular highlights, "
    "volumetric rim light, and physical material separation. Do not flatten planet-cats into soft digital painting, "
    "poster illustration, airbrushed mascot art, storybook fantasy, or generic painted rendering. The generated scene "
    "must look like the approved reference characters were placed into the arena, not redrawn in a cheaper illustrated "
    "style."
)

_PLANET_REFERENCE_MATERIAL_BLOCKS: Final[dict[str, str]] = {
    "Venus": (
        "[VENUS MATERIAL FIDELITY] pearl-pink/rose-gold body, translucent flowing ribbons, glowing jewelry, glossy gems, "
        "premium costume layering, soft sculpted 3D fur—not flat beige/pink painted cat or simple princess mascot."
    ),
    "Saturn": (
        "[SATURN MATERIAL FIDELITY] black-and-gold heavy layered robes, metallic chains, ringed Saturn hat silhouette, "
        "gold dust/stone/time-pressure aura, crisp chain links, premium dark fabric—not flat dark villain cat or "
        "generic black-robed mascot."
    ),
    "Uranus": (
        "[URANUS MATERIAL FIDELITY] cyan/turquoise electric fur, glowing orbital plasma rings, floating debris, metallic "
        "bands, sharp cyan eyes, crisp electric rim light—not generic blue lightning cat."
    ),
    "Neptune": (
        "[NEPTUNE MATERIAL FIDELITY] oceanic blue/cyan/silver palette, trident identity, liquid energy details, glossy "
        "water-like highlights, layered costume/jewel details—not flat solid-blue water mascot."
    ),
    "Mars": (
        "[MARS MATERIAL FIDELITY] red/orange martial body, battle armor, shield/weapon detail, hot ember lighting, "
        "crisp metal highlights—not generic orange cartoon warrior cat."
    ),
    "Mercury": (
        "[MERCURY MATERIAL FIDELITY] silver/blue messenger body, glyph/signal ribbons, staff detail, luminous "
        "scroll/symbol effects, glossy gems/metal accents—not generic gray mage cat."
    ),
    "Sun": (
        "[SUN MATERIAL FIDELITY] golden solar body, radiant crown/light, warm luminous fur, bright specular gold "
        "accents—not generic orange fire cat."
    ),
    "Moon": (
        "[MOON MATERIAL FIDELITY] pearl/silver lunar softness, reflective glow, delicate moonlit fur, emotional "
        "luminous aura—not generic pale cat."
    ),
    "Pluto": (
        "[PLUTO MATERIAL FIDELITY] dark underworld body, volcanic/shadow aura, deep jewel/obsidian materials, intense "
        "eyes—not generic black villain cat."
    ),
    "Jupiter": (
        "[JUPITER MATERIAL FIDELITY] grand regal body, gold/purple storm-like planetary richness, ceremonial "
        "accessories, premium ornate material—not generic large wizard cat."
    ),
}

REFERENCE_MATERIAL_FIDELITY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "cheap illustrated redraw",
    "flat fantasy painting",
    "soft painted mascot",
    "lost reference material quality",
    "flat painted fur",
    "flat painted armor",
    "missing jewelry detail",
    "missing glossy gems",
    "missing chain detail",
    "missing weapon detail",
    "low material separation",
    "generic planet cat",
    "reference quality lost",
    "storybook fantasy art",
    "airbrushed mascot look",
    "non-3d illustration",
)


def build_reference_material_fidelity_block(planet_a: str, planet_b: str) -> str:
    """Global material fidelity plus planet-specific reminders for the two active planets."""
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    parts = [REFERENCE_MATERIAL_FIDELITY_BLOCK]
    for planet in (pa, pb):
        block = _PLANET_REFERENCE_MATERIAL_BLOCKS.get(planet)
        if block:
            parts.append(block)
    return " ".join(parts).strip()


__all__ = [
    "REFERENCE_MATERIAL_FIDELITY_BLOCK",
    "REFERENCE_MATERIAL_FIDELITY_MARKER",
    "REFERENCE_MATERIAL_FIDELITY_NEGATIVE_EXTRAS",
    "build_reference_material_fidelity_block",
]
