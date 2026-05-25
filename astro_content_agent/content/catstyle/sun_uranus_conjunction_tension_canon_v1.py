"""Pair-specific premium visual canon: Sun conjunct Uranus (tension).

Solar identity/will overloaded by Uranian shock, rebellion, and breakthrough—fusion staging
in the cosmic zodiac coliseum with canonical ☉/♅ banner glyphs.
"""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.planet_glyph_registry_v1 import format_pair_flag_glyph_system_block


def is_sun_uranus_conjunction_tension(planet_a: str, planet_b: str, aspect_type: str, mode: str) -> bool:
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    if {pa, pb} != {"Sun", "Uranus"}:
        return False
    if (aspect_type or "").strip().lower() != "conjunction":
        return False
    return (mode or "").strip().lower() == "tension"


def sun_uranus_conjunction_tension_flag_glyph_block(
    planet_a: str, planet_b: str, aspect_type: str, mode: str
) -> str:
    """Left/port = Sun ☉, right/starboard = Uranus ♅ for Sun–Uranus conjunction + tension."""
    if is_sun_uranus_conjunction_tension(planet_a, planet_b, aspect_type, mode):
        return format_pair_flag_glyph_system_block("Sun", "Uranus").strip()
    return ""


SUN_URANUS_CONJUNCTION_TENSION_VISUAL_CANON: Final[str] = (
    "[SUN-URANUS CONJUNCTION TENSION VISUAL CANON v1] "
    "**Core metaphor:** the solar center of identity and will is **overloaded** by Uranian electricity—shock, rebellion, "
    "sudden liberation, system-break, and creative disruption. **Conjunction = fusion/overload**, not two cats merely arguing. "
    "**Tension = unstable ignition**—solar flare meets lightning strike; identity shocked awake. "
    "**Premium cinematic comic-poster** in the **cosmic zodiac coliseum arena** (monumental tiered architecture, tournament scale). "
    "**Earth disk above** the arena vault; **zodiac circle engraved into stone floor / stone brick paving**. "
    "**Approved-reference benchmark:** when the Sun/Uranus approved reference is active, use it as the **benchmark for all future Sun/Uranus images**—"
    "match its premium density, coliseum scale, and catplanet reads. "
    "**Sun planet-cat** = **living solar-core body** (molten plasma / star-surface texture, orange-gold celestial glow, "
    "corona integrated in silhouette)—armor/staff are **secondary trim**, NOT a normal orange furry cat with fire VFX. "
    "**Sky:** **dense layered starfield**, Milky Way streak, nebula haze—Earth above arena but sky **never empty except Earth**. "
    "**Uranus planet-cat** = **bright cyan ice-gas** with **strong electric rings / orbit effects**, inventor debris, "
    "hard rebel-genius face, tech hardware silhouette—**NO leather jacket**; match approved **premium spectacle** without body glyphs. "
    "**Mandatory staging:** **Sun on the left or center-left** as the radiant solar force; **Uranus on the right or center-right** "
    "as the electric disruptive force—preserve at poster scale. "
    "**Fusion beat:** visible **energy collision/fusion** between them—**dynamic movement**, **shockwave**, "
    "**solar flare + electric lightning arc** bridging the conjunction (high scale, strong silhouettes, dramatic rim and impact lighting). "
    "**Not** a static face-off, **not** two cats simply pointing at each other, **not** weak low-stakes argument posing. "
    "**Glyph / flag hard-lock:** left banner cloth **only canonical Sun glyph \u2609 (☉)**; right banner **only canonical Uranus glyph "
    "\u2645 (♅)**—large clean readable marks **integrated into flag cloth** per **[CATSTYLE PAIR FLAG GLYPH SYSTEM v1]**; "
    "no fake glyphs, no random symbols, no wrong Uranus sign. "
    "**Drift negatives (this pair):** reject storybook illustration, children-book style, soft watercolor, cozy cute scene, "
    "flat mascot cats, toy-like cats, simple argument pose, generic cute cartoon, static standing confrontation."
)


SUN_URANUS_APPROVED_REFERENCE_FIDELITY_BLOCK: Final[str] = (
    "[SUN-URANUS APPROVED REFERENCE FIDELITY v1] When the approved Sun/Uranus conjunction+tension reference is active, "
    "match its **premium battle-poster** DNA: **Sun** = orange-gold royal solar catplanet warrior—heavy, fierce, "
    "solar authority / Leo-coded royal fire (never a simple cute orange cat). "
    "**Uranus** = **bright cyan** ice-gas electric disruptor—**punk-tech cuffs, heavy collar/harness, portal-tech**, strong orbit identity, "
    "anarchist rebel genius silhouette (match approved reference accessory/hardware richness—**no body/chest/collar/harness glyphs**). "
    "Preserve **red Sun faction flag left** with canonical **\u2609 (☉)** and **blue Uranus faction flag right** with canonical **\u2645 (♅)**—"
    "large heraldic cloth integration. Preserve **orange solar force versus blue electric Uranian force**, "
    "**dynamic battle composition** with shockwave / flare / arc energy (not static pointing duel), "
    "**high contrast**, **sharp linework**, **dramatic rim lighting**, **expensive poster finish**, "
    "**grand brighter coliseum** with illuminated arches and tier depth, **Earth above arena**, **rich saturated cosmic sky** "
    "(many stars, **colorful Milky Way / galaxy band**, nebula variation), **large readable zodiac circle floor**—"
    "fantasy-cosmic premium poster, not a playful duel or flat simple confrontation."
)

SUN_URANUS_APPROVED_REFERENCE_FIDELITY_COMPACT: Final[str] = (
    "[SUN-URANUS REF FIDELITY] **Approved reference = visual target.** "
    "Sun: molten solar-core, staff, fiery premium (\u2609 red flag left—filled central dot). "
    "Uranus: bright cyan/blue, **lightning/electric rings**, **orbiting stones/debris**, rebel genius—**no jacket** (\u2645 blue flag right only). "
    "Arena: **spectacular brighter** coliseum, slight asymmetry; sky: **many stars**, **colorful Milky Way band**, nebula dust—Earth above. "
    "Overall: **brighter, richer, cinematic** orange-vs-blue showdown; banner-only glyphs. "
    "**Benchmark for all future Sun/Uranus images** when approved reference is active."
)


SUN_URANUS_CONJUNCTION_TENSION_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "storybook illustration dominance",
    "cozy cute low-drama conjunction scene",
    "static face-off with no fusion energy",
    "weak low-stakes argument pose",
    "cute yellow cat with no solar authority",
    "generic blue trickster cat with no electric disruption",
    "ordinary fur cats",
    "reference-lite reinterpretation",
    "simplified mascot redraw",
    "soft cartoon redraw",
    "low-density render",
    "flat arena backdrop",
    "losing approved reference visual DNA",
    "fake astrology glyphs or wrong Uranus symbol on banners",
    "malformed Sun or Uranus planetary signs",
)

__all__ = [
    "SUN_URANUS_APPROVED_REFERENCE_FIDELITY_COMPACT",
    "SUN_URANUS_APPROVED_REFERENCE_FIDELITY_BLOCK",
    "SUN_URANUS_CONJUNCTION_TENSION_NEGATIVE_EXTRAS",
    "SUN_URANUS_CONJUNCTION_TENSION_VISUAL_CANON",
    "is_sun_uranus_conjunction_tension",
    "sun_uranus_conjunction_tension_flag_glyph_block",
]
