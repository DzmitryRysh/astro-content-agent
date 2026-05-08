"""Catstyle Planet Canon v1 - deterministic identity layer for all ten planets."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PlanetCanonProfile(BaseModel):
    planet_name: str
    archetype: str
    core_mood: str
    visual_language: str
    materials: str
    color_logic: str
    motion_language: str
    pose_language: str
    signature_props: str
    environment_cues: str
    face_expression: str
    aura_style: str
    must_have: list[str] = Field(default_factory=list, min_length=1)
    must_not_have: list[str] = Field(default_factory=list, min_length=1)


_ORDER = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)
_CANONICAL: dict[str, str] = {p.lower(): p for p in _ORDER}

PLANET_CANON_V1: dict[str, PlanetCanonProfile] = {
    "Sun": PlanetCanonProfile(
        planet_name="Sun",
        archetype="Radiant center, leadership, dignity, coherent authority.",
        core_mood="Warm confidence, visibility, sovereign presence.",
        visual_language="Central composition, crown-like solar geometry, clean heroic read.",
        materials="Polished gold, warm enamel, satin sunlight bloom.",
        color_logic="Gold, amber, warm cream, controlled orange accents.",
        motion_language="Measured commanding arcs, deliberate spotlight turns.",
        pose_language="Open chest, lifted chin, centered stage-ready stance.",
        signature_props="Solar medallion, subtle regal collar motifs, banner-like drape.",
        environment_cues="Dawn horizon, concentric radiance, ordered ceremonial space.",
        face_expression="Confident noble gaze, warm assertive half-smile.",
        aura_style="Halo-like golden corona with stable radial symmetry.",
        must_have=[
            "Sun must read as central and radiant authority.",
            "Keep warm gold-led palette with dignified stage presence.",
        ],
        must_not_have=[
            "Do not depict Sun as timid, hidden, or sneaky-chaotic.",
            "Do not collapse Sun into diffuse background energy.",
        ],
    ),
    "Moon": PlanetCanonProfile(
        planet_name="Moon",
        archetype="Safety, softness, rhythm, care, emotional honesty.",
        core_mood="Tender, vulnerable, comfort-seeking, protective.",
        visual_language="Rounded protective silhouettes, fabric and cushion cues, gentle curves.",
        materials="Soft cloth, velvet blanket texture, milk-light glow, water-soft gradients.",
        color_logic="Silver, pearl, pale blue-gray, muted lavender shadow.",
        motion_language="Slow rocking, protective wrapping gestures, tidal pacing.",
        pose_language="Curled or shielding posture, inward arms, guarded openness.",
        signature_props="Pillow, folded blanket, crescent motifs, quiet vessel of water.",
        environment_cues="Moonlit interior nook, calm reflective surfaces, safe nest feel.",
        face_expression="Soft eyes, feeling-forward honesty, fragile but present gaze.",
        aura_style="Silver-lunar glow, diffuse mist edge, low-intensity aura.",
        must_have=[
            "Moon must read as soft, vulnerable, comfort-seeking, silver-lit.",
            "Preserve safety-and-care emotional language before conflict dynamics.",
        ],
        must_not_have=[
            "Do not give Moon a fiery aura or militaristic strike posture.",
            "Do not depict Moon as bluntly aggressive combat energy.",
            "Do not depict Moon as an action-hero fighter archetype.",
        ],
    ),
    "Mercury": PlanetCanonProfile(
        planet_name="Mercury",
        archetype="Signals, speech, wit, analysis, questions, agility.",
        core_mood="Quick-minded, curious, adaptive, communicative.",
        visual_language="Dynamic hand gestures, messenger lines, note/symbol framing.",
        materials="Paper, ink, polished light metal accents, translucent data ribbons.",
        color_logic="Cool gray, mint, quick silver-white highlights.",
        motion_language="Rapid pivots, darting vector movement, conversational rhythm.",
        pose_language="Forward lean, active hands, observational stance.",
        signature_props="Notes, messenger satchel, glyph cards, stylus-like pointer.",
        environment_cues="Signal lanes, airy studio maps, symbolic overlays.",
        face_expression="Alert eyes, skeptical brow lift, playful precision.",
        aura_style="Thin fast-moving light traces, signal pulses.",
        must_have=[
            "Mercury must read as fact-seeking, question-asking, signal-processing intelligence.",
            "Keep agile messenger posture and active hand language.",
        ],
        must_not_have=[
            "Do not depict Mercury as heavy monolithic stillness.",
            "Do not replace Mercury with brute-force aggression.",
        ],
    ),
    "Venus": PlanetCanonProfile(
        planet_name="Venus",
        archetype="Attraction, harmony, tact, beauty, pleasure, value curation.",
        core_mood="Graceful, inviting, relational, sensual but controlled.",
        visual_language="Elegant curves, balanced ornament, soft relational spacing.",
        materials="Silk, pearl, brushed rose metal, floral textures.",
        color_logic="Rose, cream, soft green accents, balanced warm neutrals.",
        motion_language="Fluid elegant transitions, inviting reach-and-withdraw cadence.",
        pose_language="Open relational posture, graceful neck and paw arcs.",
        signature_props="Mirror, pearl strand, rose/floral motif, refined accessory anchor.",
        environment_cues="Curated aesthetic setting, soft drapery, pleasing symmetry.",
        face_expression="Warm charming gaze, refined pleasure-aware expression.",
        aura_style="Velvet glow, rose-gold soft aura, polished harmony field.",
        must_have=[
            "Venus must read as charm, contact, pleasure, and refined taste.",
            "Keep graceful relational posture and aesthetic softness.",
        ],
        must_not_have=[
            "Do not depict Venus with rough combat posture.",
            "Do not reduce Venus to blunt aggression or militaristic force.",
        ],
    ),
    "Mars": PlanetCanonProfile(
        planet_name="Mars",
        archetype="Strike, action, risk, force, heat, decisive momentum.",
        core_mood="Urgent, assertive, confrontational, kinetic.",
        visual_language="Forward-driving diagonals, impact cues, sharp vector thrust.",
        materials="Forged iron, scorched leather, ember sparks, battle-worn edges.",
        color_logic="Red, rust, iron black, white-hot spark accents.",
        motion_language="Lunge, burst, stomp, immediate directional push.",
        pose_language="Charge-ready stance, planted power, attack-forward lean.",
        signature_props="Bandana, impact marks, steam/spark cues, training blade motifs.",
        environment_cues="Impact floor cracks, heat distortion, kinetic debris.",
        face_expression="Determined scowl, intense focus, clenched readiness.",
        aura_style="Hot red aura with impact flickers and pressure arcs.",
        must_have=[
            "Mars must read as heat, action, and immediate force.",
            "Preserve forward-driving posture and strike-ready momentum.",
        ],
        must_not_have=[
            "Do not depict Mars as passive drifting softness.",
            "Do not drain Mars into indecisive decorative stillness.",
        ],
    ),
    "Jupiter": PlanetCanonProfile(
        planet_name="Jupiter",
        archetype="Expansion, meaning, benevolent authority, horizon and belief.",
        core_mood="Generous, broad, optimistic, mentoring.",
        visual_language="Large framing, expansive gestures, sky-opening composition.",
        materials="Rich cloth, polished wood, ceremonial trim, celestial parchment.",
        color_logic="Royal purple, warm ochre, expansive blue-cream contrast.",
        motion_language="Broad welcoming sweeps, upward horizon gestures.",
        pose_language="Open arms, elevated chest, teacher-or-orator posture.",
        signature_props="Banner, open codex, guide pointer, laurel/crest hint.",
        environment_cues="Wide horizon, elevated platforms, grand civic-cosmic space.",
        face_expression="Confident benevolent smile, mentor clarity in gaze.",
        aura_style="Large soft radiant field with high-altitude openness.",
        must_have=[
            "Jupiter must read as large-scale growth, meaning, and benevolent authority.",
            "Preserve expansive posture and horizon-oriented staging.",
        ],
        must_not_have=[
            "Do not collapse Jupiter into petty cramped minimalism.",
            "Do not depict Jupiter as mean-spirited small-scale pettiness.",
        ],
    ),
    "Saturn": PlanetCanonProfile(
        planet_name="Saturn",
        archetype="Structure, control through form, time, limits, responsibility.",
        core_mood="Cold, heavy, severe, disciplined, patient.",
        visual_language="Rigid geometry, vertical authority, barrier and gate motifs.",
        materials="Stone, iron, graphite, chain links, clockwork metal.",
        color_logic="Graphite gray, iron black, desaturated bronze, cold edge light.",
        motion_language="Minimal controlled motion, stop-gesture authority, timed stillness.",
        pose_language="Upright rigid stance, limiting gestures, judge-like containment.",
        signature_props="Clock/ring motif, key, chain or architectural frame elements.",
        environment_cues="Tower, wall, threshold, shadowed institutional space.",
        face_expression="Severe measured stare, disciplined restraint, non-reactive authority.",
        aura_style="Cold compressed field, heavy gravity halo, low-frequency shadow ring.",
        must_have=[
            "Saturn must read as cold, heavy, stone-and-iron authority.",
            "Keep rigid boundary-setting posture and formal structural presence.",
        ],
        must_not_have=[
            "Do not depict Saturn with flames or reckless attack energy.",
            "Do not depict Saturn as explosive combat speed or wild chaos.",
            "Do not depict Saturn with martial weapons, ninja/fighter styling, or Mars-like aggression.",
            "Do not let Saturn inherit Mars visual traits.",
        ],
    ),
    "Uranus": PlanetCanonProfile(
        planet_name="Uranus",
        archetype="Rupture, rebellion, liberation, surprise, weird truth.",
        core_mood="Electric, disruptive, unconventional, anti-script.",
        visual_language="Asymmetry, fracture lines, neon-electric interruptions.",
        materials="Charged alloys, neon glass, ionized vapor edges.",
        color_logic="Electric teal, violet, shock-white sparks, high contrast.",
        motion_language="Snap breaks, sudden pivots, unpredictable jumps.",
        pose_language="Angular off-axis stance, anti-classical body line.",
        signature_props="Lightning motifs, portal hoop, fractured geometry accent.",
        environment_cues="Glitch-like skyline, disrupted grid, liberated stage breaks.",
        face_expression="Defiant spark, amused rebel stare, alert disruption grin.",
        aura_style="Electric crackle halo with non-symmetrical pulse arcs.",
        must_have=[
            "Uranus must read as freedom-through-disruption and weird truth.",
            "Keep asymmetry and electric rupture cues visible.",
        ],
        must_not_have=[
            "Do not depict Uranus as obedient classical stability.",
            "Do not smooth Uranus into polite predictable symmetry.",
        ],
    ),
    "Neptune": PlanetCanonProfile(
        planet_name="Neptune",
        archetype="Dream, symbol, mist, compassion, transcendence, diffusion.",
        core_mood="Elusive, poetic, porous, oceanic.",
        visual_language="Soft haze layering, symbolic drift, blurred depth transitions.",
        materials="Mist, water-glass translucence, vapor silk, sea-light film.",
        color_logic="Deep sea blue, fog lavender, aqua glow gradients.",
        motion_language="Drift, dissolve, wave-like glide, non-linear flow.",
        pose_language="Fluid floating posture, partially turned elusive read.",
        signature_props="Fish/star-water motifs, vapor ribbons, symbolic vessel forms.",
        environment_cues="Foggy shoreline cosmos, submerged-star ambience, dream architecture.",
        face_expression="Distant empathetic gaze, soft-focus contemplation.",
        aura_style="Diffuse mist aura with watery star refraction.",
        must_have=[
            "Neptune must read as dreamlike, symbolic, oceanic diffusion.",
            "Preserve mist, translucence, and elusive fluid movement.",
        ],
        must_not_have=[
            "Do not depict Neptune as brute hard realism without dream quality.",
            "Do not force Neptune into rigid literal militaristic framing.",
        ],
    ),
    "Pluto": PlanetCanonProfile(
        planet_name="Pluto",
        archetype="Depth, totality, control, transformation, underworld authority.",
        core_mood="Intense, severe, field-dominating, strategic shadow power.",
        visual_language="Dense gravity center, subterranean pressure, controlled darkness.",
        materials="Black metal, volcanic stone, magma glow, ritual cauldron steel.",
        color_logic="Charcoal black, deep plum, magma ember rim-light.",
        motion_language="Slow pressure shifts, deliberate dominance, controlled surge.",
        pose_language="Heavy anchored stance, contained authority, predatory patience.",
        signature_props="Cauldron, smoke tendrils, ringed iron motifs, deep-core symbols.",
        environment_cues="Subterranean chamber, fault-line glow, abyssal architecture.",
        face_expression="Calm intense stare, non-reactive control, depth-first gaze.",
        aura_style="Compressed dark aura with magma veins and shadow pull.",
        must_have=[
            "Pluto must read as controlled underworld depth and transformation power.",
            "Preserve heavy field-dominating posture and subterranean gravity cues.",
        ],
        must_not_have=[
            "Do not depict Pluto as frivolous light chatty mercurial energy.",
            "Do not flatten Pluto into cute weightless decorative sweetness.",
        ],
    ),
}


def normalize_planet_name(name: str) -> str:
    key = (name or "").strip().lower()
    if key not in _CANONICAL:
        known = ", ".join(_ORDER)
        raise ValueError(f"Unknown planet {name!r}. Planet canon supports: {known}.")
    return _CANONICAL[key]


def get_planet_canon(planet_name: str) -> PlanetCanonProfile:
    return PLANET_CANON_V1[normalize_planet_name(planet_name)]


def list_planet_canons() -> list[PlanetCanonProfile]:
    return [PLANET_CANON_V1[p] for p in _ORDER]


def build_planet_canon_prompt_fragment(planet_name: str) -> str:
    c = get_planet_canon(planet_name)
    must_have = " | ".join(c.must_have)
    must_not = " | ".join(c.must_not_have)
    return (
        f"[PLANET CANON v1 - {c.planet_name}] "
        f"Archetype: {c.archetype} "
        f"Core mood: {c.core_mood} "
        f"Visual language: {c.visual_language} "
        f"Materials: {c.materials} "
        f"Color logic: {c.color_logic} "
        f"Motion language: {c.motion_language} "
        f"Pose language: {c.pose_language} "
        f"Signature props: {c.signature_props} "
        f"Environment cues: {c.environment_cues} "
        f"Face expression: {c.face_expression} "
        f"Aura style: {c.aura_style} "
        f"Must-have identity: {must_have} "
        f"Must-not identity: {must_not}."
    )


__all__ = [
    "PlanetCanonProfile",
    "PLANET_CANON_V1",
    "build_planet_canon_prompt_fragment",
    "get_planet_canon",
    "list_planet_canons",
    "normalize_planet_name",
]
