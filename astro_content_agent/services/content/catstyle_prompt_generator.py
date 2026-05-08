"""Generate Catstyle v0 image prompt packs (text only; no image API calls)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.aspect_library_v0 import ASPECT_CAT_INTERACTIONS, get_aspect_interaction
from astro_content_agent.content.catstyle.character_skins_v0 import get_character_skin
from astro_content_agent.content.catstyle.hero_shots_v1 import (
    format_hero_shot_prompt_block,
    shot_roles_for_variant_indices,
)
from astro_content_agent.content.catstyle.models import (
    CatstylePromptPack,
    CatstylePromptRequest,
    CatstyleRenderStyleProfile,
    PlanetCatCanon,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import (
    get_planet_canon,
    normalize_planet_name as canon_normalize_planet_name,
)
from astro_content_agent.content.catstyle.planet_canon import (
    build_planet_canon_prompt_fragment,
    get_planet_canon as get_planet_canon_v2,
)
from astro_content_agent.content.catstyle.planet_identity_markers_v1 import (
    format_identity_markers_prompt_block,
    get_planet_identity_marker_profile,
)
from astro_content_agent.content.catstyle.scene_templates_v1 import (
    format_scene_template_prompt_block,
    validate_explicit_scene_template,
)
from astro_content_agent.content.catstyle.render_style_profiles_v1 import (
    DEFAULT_RENDER_STYLE_PROFILE_KEY,
    format_render_style_prompt_block,
    get_render_style_profile,
)
from astro_content_agent.content.catstyle.world_templates_v1 import (
    DEFAULT_WORLD_TEMPLATE_KEY,
    format_world_template_prompt_block,
    get_world_template,
)
from astro_content_agent.services.content.catstyle_art_direction import (
    apply_art_direction_to_prompt_pack,
    build_catstyle_art_direction_profile,
    resolve_art_energy,
)
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import (
    CatstyleTransitPairSeed,
    get_transit_pair_seed,
    orient_outer_personal,
)

_CATSTYLE_SUBJECT_GUARDS = (
    "Planet-cats keep rounded comic-body proportions with expressive theatrical faces and silhouette-first readability "
    "at thumbnail scale; follow each character's locked canon and identity-marker blocks below. "
    "No text in image, no logos, no brands."
)

_NEGATIVE_BASE_CHUNKS = [
    "text, words, letters, captions, watermarks, logos, trademarks, QR codes",
    "photorealistic, hyperreal skin, photoreal materials, HDR glossy",
    "3D CGI figurine finish, game splash render look, game-engine shading",
    "microtexture noise, tiny crack noise, excess particles clutter",
    "childish nursery style, kawaii, chibi, sticker mascot style",
    "flat vector icon, mobile-game icon look, simplistic educational cartoon",
    "cluttered architecture detail spam, busy background clutter, weak bland composition",
    "disconnected sticker posing, over-rendered fur strands, over-rendered material noise",
]


def _image_prompt_lead(render_prof: CatstyleRenderStyleProfile) -> str:
    """Opening sentences: render-profile priority before canon/world/scene (must not contradict premium finish)."""
    return f"{render_prof.image_prompt_opening_line.strip()} {_CATSTYLE_SUBJECT_GUARDS}".strip()


def _image_prompt_opening_prefix(render_prof: CatstyleRenderStyleProfile) -> str:
    """Opening lead plus optional v2 style-hardlock mandate (deterministic, highest priority before Aspect line)."""
    base = _image_prompt_lead(render_prof)
    hb = render_prof.style_hardlock_block
    if hb and str(hb).strip():
        return f"{base} [STYLE HARDLOCK v2 - premium poster mandate] {hb.strip()}".strip()
    return base


def _aspect_choreography_block(aspect_type: str) -> str:
    """Deterministic aspect choreography: hard aspects clash; soft aspects cooperate (Catstyle v1)."""
    k = (aspect_type or "").strip().lower()
    mapping: dict[str, str] = {
        "square": (
            "[ASPECT CHOREOGRAPHY v1 - square] Active angular conflict on the zodiac arena: friction, strike/counterstrike, "
            "tense collision beats; keep conflict readable at poster scale but each planet expresses force through its own "
            "planetary physics—never generic MMA."
        ),
        "opposition": (
            "[ASPECT CHOREOGRAPHY v1 - opposition] Face-off polarity on the arena rim: mirrored duel tension, push-pull, "
            "two poles leaning into each other with reversible momentum."
        ),
        "trine": (
            "[ASPECT CHOREOGRAPHY v1 - trine] Smooth cooperative flow: dance-like harmony, synchronized movement, "
            "shared rhythm choreography."
        ),
        "sextile": (
            "[ASPECT CHOREOGRAPHY v1 - sextile] Playful cooperation: light coordinated exchange, quick friendly assists, "
            "sparkling back-and-forth without harsh clash."
        ),
        "conjunction": (
            "[ASPECT CHOREOGRAPHY v1 - conjunction] Merged fused force: combined amplification, stacked silhouettes, "
            "single-forward surge choreography."
        ),
    }
    return mapping.get(k, "")


def _aspect_choreography_animation_clause(aspect_type: str) -> str:
    """Short animation bias aligned with major-aspect choreography."""
    k = (aspect_type or "").strip().lower()
    mapping: dict[str, str] = {
        "square": "Choreography bias: angular friction, strike/counterstrike readability (planet-specific). ",
        "opposition": "Choreography bias: mirrored face-off, push-pull polarity. ",
        "trine": "Choreography bias: smooth synchronized flow and cooperative rhythm. ",
        "sextile": "Choreography bias: playful coordinated assists and light exchange. ",
        "conjunction": "Choreography bias: fused amplification and merged-forward motion. ",
    }
    return mapping.get(k, "")


def _planet_pair_action_language(pa: str, pb: str) -> str:
    """Planet-specific allowed action lexicon (Moon/Saturn explicit for choreography v1)."""
    pair = {pa.strip().lower(), pb.strip().lower()}
    chunks: list[str] = []
    if "moon" in pair:
        chunks.append(
            "[PLANETARY ACTION LEXICON v1 - Moon] Prefer: pillow strike, moonlight wave, protective defensive motion, "
            "tidal push, emotional flinch/retreat/burst—soft but active movement."
        )
    if "saturn" in pair:
        chunks.append(
            "[PLANETARY ACTION LEXICON v1 - Saturn] Prefer: stone block, freeze/frost field, gravity press, chain bind, "
            "gate slam, ruler strike as measuring/architect line (not a blade swing), wall summon, stop gesture, time lock, "
            "heavy downward force. Saturn may fight hard through barriers/time/weight—never as fiery reckless Mars: "
            "no flames, no fire aura, no ninja/fighter styling, no martial-arts choreography, no reckless attack pose, "
            "no Mars-like aggression, no nunchucks/martial weapons."
        )
    return " ".join(chunks).strip()


def _mars_heavy_scene_style_decouple_block(req: CatstylePromptRequest, pa: str, pb: str) -> str:
    """Mars-named scene or Mars-heavy reference finisher on a non-Mars pair: anchor finish only—not Mars combat behavior."""
    if "mars" in {pa.strip().lower(), pb.strip().lower()}:
        return ""
    raw = (req.scene_template_key or "").strip().lower()
    mars_named_scene = bool(raw.startswith("mars_"))
    if not mars_named_scene and not req.mars_heavy_style_reference_finisher:
        return ""
    return (
        "[MARS-HEAVY STYLE REFERENCE DECOUPLING v1] This Mars-forward scene template or Mars-heavy reference may anchor "
        "finish quality only for these non-Mars planet-cats: inherit polish, line weight, lighting rhythm, and poster composition "
        "ONLY—do NOT import Mars choreography, sparks/flames, brawling, explosive kicks, savage duel posing, or combat staging onto "
        "these characters."
    )


def _animation_prompt_body(
    pa: str,
    pb: str,
    aspect_type: str,
    anim_skin: str,
    render_prof: CatstyleRenderStyleProfile,
) -> str:
    """Loop prompt aligned with the same render finish as still frames (no legacy flat-cartoon lead-in)."""
    prefix = _image_prompt_opening_prefix(render_prof)
    choreo_anim = _aspect_choreography_animation_clause(aspect_type)
    return (
        f"{prefix} "
        f"Loopable 3–5s animation: {pa} and {pb} planet-cats, aspect {aspect_type}; {choreo_anim}"
        f"minimal squash-and-stretch "
        f"preserving silhouette reads; outlines stay crisp at loop resolution; environment honors locked world/scene "
        f"when applicable (otherwise restrained cosmic void is acceptable); readable comic timing.{anim_skin}"
    ).strip()

def normalize_planet_name(name: str) -> str:
    """Canonical planet title (delegates to planet canon v1)."""
    return canon_normalize_planet_name(name)


def _strip_optional_skin(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _strip_optional_str(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _join_world_scene_middle(world_block: str, scene_block: str) -> str:
    parts = [p.strip() for p in (world_block, scene_block) if p and str(p).strip()]
    if not parts:
        return ""
    return " ".join(parts) + " "


def _resolve_world_scene_blocks(
    req: CatstylePromptRequest, pa: str, pb: str
) -> tuple[str, str, dict | None, dict | None]:
    scene_energy = resolve_art_energy(req.editorial_profile, req.mode)
    raw_w = _strip_optional_str(req.world_template_key)
    wt = None
    if raw_w:
        wt = get_world_template(raw_w)
    elif req.premium_art_direction:
        wt = get_world_template(DEFAULT_WORLD_TEMPLATE_KEY)

    world_block = format_world_template_prompt_block(wt, scene_energy=scene_energy) if wt else ""
    world_prof = wt.model_dump(mode="json") if wt else None

    raw_s = _strip_optional_str(req.scene_template_key)
    scene_block = ""
    scene_prof = None
    if raw_s:
        st = validate_explicit_scene_template(raw_s, pa, pb, req.aspect_type)
        scene_block = format_scene_template_prompt_block(st)
        scene_prof = st.model_dump(mode="json")

    return world_block, scene_block, world_prof, scene_prof


def _attach_template_profiles(
    pack: CatstylePromptPack,
    *,
    world_template_profile: dict | None,
    scene_template_profile: dict | None,
    render_style_profile: dict | None,
) -> CatstylePromptPack:
    data = pack.model_dump(mode="json")
    data["world_template_profile"] = world_template_profile
    data["scene_template_profile"] = scene_template_profile
    data["render_style_profile"] = render_style_profile
    return CatstylePromptPack.model_validate(data)


def _dedupe_negative_phrases(phrases: list[str]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for phrase in phrases:
        raw = phrase.strip()
        if not raw:
            continue
        norm = " ".join(raw.lower().split())
        if norm in seen:
            continue
        seen.add(norm)
        ordered.append(raw)
    return ", ".join(ordered)


def _merge_negative_prompt(base_comma_chunks: list[str], extra_phrases: list[str]) -> str:
    pieces: list[str] = []
    for chunk in base_comma_chunks:
        for part in chunk.split(","):
            t = part.strip()
            if t:
                pieces.append(t)
    for phrase in extra_phrases:
        t = phrase.strip()
        if t:
            pieces.append(t)
    return _dedupe_negative_phrases(pieces)


def _resolve_render_style(req: CatstylePromptRequest):
    raw = (req.render_style_profile_key or "").strip()
    key = raw or DEFAULT_RENDER_STYLE_PROFILE_KEY
    profile = get_render_style_profile(key)
    render_middle = format_render_style_prompt_block(profile).strip() + " "
    return profile, profile.model_dump(mode="json"), render_middle


def _validate_skins_for_pair(pa: str, pb: str, skin_a: str | None, skin_b: str | None) -> None:
    if skin_a:
        get_character_skin(pa, skin_a)
    if skin_b:
        get_character_skin(pb, skin_b)


def _planet_cat_line(planet: str, canon: PlanetCatCanon, skin_key: str | None) -> str:
    sk_raw = _strip_optional_skin(skin_key)
    marker = get_planet_identity_marker_profile(planet)
    marker_block = format_identity_markers_prompt_block(planet, marker, has_skin=bool(sk_raw))
    canon_v2 = get_planet_canon_v2(planet)
    canon_v2_block = build_planet_canon_prompt_fragment(planet)
    must_have = " | ".join(canon_v2.must_have)
    must_not = " | ".join(canon_v2.must_not_have)
    base = (
        f"{planet} planet-cat [CANON v1 base]: {canon.short_prompt_line} "
        f"This block is the immutable planet identity — keep recognizable across every scene and skin. "
        f"Archetype: {canon.role_archetype} "
        f"Silhouette: {canon.silhouette_notes} "
        f"Shape language: {canon.core_shape_language} "
        f"Palette: {canon.core_palette} "
        f"Face: {canon.facial_expression_language} "
        f"Body: {canon.body_language} "
        f"Signature props: {canon.signature_props} "
        f"Signature details: {canon.signature_details} "
        f"Emotional tone: {canon.emotional_tone} "
        f"Motion style: {canon.motion_style} "
        f"Visual priorities: {canon.visual_do} "
        f"Visual avoid: {canon.visual_avoid} "
        f"Recognizability rule: {canon.recognizability_rule} "
        f"{canon_v2_block} "
        f"{planet} must-have traits lock: {must_have} "
        f"{planet} must-not traits lock: {must_not}"
    )
    base_with_markers = f"{base} {marker_block}"
    if not sk_raw:
        return base_with_markers
    sk = get_character_skin(planet, sk_raw)
    overlay = (
        f" Archetype skin **{sk.display_name}** (OPTIONAL COSTUME OVERLAY ONLY — preserve the full [CANON v1 base] "
        f"and [IDENTITY MARKERS v1] sections above: same planet, base silhouette, glyphs/placement cues, "
        f"signature props/details, and recognizability rule must remain readable; "
        f"skin enhances costume/scene hooks, never replaces the planet-cat core): "
        f"costume: {sk.costume_elements}. Props: {sk.prop_elements}. Body language: {sk.body_language}. "
        f"Scene hooks: {sk.scene_hooks}. Skin signature details: {sk.signature_details}. "
        f"Avoid for this skin: {sk.avoid_elements}."
    )
    return base_with_markers + overlay


def _moon_saturn_visual_correction_block(pa: str, pb: str, aspect_type: str, mode: str) -> str:
    """Moon square Saturn: arena-readable clash where Moon stays soft-force and Saturn stays structural—not Mars combat."""
    pair = {pa.lower(), pb.lower()}
    if pair != {"moon", "saturn"}:
        return ""
    if (aspect_type or "").strip().lower() != "square":
        return ""
    if (mode or "").strip().lower() != "tension":
        return ""
    return (
        "[MOON-SATURN VISUAL CORRECTION PATCH v1 - mandatory identity guard] "
        "Dynamic zodiac-arena conflict is OK here: this is softness versus structure, not a generic action-hero brawl or soft cat versus fire ninja. "
        "Moon attacks/defends with pillow strikes, moonlight waves, tidal pushes, protective defensive motion, emotional "
        "flinch/retreat/burst—soft but active force; Moon stays rounded, vulnerable, comfort-seeking, silver-lit, clutching pillow/blanket/soft cloth; "
        "may glance toward a small glowing cozy doorway/window as memory of past comfort. "
        "Saturn counters with stone blocks, freeze/frost fields, gravity presses, chain binds, gate slams, wall summons, stop gesture, "
        "time-lock, ruler-as-measure strike, heavy downward structural force—cold stone-and-iron judge/architect/guardian energy; upright, severe, emotionally reserved. "
        "Scene metaphor: a heavy stone gate of time and responsibility blocks the way back to comfort while Moon presses with soft waves. "
        "Checkpoint imagery: stone gate/wall/tower, chain, clock boundary line; Saturn props like ruler, key, hourglass, blank watch, architectural plan. "
        "Composition target: premium cinematic comic poster, strong silhouettes, dramatic arena-readable pressure via symbolism (not MMA). "
        "Palette target: cold stone-and-silver dominant palette with controlled warm memory glow only in background comfort cue. "
        "Saturn critical negatives: do NOT depict Saturn with flames, fire aura, martial weapons, ninja/fighter styling, "
        "reckless attack pose, reckless speed, or Mars-like aggression; do NOT let Saturn inherit Mars visual traits. "
        "Whole-scene hard negatives: no martial-arts duel choreography, no body-on-body brawl, no nunchucks; "
        "not cute nursery, not flat mascot, not 3D CGI figurine, not game render look. "
        "Read: Moon softer/more emotionally defensive, Saturn still/imposing/limiting through mass and time; vulnerability vs discipline."
    )


def _prompt_choreography_middleware(
    req: CatstylePromptRequest, pa: str, pb: str, pair_guard: str
) -> str:
    """Aspect choreography + optional planet lexicon + Mars scene decouple; Moon/Saturn square adds dedicated guard."""
    blocks = [
        _aspect_choreography_block(req.aspect_type),
        _planet_pair_action_language(pa, pb),
        _mars_heavy_scene_style_decouple_block(req, pa, pb),
        pair_guard,
    ]
    return " ".join(b for b in blocks if b).strip()


def _skin_animation_suffix(pa: str, pb: str, skin_a: str | None, skin_b: str | None) -> str:
    parts: list[str] = []
    if skin_a:
        sk = get_character_skin(pa, skin_a)
        parts.append(f"{pa} in {sk.display_name} skin")
    if skin_b:
        sk = get_character_skin(pb, skin_b)
        parts.append(f"{pb} in {sk.display_name} skin")
    if not parts:
        return ""
    return " Archetype overlays: " + "; ".join(parts) + "."


def _skin_carousel_suffix(skin_a: str | None, skin_b: str | None) -> str:
    if not skin_a and not skin_b:
        return ""
    return " Honor optional archetype skins on labeled planet-cats where specified (still Catstyle round bodies)."


def _supported_pairs_hint() -> str:
    deep = [" + ".join(sorted(k, key=str.lower)) for k in ASPECT_CAT_INTERACTIONS]
    return "Deep aspect library: " + "; ".join(sorted(deep)) + ". Plus 25 social/outer-to-personal transit seeds (transit_pair_seed_v0)."


def _pack_from_deep(
    pa: str,
    pb: str,
    req: CatstylePromptRequest,
    *,
    canon_a: PlanetCatCanon,
    canon_b: PlanetCatCanon,
    aspect_ix,
    skin_a: str | None,
    skin_b: str | None,
    render_prof: CatstyleRenderStyleProfile,
    template_middle: str = "",
    render_middle: str = "",
    render_negative_additions: list[str] | None = None,
) -> CatstylePromptPack:
    tension_scenes = list(aspect_ix.scene_ideas)
    comp_scenes = list(aspect_ix.compensation_scene_ideas)
    n = req.variants_count
    shot_roles = shot_roles_for_variant_indices(n, req.shot_mode)
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
    pair_guard = _moon_saturn_visual_correction_block(pa, pb, req.aspect_type, req.mode)
    choreo_block = _prompt_choreography_middleware(req, pa, pb, pair_guard)
    anim_skin = _skin_animation_suffix(pa, pb, skin_a, skin_b)

    image_prompts: list[str] = []
    for i in range(n):
        if req.mode == "tension":
            base_scene = tension_scenes[i % len(tension_scenes)]
        elif req.mode == "compensation":
            base_scene = comp_scenes[i % len(comp_scenes)]
            if i >= len(comp_scenes):
                base_scene = f"{base_scene} Constructive channel: {aspect_ix.constructive_channel}"
        else:
            pool = tension_scenes + comp_scenes
            base_scene = pool[i % len(pool)]

        shot_blk = format_hero_shot_prompt_block(shot_roles[i])
        shot_middle = (shot_blk + " ") if shot_blk else ""

        prompt = (
            f"{_image_prompt_opening_prefix(render_prof)} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"{choreo_block} "
            f"{template_middle}"
            f"{render_middle}"
            f"{shot_middle}"
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {aspect_ix.core_tension} "
            f"Constructive undertone available: {aspect_ix.constructive_channel}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = _animation_prompt_body(pa, pb, req.aspect_type, anim_skin, render_prof)

    rn = list(render_negative_additions or [])
    negative_prompt = _merge_negative_prompt(_NEGATIVE_BASE_CHUNKS, list(aspect_ix.avoid_list) + rn)

    carousel_idea = (
        f"Carousel outline (cover + {n} art slides): cover shows {pa}+{pb} round cats under stars with clear "
        f"{req.aspect_type} read; slides rotate through the variant scene beats without on-image text; "
        f"final slide leans into constructive channel: {aspect_ix.constructive_channel} "
        f"(props and poses only, catstyle rules unchanged).{_skin_carousel_suffix(skin_a, skin_b)}"
    ).strip()

    return CatstylePromptPack(
        image_prompts=image_prompts,
        animation_prompt=animation_prompt,
        negative_prompt=negative_prompt,
        carousel_idea=carousel_idea,
        image_prompt_shot_roles=shot_roles,
    )


def _pack_from_seed(
    pa: str,
    pb: str,
    req: CatstylePromptRequest,
    *,
    canon_a: PlanetCatCanon,
    canon_b: PlanetCatCanon,
    seed: CatstyleTransitPairSeed,
    skin_a: str | None,
    skin_b: str | None,
    render_prof: CatstyleRenderStyleProfile,
    template_middle: str = "",
    render_middle: str = "",
    render_negative_additions: list[str] | None = None,
) -> CatstylePromptPack:
    tension_scenes = list(seed.suggested_scene_angles)
    comp_scenes = [seed.constructive_channel, seed.visual_metaphor]
    n = req.variants_count
    shot_roles = shot_roles_for_variant_indices(n, req.shot_mode)
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
    pair_guard = _moon_saturn_visual_correction_block(pa, pb, req.aspect_type, req.mode)
    choreo_block = _prompt_choreography_middleware(req, pa, pb, pair_guard)
    anim_skin = _skin_animation_suffix(pa, pb, skin_a, skin_b)

    image_prompts: list[str] = []
    for i in range(n):
        if req.mode == "tension":
            base_scene = tension_scenes[i % len(tension_scenes)]
        elif req.mode == "compensation":
            base_scene = comp_scenes[i % len(comp_scenes)]
            if i >= len(comp_scenes):
                base_scene = f"{base_scene} Constructive channel: {seed.constructive_channel}"
        else:
            pool = tension_scenes + comp_scenes
            base_scene = pool[i % len(pool)]

        shot_blk = format_hero_shot_prompt_block(shot_roles[i])
        shot_middle = (shot_blk + " ") if shot_blk else ""

        prompt = (
            f"{_image_prompt_opening_prefix(render_prof)} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"{choreo_block} "
            f"{template_middle}"
            f"{render_middle}"
            f"{shot_middle}"
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {seed.core_tension} "
            f"Constructive undertone available: {seed.constructive_channel} "
            f"Visual metaphor: {seed.visual_metaphor}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = _animation_prompt_body(pa, pb, req.aspect_type, anim_skin, render_prof)

    rn = list(render_negative_additions or [])
    negative_prompt = _merge_negative_prompt(_NEGATIVE_BASE_CHUNKS, list(seed.avoid) + rn)

    carousel_idea = (
        f"Carousel outline (cover + {n} art slides): cover shows {pa}+{pb} round cats under stars with clear "
        f"{req.aspect_type} read; slides rotate through transit seed v0 scene angles without on-image text; "
        f"final slide leans into constructive channel: {seed.constructive_channel} "
        f"(props and poses only, catstyle rules unchanged).{_skin_carousel_suffix(skin_a, skin_b)}"
    ).strip()

    return CatstylePromptPack(
        image_prompts=image_prompts,
        animation_prompt=animation_prompt,
        negative_prompt=negative_prompt,
        carousel_idea=carousel_idea,
        image_prompt_shot_roles=shot_roles,
    )


def _pack_from_fallback(
    pa: str,
    pb: str,
    req: CatstylePromptRequest,
    *,
    canon_a: PlanetCatCanon,
    canon_b: PlanetCatCanon,
    outer: str,
    personal: str,
    skin_a: str | None,
    skin_b: str | None,
    render_prof: CatstyleRenderStyleProfile,
    template_middle: str = "",
    render_middle: str = "",
    render_negative_additions: list[str] | None = None,
) -> CatstylePromptPack:
    core = f"{outer} social rhythm meets {personal} everyday stakes—generic transit beat v0 (seed TBD)."
    constructive = f"Shared constructive beat: {outer} and {personal} negotiate one clear cartoon gesture."
    angles = [
        f"{outer} planet-cat looms with simple prop; {personal} planet-cat reacts with one readable emotion.",
        f"{personal} offers one minimal object; {outer} reframes it with one bold silhouette change.",
        "Tug-of-war over a single blank card—no readable text.",
        "Spotlight circle on floor; both cats negotiate rim with deadpan comedy.",
    ]
    tension_scenes = angles
    comp_scenes = [constructive, f"{outer} and {personal} co-build one tiny two-block tower."]
    avoid = ["gore", "real weapons", "readable text in frame", "photorealistic violence"]
    n = req.variants_count
    shot_roles = shot_roles_for_variant_indices(n, req.shot_mode)
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
    pair_guard = _moon_saturn_visual_correction_block(pa, pb, req.aspect_type, req.mode)
    choreo_block = _prompt_choreography_middleware(req, pa, pb, pair_guard)
    anim_skin = _skin_animation_suffix(pa, pb, skin_a, skin_b)

    image_prompts: list[str] = []
    for i in range(n):
        if req.mode == "tension":
            base_scene = tension_scenes[i % len(tension_scenes)]
        elif req.mode == "compensation":
            base_scene = comp_scenes[i % len(comp_scenes)]
            if i >= len(comp_scenes):
                base_scene = f"{base_scene} Constructive channel: {constructive}"
        else:
            pool = tension_scenes + comp_scenes
            base_scene = pool[i % len(pool)]

        shot_blk = format_hero_shot_prompt_block(shot_roles[i])
        shot_middle = (shot_blk + " ") if shot_blk else ""

        prompt = (
            f"{_image_prompt_opening_prefix(render_prof)} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"{choreo_block} "
            f"{template_middle}"
            f"{render_middle}"
            f"{shot_middle}"
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {core} "
            f"Constructive undertone available: {constructive}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = _animation_prompt_body(pa, pb, req.aspect_type, anim_skin, render_prof)

    rn = list(render_negative_additions or [])
    negative_prompt = _merge_negative_prompt(_NEGATIVE_BASE_CHUNKS, avoid + rn)

    carousel_idea = (
        f"Carousel outline (cover + {n} art slides): cover shows {pa}+{pb} round cats under stars with clear "
        f"{req.aspect_type} read; generic outer-to-personal fallback beats; "
        f"final slide leans into: {constructive} (props and poses only).{_skin_carousel_suffix(skin_a, skin_b)}"
    ).strip()

    return CatstylePromptPack(
        image_prompts=image_prompts,
        animation_prompt=animation_prompt,
        negative_prompt=negative_prompt,
        carousel_idea=carousel_idea,
        image_prompt_shot_roles=shot_roles,
    )


def generate_catstyle_prompt_pack(req: CatstylePromptRequest) -> CatstylePromptPack:
    """Build prompts from deep aspect library, transit pair seeds, or generic outer-to-personal fallback."""
    pa = normalize_planet_name(req.planet_a)
    pb = normalize_planet_name(req.planet_b)
    canon_a = get_planet_canon(pa)
    canon_b = get_planet_canon(pb)
    skin_a = _strip_optional_skin(req.skin_a)
    skin_b = _strip_optional_skin(req.skin_b)
    _validate_skins_for_pair(pa, pb, skin_a, skin_b)

    world_block, scene_block, world_prof, scene_prof = _resolve_world_scene_blocks(req, pa, pb)
    template_middle = _join_world_scene_middle(world_block, scene_block)

    render_prof, render_prof_dict, render_middle = _resolve_render_style(req)
    render_neg = list(render_prof.negative_prompt_additions)

    aspect_ix = get_aspect_interaction(pa, pb)
    if aspect_ix is not None:
        pack = _pack_from_deep(
            pa,
            pb,
            req,
            canon_a=canon_a,
            canon_b=canon_b,
            aspect_ix=aspect_ix,
            skin_a=skin_a,
            skin_b=skin_b,
            render_prof=render_prof,
            template_middle=template_middle,
            render_middle=render_middle,
            render_negative_additions=render_neg,
        )
    else:
        oriented = orient_outer_personal(pa, pb)
        if oriented is None:
            raise ValueError(
                f"No Catstyle content for {pa} + {pb}: not a social/outer-to-personal transit pair. {_supported_pairs_hint()}"
            )

        outer, personal = oriented
        seed = get_transit_pair_seed(outer, personal)
        if seed is not None:
            pack = _pack_from_seed(
                pa,
                pb,
                req,
                canon_a=canon_a,
                canon_b=canon_b,
                seed=seed,
                skin_a=skin_a,
                skin_b=skin_b,
                render_prof=render_prof,
                template_middle=template_middle,
                render_middle=render_middle,
                render_negative_additions=render_neg,
            )
        else:
            pack = _pack_from_fallback(
                pa,
                pb,
                req,
                canon_a=canon_a,
                canon_b=canon_b,
                outer=outer,
                personal=personal,
                skin_a=skin_a,
                skin_b=skin_b,
                render_prof=render_prof,
                template_middle=template_middle,
                render_middle=render_middle,
                render_negative_additions=render_neg,
            )

    pack = _attach_template_profiles(
        pack,
        world_template_profile=world_prof,
        scene_template_profile=scene_prof,
        render_style_profile=render_prof_dict,
    )
    return _finalize_pack_with_art_direction(pack, req, pa, pb, skin_a, skin_b)


def _finalize_pack_with_art_direction(
    pack: CatstylePromptPack,
    req: CatstylePromptRequest,
    pa: str,
    pb: str,
    skin_a: str | None,
    skin_b: str | None,
) -> CatstylePromptPack:
    if not req.premium_art_direction:
        return pack
    art_profile = build_catstyle_art_direction_profile(
        editorial_profile=req.editorial_profile,
        mode=req.mode,
        planet_a=pa,
        planet_b=pb,
        skin_a=skin_a,
        skin_b=skin_b,
    )
    return apply_art_direction_to_prompt_pack(pack, art_profile)


__all__ = [
    "generate_catstyle_prompt_pack",
    "normalize_planet_name",
]
