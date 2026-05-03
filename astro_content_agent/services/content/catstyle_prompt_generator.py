"""Generate Catstyle v0 image prompt packs (text only; no image API calls)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.aspect_library_v0 import ASPECT_CAT_INTERACTIONS, get_aspect_interaction
from astro_content_agent.content.catstyle.models import CatstylePromptPack, CatstylePromptRequest, PlanetCatProfile
from astro_content_agent.content.catstyle.planet_bible_v0 import PLANET_CAT_PROFILES
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

_CANONICAL_PLANET: dict[str, str] = {p.lower(): p for p in PLANET_CAT_PROFILES}


def normalize_planet_name(name: str) -> str:
    key = (name or "").strip().lower()
    if key not in _CANONICAL_PLANET:
        known = ", ".join(sorted(PLANET_CAT_PROFILES))
        raise ValueError(f"Unknown planet {name!r}. Catstyle v0 supports: {known}.")
    return _CANONICAL_PLANET[key]


def _supported_pairs_hint() -> str:
    deep = [" + ".join(sorted(k, key=str.lower)) for k in ASPECT_CAT_INTERACTIONS]
    return "Deep aspect library: " + "; ".join(sorted(deep)) + ". Plus 25 social/outer-to-personal transit seeds (transit_pair_seed_v0)."


def _pack_from_deep(
    pa: str,
    pb: str,
    req: CatstylePromptRequest,
    *,
    prof_a: PlanetCatProfile,
    prof_b: PlanetCatProfile,
    aspect_ix,
) -> CatstylePromptPack:
    tension_scenes = list(aspect_ix.scene_ideas)
    comp_scenes = list(aspect_ix.compensation_scene_ideas)
    n = req.variants_count

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
            f"{pa} planet-cat: {prof_a.visual_identity}; palette {prof_a.colors}; "
            f"expression style {prof_a.facial_expression_style}; props {prof_a.signature_props}. "
            f"{pb} planet-cat: {prof_b.visual_identity}; palette {prof_b.colors}; "
            f"expression style {prof_b.facial_expression_style}; props {prof_b.signature_props}. "
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {aspect_ix.core_tension} "
            f"Constructive undertone available: {aspect_ix.constructive_channel}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = (
        f"Loopable 3–5s animation, same catstyle: {pa} and {pb} planet-cats, aspect {req.aspect_type}, "
        f"minimal squash-and-stretch on round bodies, thick outlines held crisp at small size, "
        f"dark starry backdrop, readable silhouettes, comic timing; {_STYLE_CORE}"
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
        f"(props and poses only, catstyle rules unchanged)."
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
    prof_a: PlanetCatProfile,
    prof_b: PlanetCatProfile,
    seed: CatstyleTransitPairSeed,
) -> CatstylePromptPack:
    tension_scenes = list(seed.suggested_scene_angles)
    comp_scenes = [seed.constructive_channel, seed.visual_metaphor]
    n = req.variants_count

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
            f"{pa} planet-cat: {prof_a.visual_identity}; palette {prof_a.colors}; "
            f"expression style {prof_a.facial_expression_style}; props {prof_a.signature_props}. "
            f"{pb} planet-cat: {prof_b.visual_identity}; palette {prof_b.colors}; "
            f"expression style {prof_b.facial_expression_style}; props {prof_b.signature_props}. "
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {seed.core_tension} "
            f"Constructive undertone available: {seed.constructive_channel} "
            f"Visual metaphor: {seed.visual_metaphor}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = (
        f"Loopable 3–5s animation, same catstyle: {pa} and {pb} planet-cats, aspect {req.aspect_type}, "
        f"minimal squash-and-stretch on round bodies, thick outlines held crisp at small size, "
        f"dark starry backdrop, readable silhouettes, comic timing; {_STYLE_CORE}"
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
        f"(props and poses only, catstyle rules unchanged)."
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
    prof_a: PlanetCatProfile,
    prof_b: PlanetCatProfile,
    outer: str,
    personal: str,
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
            f"{pa} planet-cat: {prof_a.visual_identity}; palette {prof_a.colors}; "
            f"expression style {prof_a.facial_expression_style}; props {prof_a.signature_props}. "
            f"{pb} planet-cat: {prof_b.visual_identity}; palette {prof_b.colors}; "
            f"expression style {prof_b.facial_expression_style}; props {prof_b.signature_props}. "
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {core} "
            f"Constructive undertone available: {constructive}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = (
        f"Loopable 3–5s animation, same catstyle: {pa} and {pb} planet-cats, aspect {req.aspect_type}, "
        f"minimal squash-and-stretch on round bodies, thick outlines held crisp at small size, "
        f"dark starry backdrop, readable silhouettes, comic timing; {_STYLE_CORE}"
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
        f"final slide leans into: {constructive} (props and poses only)."
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
    prof_a: PlanetCatProfile = PLANET_CAT_PROFILES[pa]
    prof_b: PlanetCatProfile = PLANET_CAT_PROFILES[pb]

    aspect_ix = get_aspect_interaction(pa, pb)
    if aspect_ix is not None:
        return _pack_from_deep(pa, pb, req, prof_a=prof_a, prof_b=prof_b, aspect_ix=aspect_ix)

    oriented = orient_outer_personal(pa, pb)
    if oriented is None:
        raise ValueError(
            f"No Catstyle content for {pa} + {pb}: not a social/outer-to-personal transit pair. {_supported_pairs_hint()}"
        )

    outer, personal = oriented
    seed = get_transit_pair_seed(outer, personal)
    if seed is not None:
        return _pack_from_seed(pa, pb, req, prof_a=prof_a, prof_b=prof_b, seed=seed)

    return _pack_from_fallback(pa, pb, req, prof_a=prof_a, prof_b=prof_b, outer=outer, personal=personal)


__all__ = [
    "generate_catstyle_prompt_pack",
    "normalize_planet_name",
]
