"""Catstyle scene beat / camera templates v1 (pairs with world_templates_v1)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.character_skins_v0 import normalize_skin_key
from astro_content_agent.content.catstyle.models import CatstyleSceneTemplate
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name as canon_normalize_planet_name
from astro_content_agent.services.content.catstyle_art_direction import resolve_art_energy

SCENE_TEMPLATES: dict[str, CatstyleSceneTemplate] = {
    "mars_spartan_cliff_kick": CatstyleSceneTemplate(
        template_key="mars_spartan_cliff_kick",
        display_name="Mars Spartan Cliff Kick",
        compatible_pairs=[
            ("Jupiter", "Mars"),
            ("Mars", "Jupiter"),
            ("Saturn", "Mars"),
            ("Mars", "Saturn"),
        ],
        compatible_aspects=["square", "opposition"],
        compatible_skins=["spartan_king"],
        energy="charged",
        primary_action=(
            "Mars planet-cat in Spartan King overlay executes a dramatic forward cliff-edge martial kick  -  "
            "'This is Mars' kinetic trophy beat framed against arena sky."
        ),
        composition=(
            "Strong diagonal kick line cuts frame; shield and spear readable as comic silhouettes; "
            "Jupiter/Saturn counter-cat reacts at opposing rim of disc."
        ),
        camera_angle="Low heroic three-quarter looking up at kicking Mars; wide enough to read shield face glyph.",
        foreground_elements="Kick dust puff, shield rim catching rim-light, spear shaft parallel to kick vector.",
        background_elements="Arena disc drops into cosmic void; zodiac band hinted at frame edge.",
        emotional_read="Competitive dominance with theatrical hero energy  -  comic, not brutal.",
        required_markers=[
            "Mars glyph visible on shield face or shoulder tattoo (flat icon)",
            "Round Mars planet-cat silhouette intact under armor strips",
        ],
        optional_props=["minimal bronze cape flap", "arena sparks as flat stars"],
        text_overlay_ideas=["optional poster slug blocked  -  never render text"],
        avoid=["realistic gore", "readable Greek lettering", "photoreal weapons"],
        short_prompt_line=(
            "Spartan Mars cliff kick on cosmic arena disc  -  shield + spear + Mars glyph; heroic comic duel staging."
        ),
    ),
    "mars_rambo_survival_pose": CatstyleSceneTemplate(
        template_key="mars_rambo_survival_pose",
        display_name="Mars Rambo Survival Pose",
        compatible_planets=["Mars"],
        compatible_aspects=["square", "opposition", "conjunction"],
        compatible_skins=["rambo"],
        energy="charged",
        primary_action=(
            "Mars in survival-warrior stance  -  bandana, ammo belt blocks, toy machine-gun silhouette lowered ready; "
            "optional cartoon self-stitching beat on shoulder (ink lines only)."
        ),
        composition="Center-survival figure with opposing planet-cat smaller in depth plane reacting to Mars rage-read.",
        camera_angle="Eye-level gritty comic lens; slight dutch tilt for battlefield irony.",
        foreground_elements="Mud streak cards, rain sheet as gray ribbons, shell casings as blank discs.",
        background_elements="Arena rim fog merging into star void.",
        emotional_read="Battlefield exhaustion flipping into cartoon rage  -  funny-survival, not horror.",
        required_markers=["Mars glyph tattoo readable", "headband silhouette crisp"],
        optional_props=["bandolier blocks", "cartoon stitch marks"],
        text_overlay_ideas=["grunt caption blocked"],
        avoid=["photoreal firearms", "readable military patches", "blood"],
        short_prompt_line="Rambo Mars survival pose  -  bandana, ammo silhouette, toy gun shape; comic stitches OK.",
    ),
    "mars_bruce_lee_nunchucks": CatstyleSceneTemplate(
        template_key="mars_bruce_lee_nunchucks",
        display_name="Mars Bruce Lee Nunchucks",
        compatible_planets=["Mars"],
        compatible_aspects=["square", "opposition", "conjunction"],
        compatible_skins=None,
        energy="charged",
        primary_action=(
            "Martial-arts Mars with nunchucks mid-twirl  -  fast low stance, flame tuft on ears readable, kinetic blur arcs "
            "as thick outlines only."
        ),
        composition="Radial motion trails anchored on Mars; partner planet caught mid-flinch at arena mid-line.",
        camera_angle="Slightly high manga-panel tilt emphasizing spin ellipse of nunchucks.",
        foreground_elements="Motion smear curves, impact star puff near paws.",
        background_elements="Zodiac ring blur suggesting arena spin.",
        emotional_read="Speed discipline vs brute Mars stereotypes  -  playful homage energy without copying likeness.",
        required_markers=["Mars glyph on belt buckle or headband tag", "flame ear tuft visible"],
        optional_props=["training drum prop as circle"],
        text_overlay_ideas=["whoosh FX blocked"],
        avoid=["realistic Bruce likeness", "readable logos"],
        short_prompt_line="Mars martial cat  -  nunchucks spin, flame tuft, kinetic silhouette on arena floor.",
    ),
    "venus_marilyn_wind_grate": CatstyleSceneTemplate(
        template_key="venus_marilyn_wind_grate",
        display_name="Venus Marilyn Wind Grate",
        compatible_pairs=[
            ("Uranus", "Venus"),
            ("Venus", "Uranus"),
        ],
        compatible_aspects=["square", "opposition"],
        compatible_skins=None,
        energy="charged",
        primary_action=(
            "Venus planet-cat posed over glowing subway-style vent grate  -  wind lifts dress hem dramatically; "
            "both Venus paws modestly pin skirt hem comic-glam style."
        ),
        composition="Vertical grate light ghosts Venus silhouette; Uranus cat arcs chaotic zigzag neon gust behind.",
        camera_angle="Street-premium low angle inside arena pretending grate is deck vent.",
        foreground_elements="Billowing dress folds as thick shapes, paw pads pressing hem.",
        background_elements="Electric portals mixing stars through grate glow.",
        emotional_read="Glamour disrupted by sudden Uranian gust  -  funny iconic staging without copying IP.",
        required_markers=["Venus glyph on jewelry clasp or belt buckle", "round Venus body readable"],
        optional_props=["single faux pearl bracelet tube"],
        text_overlay_ideas=["dress flare silhouette cue blocked"],
        avoid=["photoreal celebrity likeness", "readable signage"],
        short_prompt_line="Venus over glowing grate  -  paws holding skirt, glyph jewelry; Uranus electric gust backdrop.",
    ),
    "venus_mermaid_cauldron": CatstyleSceneTemplate(
        template_key="venus_mermaid_cauldron",
        display_name="Venus Mermaid Cauldron",
        compatible_pairs=[
            ("Venus", "Neptune"),
            ("Neptune", "Venus"),
            ("Venus", "Pluto"),
            ("Pluto", "Venus"),
        ],
        compatible_aspects=["square", "opposition", "conjunction"],
        compatible_skins=None,
        energy="balanced",
        primary_action=(
            "Venus as mermaid-tail planet-cat partly submerged in bubbling cauldron pool inset into arena floor  -  "
            "tail splash freezes as comic shapes."
        ),
        composition="Cauldron centered disc depression; partner planet looms rim stirring shadows or fog.",
        camera_angle="Slightly above cauldron lip looking down at Venus face pearls.",
        foreground_elements="Bubbles, fish silhouettes, steam curls.",
        background_elements="Nebula steam blending zodiac ring.",
        emotional_read="Enchantment tension  -  Venus charm pulled into deep-water psycho fog.",
        required_markers=["Venus glyph on tail clasp or necklace"],
        optional_props=["tiny rubber duck silhouette"],
        text_overlay_ideas=["potion label blocked"],
        avoid=["horror gore", "explicit fetish"],
        short_prompt_line="Mermaid Venus in cauldron inset  -  bubbles, fish; Neptune/Pluto rim tension.",
    ),
    "venus_fashion_boss_pressure": CatstyleSceneTemplate(
        template_key="venus_fashion_boss_pressure",
        display_name="Venus Fashion Boss Pressure",
        compatible_pairs=[
            ("Venus", "Pluto"),
            ("Pluto", "Venus"),
            ("Venus", "Saturn"),
            ("Saturn", "Venus"),
        ],
        compatible_aspects=["square", "opposition"],
        compatible_skins=None,
        energy="charged",
        primary_action=(
            "Editorial runway glare  -  Venus controls spotlight wand while Pluto/Saturn cat submits nervously; "
            "luxury fashion pressure tableau with stark silhouette posters behind (blank)."
        ),
        composition="Strong verticals  -  backstage truss mimicking Saturn ribs or Pluto smoke pillars.",
        camera_angle="Frontal poster lens with slight worm-eye exaggeration.",
        foreground_elements="Clipboards blank, rack of monochrome cloaks as shapes.",
        background_elements="Arena sky darkened like backstage void.",
        emotional_read="Power-beauty negotiation turning tense  -  original staging only.",
        required_markers=["Venus glyph on buckle or earring"],
        optional_props=["handheld spotlight cone"],
        text_overlay_ideas=["magazine cover blocked"],
        avoid=["copying specific movie poster compositions", "readable brand logos"],
        short_prompt_line="Fashion boss Venus vs Pluto/Saturn tension  -  runway glare, editorial control metaphor.",
    ),
    "venus_couture_harmony": CatstyleSceneTemplate(
        template_key="venus_couture_harmony",
        display_name="Venus Couture Harmony",
        compatible_pairs=[
            ("Venus", "Saturn"),
            ("Saturn", "Venus"),
        ],
        compatible_aspects=["trine", "sextile"],
        compatible_skins=None,
        energy="supportive",
        primary_action=(
            "Shared tailoring beat  -  Saturn pins hem while Venus drapes fabric; cooperative couture fitting moment "
            "on arena disc."
        ),
        composition="Mirrored poses forming heart-negative space between bodies.",
        camera_angle="Straight-on symmetrical comic panel.",
        foreground_elements="Mannequin cat bust, chalk tailor markings.",
        background_elements="Soft star curtain.",
        emotional_read="Disciplined luxury friendship  -  tasteful, calm.",
        required_markers=["both Venus and Saturn glyphs visible as accessories"],
        optional_props=["measuring tape loop"],
        text_overlay_ideas=["atelier sign blocked"],
        avoid=["cold villain Saturn cliché without warmth"],
        short_prompt_line="Supportive Saturn + Venus couture harmony  -  co-tailoring on cosmic runway disc.",
    ),
    "pluto_tricycle_showdown": CatstyleSceneTemplate(
        template_key="pluto_tricycle_showdown",
        display_name="Pluto Tricycle Showdown",
        compatible_pairs=[
            ("Pluto", "Mars"),
            ("Mars", "Pluto"),
            ("Pluto", "Venus"),
            ("Venus", "Pluto"),
        ],
        compatible_aspects=["square", "opposition"],
        compatible_skins=None,
        energy="charged",
        primary_action=(
            "Tiny Pluto planet-cat on absurd micro-tricycle rolling foreground  -  hypnotic spiral pupils dominating "
            "frame while Mars/Venus reels backward comic stagger."
        ),
        composition="Forced perspective makes trike monumental shadow.",
        camera_angle="Low creep comic angle emphasizing oversized eyes.",
        foreground_elements="Smoke puffs from trike bell, spiral glare overlays.",
        background_elements="Arena rim bends like hypnosis ring.",
        emotional_read="Creepy-comic dominance  -  laugh-first horror cues.",
        required_markers=["Pluto glyph on trike hubcap"],
        optional_props=["tin horn squeak lines"],
        text_overlay_ideas=["hypnosis spiral FX blocked"],
        avoid=["realistic child peril", "gore"],
        short_prompt_line="Pluto on tiny trike  -  spiral eyes, comic creep dominance vs Mars/Venus stumble.",
    ),
    "pluto_cauldron_control": CatstyleSceneTemplate(
        template_key="pluto_cauldron_control",
        display_name="Pluto Cauldron Control",
        compatible_planets=["Pluto"],
        compatible_aspects=["square", "opposition", "conjunction"],
        compatible_skins=None,
        energy="balanced",
        primary_action="Pluto stirs towering cauldron fog  -  transformation/alchemy control gesture facing partner cat.",
        composition="Spiral steam ties both cats; Pluto occupies leverage corner.",
        camera_angle="Over-shoulder from partner toward bubbling glow.",
        foreground_elements="Ladle drip arcs, glyph sparks.",
        background_elements="Arena sky swallowed by smoke donut.",
        emotional_read="Spellbound negotiation  -  power through subtle menace.",
        required_markers=["Pluto glyph etched on cauldron lip"],
        optional_props=["glass orb bobbing"],
        text_overlay_ideas=["recipe parchment blocked"],
        avoid=["body horror", "readable spells"],
        short_prompt_line="Pluto stirring arena cauldron  -  smoke control, transformation staging.",
    ),
    "saturn_tower_captivity": CatstyleSceneTemplate(
        template_key="saturn_tower_captivity",
        display_name="Saturn Tower Captivity",
        compatible_pairs=[
            ("Saturn", "Venus"),
            ("Venus", "Saturn"),
            ("Saturn", "Moon"),
            ("Moon", "Saturn"),
        ],
        compatible_aspects=["square", "opposition"],
        compatible_skins=None,
        energy="charged",
        primary_action=(
            "Thin cosmic tower prism rises from arena floor  -  Venus/Moon cat visible behind simplified barred window "
            "silhouette while Saturn cat guards spiral staircase outer rim."
        ),
        composition="Vertical tower split framing emotional distance.",
        camera_angle="Mild widescreen cinematic panel.",
        foreground_elements="Chains as balloon circles, key halo prop.",
        background_elements="Soft storms brushing zodiac ring.",
        emotional_read="Delayed longing / captivity trope  -  original fairy-tone comic mood.",
        required_markers=["Saturn ring silhouette echo on tower moldings"],
        optional_props=["hourglass prop"],
        text_overlay_ideas=["tower window glow blocked"],
        avoid=["grim torture imagery", "readable signage"],
        short_prompt_line="Saturn tower captivity beat  -  Venus/Moon behind bars silhouette; Saturn sentinel rim.",
    ),
    "saturn_couture_architect": CatstyleSceneTemplate(
        template_key="saturn_couture_architect",
        display_name="Saturn Couture Architect",
        compatible_pairs=[
            ("Saturn", "Venus"),
            ("Venus", "Saturn"),
        ],
        compatible_aspects=["trine", "sextile", "square"],
        compatible_skins=None,
        energy="supportive",
        primary_action=(
            "Saturn in tailored architect skin drafts glowing blueprint lines in air while Venus aligns accessory racks  -  "
            "structured elegance handshake beat."
        ),
        composition="Ortho-grid ghost lines overlay arena floor like tempered glass.",
        camera_angle="Slight overhead drafting-table vibe.",
        foreground_elements="T-square hovers, marble pedestal cubes.",
        background_elements="Constellation grid aligning zodiac ring geometry.",
        emotional_read="Old-money discipline meets Venus refinement cooperatively.",
        required_markers=["Saturn glyph cufflink", "Venus glyph brooch"],
        optional_props=["ring-hoop belt echo"],
        text_overlay_ideas=["floor plan blocked"],
        avoid=["readable blueprints", "brand marks"],
        short_prompt_line="Saturn architect + Venus styling  -  cooperative geometry couture on arena plane.",
    ),
    "uranus_electric_wind_burst": CatstyleSceneTemplate(
        template_key="uranus_electric_wind_burst",
        display_name="Uranus Electric Wind Burst",
        compatible_pairs=[
            ("Uranus", "Venus"),
            ("Venus", "Uranus"),
            ("Uranus", "Moon"),
            ("Moon", "Uranus"),
        ],
        compatible_aspects=["square", "opposition"],
        compatible_skins=None,
        energy="charged",
        primary_action=(
            "Uranus cat summons sideways portal gust  -  electric wind ribbons shred curtains/fabrics around Venus/Moon "
            "while both cling to arena tether poles."
        ),
        composition="Z-axis lightning forks bracket dress chaos.",
        camera_angle="Diagonal upward chase cam.",
        foreground_elements="Zigzag neon ribbons, hair tufts standing cartoon spikes.",
        background_elements="Split sky contrasting calm vs storm wedge.",
        emotional_read="Comfort disruption slapstick  -  sudden Uranian honesty gust.",
        required_markers=["Uranus lightning bolt glyph shoulder patch"],
        optional_props=["broken umbrella silhouette"],
        text_overlay_ideas=["storm warning icon blocked"],
        avoid=["real lightning photography"],
        short_prompt_line="Uranus electric portal gust vs Venus/Moon fabrics  -  zigzag neon arena staging.",
    ),
    "uranus_rebel_icon_poster": CatstyleSceneTemplate(
        template_key="uranus_rebel_icon_poster",
        display_name="Uranus Rebel Icon Poster",
        compatible_planets=["Uranus"],
        compatible_aspects=["square", "opposition", "conjunction"],
        compatible_skins=None,
        energy="charged",
        primary_action=(
            "Posterized Uranus cat raises paw like revolutionary icon  -  electric halo stencil behind (abstract); "
            "partner planet reacts from lower third crowd silhouette shapes."
        ),
        composition="Centered propaganda poster geometry inside arena billboard frame.",
        camera_angle="Straight-on lithograph flatness with subtle fisheye.",
        foreground_elements="Spray-paint confetti blocks, star stencil torn edges.",
        background_elements="Duotone clouds clash cosmic void.",
        emotional_read="Disruptive charisma  -  punk optimism.",
        required_markers=["Uranus bolt glyph crown"],
        optional_props=["megaphone cone blank"],
        text_overlay_ideas=["poster slogan blocked"],
        avoid=["copying Che composition", "readable protest signs"],
        short_prompt_line="Uranus rebel poster stance  -  raised paw electric halo; arena billboard comic.",
    ),
    "neptune_fog_illusion_stage": CatstyleSceneTemplate(
        template_key="neptune_fog_illusion_stage",
        display_name="Neptune Fog Illusion Stage",
        compatible_planets=["Neptune"],
        compatible_aspects=["square", "opposition", "conjunction"],
        compatible_skins=None,
        energy="balanced",
        primary_action=(
            "Neptune runs fog-machine illusion stage  -  fish puppets on sticks, bubble curtains, partner cat squints "
            "through haze trying to spot real Neptune."
        ),
        composition="Layered translucent fog planes alternating silhouette reads.",
        camera_angle="Front-row theater slight low angle.",
        foreground_elements="Soap bubble clusters, fish cutouts.",
        background_elements="Spotlights as soft cones through smoke.",
        emotional_read="Mesmerizing variety show  -  comic confusion.",
        required_markers=["Neptune trident simplified as toy"],
        optional_props=["magician cape with blank crest"],
        text_overlay_ideas=["marquee blocked"],
        avoid=["drug metaphor", "explicit hypnosis spiral overload"],
        short_prompt_line="Neptune fog illusion stage  -  fish puppets, bubbles, theatrical smoke on arena deck.",
    ),
    "neptune_mermaid_dream": CatstyleSceneTemplate(
        template_key="neptune_mermaid_dream",
        display_name="Neptune Mermaid Dream",
        compatible_pairs=[
            ("Neptune", "Venus"),
            ("Venus", "Neptune"),
        ],
        compatible_aspects=["square", "opposition", "trine"],
        compatible_skins=None,
        energy="supportive",
        primary_action=(
            "Soft ocean dream tableau  -  Neptune tail braid wraps Venus gently while bioluminescent plankton dots arena "
            "floor like projector lights."
        ),
        composition="Circular embrace staged inside ripple halo.",
        camera_angle="Gentle overhead butterfly shot.",
        foreground_elements="Drifting kelp ribbons, sleepy fish buddies.",
        background_elements="Pastel aurora curtains blending zodiac ring pastel wash.",
        emotional_read="Illusionary lure turned nurturing dream.",
        required_markers=["Neptune glyph on tail scales pattern", "Venus glyph necklace"],
        optional_props=["tiny shell boom mic"],
        text_overlay_ideas=["lullaby notes blocked"],
        avoid=["sinister siren horror"],
        short_prompt_line="Neptune + Venus soft mermaid dream duet  -  bioluminescent cosmic tide pool arena inset.",
    ),
}


def normalize_scene_template_key(raw: str) -> str:
    key = (raw or "").strip().lower().replace("-", "_")
    if key not in SCENE_TEMPLATES:
        known = ", ".join(sorted(SCENE_TEMPLATES))
        raise ValueError(f"Unknown Catstyle scene template {raw!r}. Known keys: {known}.")
    return key


def get_scene_template(template_key: str) -> CatstyleSceneTemplate:
    return SCENE_TEMPLATES[normalize_scene_template_key(template_key)]


def list_scene_templates() -> list[CatstyleSceneTemplate]:
    return [SCENE_TEMPLATES[k] for k in sorted(SCENE_TEMPLATES)]


def format_scene_template_prompt_block(st: CatstyleSceneTemplate) -> str:
    markers = "; ".join(st.required_markers) if st.required_markers else "(identity defaults)"
    props = "; ".join(st.optional_props) if st.optional_props else "none"
    avoid = " | ".join(st.avoid) if st.avoid else "none"
    overlays = "; ".join(st.text_overlay_ideas) if st.text_overlay_ideas else "none"
    return (
        f"[SCENE TEMPLATE v1 - high-priority frame direction] {st.template_key} ({st.display_name}): "
        f"Primary action: {st.primary_action} "
        f"Composition: {st.composition} "
        f"Camera: {st.camera_angle} "
        f"Foreground: {st.foreground_elements} "
        f"Background: {st.background_elements} "
        f"Emotional read: {st.emotional_read} "
        f"Required markers: {markers}. "
        f"Important props: {props}. "
        f"Text overlay ideas (do not render text): {overlays}. "
        f"Avoid: {avoid}. "
        f"Compact cue: {st.short_prompt_line}"
    )


def _pair_matches_template(t: CatstyleSceneTemplate, pair: set[str]) -> bool:
    if t.compatible_pairs:
        for a, b in t.compatible_pairs:
            if {canon_normalize_planet_name(a), canon_normalize_planet_name(b)} == pair:
                return True
        return False
    if t.compatible_planets:
        need = {canon_normalize_planet_name(p) for p in t.compatible_planets}
        return need.issubset(pair)
    return False


def _aspect_ok(t: CatstyleSceneTemplate, aspect_type: str | None) -> bool:
    if t.compatible_aspects is None:
        return True
    asp = (aspect_type or "").strip().lower()
    return asp in {x.lower() for x in t.compatible_aspects}


def scene_template_compatible_with_context(
    t: CatstyleSceneTemplate,
    planet_a: str,
    planet_b: str,
    aspect_type: str | None,
) -> bool:
    pa = canon_normalize_planet_name(planet_a)
    pb = canon_normalize_planet_name(planet_b)
    pair = {pa, pb}
    return _pair_matches_template(t, pair) and _aspect_ok(t, aspect_type)


def validate_explicit_scene_template(
    template_key: str,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
) -> CatstyleSceneTemplate:
    st = get_scene_template(template_key)
    if not scene_template_compatible_with_context(st, planet_a, planet_b, aspect_type):
        pa = canon_normalize_planet_name(planet_a)
        pb = canon_normalize_planet_name(planet_b)
        raise ValueError(
            f"Scene template {template_key!r} is incompatible with {pa}+{pb} aspect {aspect_type!r}. "
            "Pick another scene template or adjust planets/aspect."
        )
    return st


def _score_scene_rank(
    t: CatstyleSceneTemplate,
    planet_a: str,
    planet_b: str,
    aspect_type: str | None,
    skin_a: str | None,
    skin_b: str | None,
    effective_energy: str,
) -> int | None:
    pa = canon_normalize_planet_name(planet_a)
    pb = canon_normalize_planet_name(planet_b)
    pair = {pa, pb}
    if not _pair_matches_template(t, pair):
        return None
    if not _aspect_ok(t, aspect_type):
        return None

    skins_applied: set[str] = set()
    for sk in (skin_a, skin_b):
        if sk:
            skins_applied.add(normalize_skin_key(sk))

    if t.compatible_pairs:
        pair_rank = 400
    elif t.compatible_planets:
        pair_rank = 300
    else:
        return None

    asp_rank = 200 if t.compatible_aspects is not None else 100

    if t.compatible_skins is not None:
        want = {normalize_skin_key(x) for x in t.compatible_skins}
        skin_rank = 150 if bool(skins_applied & want) else 0
    else:
        skin_rank = 75

    en = (effective_energy or "balanced").strip().lower()
    if t.energy == en:
        energy_rank = 50
    elif t.energy == "balanced":
        energy_rank = 25
    else:
        energy_rank = 0

    return pair_rank + asp_rank + skin_rank + energy_rank


def find_scene_templates_for_context(
    planet_a: str,
    planet_b: str,
    aspect_type: str | None = None,
    skin_a: str | None = None,
    skin_b: str | None = None,
    editorial_profile: str | None = None,
    energy: str | None = None,
    *,
    mode: str = "tension",
) -> list[CatstyleSceneTemplate]:
    """Return compatible scene templates sorted by deterministic rank (desc), then template_key."""
    pa = canon_normalize_planet_name(planet_a)
    pb = canon_normalize_planet_name(planet_b)
    eff = (energy or "").strip().lower() or resolve_art_energy(editorial_profile, mode)

    scored: list[tuple[int, str, CatstyleSceneTemplate]] = []
    for key in sorted(SCENE_TEMPLATES):
        t = SCENE_TEMPLATES[key]
        rank = _score_scene_rank(t, pa, pb, aspect_type, skin_a, skin_b, eff)
        if rank is None:
            continue
        scored.append((rank, key, t))

    scored.sort(key=lambda row: (-row[0], row[1]))
    return [t for _, _, t in scored]


__all__ = [
    "SCENE_TEMPLATES",
    "find_scene_templates_for_context",
    "format_scene_template_prompt_block",
    "get_scene_template",
    "list_scene_templates",
    "normalize_scene_template_key",
    "scene_template_compatible_with_context",
    "validate_explicit_scene_template",
]
