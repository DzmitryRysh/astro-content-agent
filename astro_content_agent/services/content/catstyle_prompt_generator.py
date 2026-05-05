"""Generate Catstyle v0 image prompt packs (text only; no image API calls)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.aspect_library_v0 import ASPECT_CAT_INTERACTIONS, get_aspect_interaction
from astro_content_agent.content.catstyle.character_skins_v0 import get_character_skin
from astro_content_agent.content.catstyle.models import CatstylePromptPack, CatstylePromptRequest, PlanetCatCanon
from astro_content_agent.content.catstyle.planet_canon_v1 import (
    get_planet_canon,
    normalize_planet_name as canon_normalize_planet_name,
)
from astro_content_agent.content.catstyle.planet_identity_markers_v1 import (
    format_identity_markers_prompt_block,
    get_planet_identity_marker_profile,
)
from astro_content_agent.services.content.catstyle_art_direction import (
    apply_art_direction_to_prompt_pack,
    build_catstyle_art_direction_profile,
)
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import (
    CatstyleTransitPairSeed,
    get_transit_pair_seed,
    orient_outer_personal,
)

_STYLE_CORE = (
    "Simple adult-cartoon planet-cats with round bodies, thick black outlines, flat colors, minimal clutter, "
    "expressive deadpan comic faces, dark starry night sky background, clear physical gesture showing "
    "interaction between the two planet-cats. No text in image, no logos, no brands, no realistic rendering, "
    "no anime style, no glossy luxury aesthetic, no excessive jewelry or fine detail clutter."
)

def normalize_planet_name(name: str) -> str:
    """Canonical planet title (delegates to planet canon v1)."""
    return canon_normalize_planet_name(name)


def _strip_optional_skin(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _validate_skins_for_pair(pa: str, pb: str, skin_a: str | None, skin_b: str | None) -> None:
    if skin_a:
        get_character_skin(pa, skin_a)
    if skin_b:
        get_character_skin(pb, skin_b)


def _planet_cat_line(planet: str, canon: PlanetCatCanon, skin_key: str | None) -> str:
    sk_raw = _strip_optional_skin(skin_key)
    marker = get_planet_identity_marker_profile(planet)
    marker_block = format_identity_markers_prompt_block(planet, marker, has_skin=bool(sk_raw))
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
        f"Recognizability rule: {canon.recognizability_rule}"
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
) -> CatstylePromptPack:
    tension_scenes = list(aspect_ix.scene_ideas)
    comp_scenes = list(aspect_ix.compensation_scene_ideas)
    n = req.variants_count
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
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

        prompt = (
            f"{_STYLE_CORE} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {aspect_ix.core_tension} "
            f"Constructive undertone available: {aspect_ix.constructive_channel}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = (
        f"Loopable 3–5s animation, same catstyle: {pa} and {pb} planet-cats, aspect {req.aspect_type}, "
        f"minimal squash-and-stretch on round bodies, thick outlines held crisp at small size, "
        f"dark starry backdrop, readable silhouettes, comic timing;{anim_skin} {_STYLE_CORE}"
    ).strip()

    negative_chunks = [
        "text, words, letters, captions, watermarks, logos, trademarks, QR codes",
        "photorealistic, hyperreal skin, HDR glossy, anime sparkle eyes, luxury product render",
        "crowded background, micro-details, filigree jewelry, chrome liquid, lens flare spam",
    ]
    negative_prompt = ", ".join(negative_chunks + aspect_ix.avoid_list)

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
) -> CatstylePromptPack:
    tension_scenes = list(seed.suggested_scene_angles)
    comp_scenes = [seed.constructive_channel, seed.visual_metaphor]
    n = req.variants_count
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
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

        prompt = (
            f"{_STYLE_CORE} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {seed.core_tension} "
            f"Constructive undertone available: {seed.constructive_channel} "
            f"Visual metaphor: {seed.visual_metaphor}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = (
        f"Loopable 3–5s animation, same catstyle: {pa} and {pb} planet-cats, aspect {req.aspect_type}, "
        f"minimal squash-and-stretch on round bodies, thick outlines held crisp at small size, "
        f"dark starry backdrop, readable silhouettes, comic timing;{anim_skin} {_STYLE_CORE}"
    ).strip()

    negative_chunks = [
        "text, words, letters, captions, watermarks, logos, trademarks, QR codes",
        "photorealistic, hyperreal skin, HDR glossy, anime sparkle eyes, luxury product render",
        "crowded background, micro-details, filigree jewelry, chrome liquid, lens flare spam",
    ]
    negative_prompt = ", ".join(negative_chunks + list(seed.avoid))

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
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
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

        prompt = (
            f"{_STYLE_CORE} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {core} "
            f"Constructive undertone available: {constructive}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = (
        f"Loopable 3–5s animation, same catstyle: {pa} and {pb} planet-cats, aspect {req.aspect_type}, "
        f"minimal squash-and-stretch on round bodies, thick outlines held crisp at small size, "
        f"dark starry backdrop, readable silhouettes, comic timing;{anim_skin} {_STYLE_CORE}"
    ).strip()

    negative_chunks = [
        "text, words, letters, captions, watermarks, logos, trademarks, QR codes",
        "photorealistic, hyperreal skin, HDR glossy, anime sparkle eyes, luxury product render",
        "crowded background, micro-details, filigree jewelry, chrome liquid, lens flare spam",
    ]
    negative_prompt = ", ".join(negative_chunks + avoid)

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

    aspect_ix = get_aspect_interaction(pa, pb)
    if aspect_ix is not None:
        pack = _pack_from_deep(
            pa, pb, req, canon_a=canon_a, canon_b=canon_b, aspect_ix=aspect_ix, skin_a=skin_a, skin_b=skin_b
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
            pack = _pack_from_seed(pa, pb, req, canon_a=canon_a, canon_b=canon_b, seed=seed, skin_a=skin_a, skin_b=skin_b)
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
