"""Generate Catstyle v0 image prompt packs (text only; no image API calls)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.aspect_library_v0 import ASPECT_CAT_INTERACTIONS, get_aspect_interaction
from astro_content_agent.content.catstyle.models import CatstylePromptPack, CatstylePromptRequest, PlanetCatProfile
from astro_content_agent.content.catstyle.planet_bible_v0 import PLANET_CAT_PROFILES

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
    pairs = [" + ".join(sorted(k, key=str.lower)) for k in ASPECT_CAT_INTERACTIONS]
    return "; ".join(sorted(pairs))


def generate_catstyle_prompt_pack(req: CatstylePromptRequest) -> CatstylePromptPack:
    """Build prompts from planet bible + aspect library v0."""
    pa = normalize_planet_name(req.planet_a)
    pb = normalize_planet_name(req.planet_b)
    aspect_ix = get_aspect_interaction(pa, pb)
    if aspect_ix is None:
        raise ValueError(
            f"No Catstyle aspect library v0 entry for {pa} + {pb}. Supported pairs: {_supported_pairs_hint()}."
        )

    prof_a: PlanetCatProfile = PLANET_CAT_PROFILES[pa]
    prof_b: PlanetCatProfile = PLANET_CAT_PROFILES[pb]

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


__all__ = [
    "generate_catstyle_prompt_pack",
    "normalize_planet_name",
]
