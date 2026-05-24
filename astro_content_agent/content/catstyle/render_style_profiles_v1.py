"""Catstyle render style profiles v1 (premium illustration finish cues)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstyleRenderStyleProfile

DEFAULT_RENDER_STYLE_PROFILE_KEY = "premium_comic_poster_v2"

RENDER_STYLE_PROFILES: dict[str, CatstyleRenderStyleProfile] = {
    "premium_comic_poster_v1": CatstyleRenderStyleProfile(
        key="premium_comic_poster_v1",
        label="Premium comic poster v1",
        description=(
            "Primary Catstyle finish target: cinematic comic splash-page / movie-poster illustration clarity "
            "with decisive staging and disciplined polish."
        ),
        image_prompt_opening_line=(
            "Premium cinematic comic-poster illustration of anthropomorphic planet-cats, polished comic rendering, "
            "bold contour lines, controlled cel-shaded / painterly lighting, rich but clean detail, dramatic arena "
            "staging, expressive faces, strong silhouette readability, poster-quality composition."
        ),
        style_core_line=(
            "Premium cinematic comic POSTER illustration - splash-page energy with movie-poster-grade composition "
            "and clean focal hierarchy; polished linework with controlled painterly texture reads "
            "(rich yet disciplined, never mush); explicitly NOT flat mascot art, NOT children's book softness, "
            "NOT kawaii simplification, NOT toy toddler-cartoon, NOT cheap chibi, NOT simple vector icon gloss."
        ),
        composition_line=(
            "Cinematic poster-grade framing with decisive foreground / midground / background separation; "
            "one focal interaction readable at thumbnail size; reject bland centered mascot tableau and "
            "empty-background characters floating like stickers."
        ),
        linework_line=(
            "Bold readable contour lines with comic illustration clarity - anchors silhouette reads "
            "without devolving into flat sticker outlines."
        ),
        shading_line=(
            "Controlled painterly shading - directional modeling that respects planes on round comic bodies; "
            "avoid noisy micro-speckle and muddy smudge heaps."
        ),
        lighting_line=(
            "Dramatic keyed rim light accents silhouettes and props - cinematic comic stage lighting "
            "without HDR realism spam."
        ),
        environment_line=(
            "Premium environment staging tied to world/scene beats - atmospheric depth cues "
            "(stars, void, arena rim glow) without empty backdrop slack."
        ),
        detail_line=(
            "Clean rich rendering discipline - purposeful folds/props/emblems only; "
            "controlled density so readability beats ornamental clutter."
        ),
        color_line=(
            "Vivid disciplined palette - harmonic contrasts supporting focal hierarchy "
            "while honoring canon palettes where noted."
        ),
        facial_expression_line=(
            "Expressive theatrical cartoon acting - deadpan comedy readable "
            "yet cinematic (eyes/paws posture telling story)."
        ),
        must_have_lines=[
            "Finished cinematic comic illustration vibe across frame.",
            "Premium comic-poster presentation with dramatic lighting and readable depth planes.",
            "One decisive hero beat moment (interaction staged intentionally).",
            "Strong silhouette legibility on both planet-cats at thumbnail.",
            "Polished digital painting finish balanced against cartoon abstraction.",
            "Poster-readable staging consistent with locked canon/markers/world/scene cues.",
        ],
        avoid_lines=[
            "Flat mascot clip-art blandness.",
            "Cheap nursery bedtime softness.",
            "Simple sticker centered-float posing.",
            "Kawaii baby-face simplification or toddler toy vibe.",
            "Cheap chibi proportions / oversized infant heads.",
            "Weak ambiguous compositions lacking focal thrust.",
            "Over-simplified mobile game idle icons.",
            "Flat vector icon treatments without cinematic depth.",
            "Noisy hyper-microtexture overlays.",
            "Photoreal bodies/furs/skin shaders.",
            "Low-effort generic clipart vibes.",
        ],
        negative_prompt_additions=[
            "simple flat children's cartoon",
            "toddler-book illustration",
            "sticker mascot style",
            "cheap vector icon",
            "low-detail kawaii look",
            "nursery cartoon softness",
            "flat-color-only rendering",
            "empty simple background",
            "overly minimal character rendering",
            "flat mascot sticker aesthetic",
            "cheap children's cartoon softness",
            "kawaii simplified toddler cute overload",
            "chibi proportions cheap novelty figure read",
            "simple flat vector icon illustration without depth",
            "symmetrical dull sticker posing centered with empty backdrop",
            "floating characters on empty void backdrop",
            "weak bland composition",
            "microscopic gritty noise texture",
            "muddy over-rendered detail piles",
            "photorealistic fur/skin pores HDR portrait lighting",
            "generic clipart icon simplicity",
            "mobile game splash idle pose blandness",
        ],
        short_prompt_line=(
            "Premium cinematic comic poster finish - splash-panel polish, bold contours, dramatic rim light, "
            "readable decisive staging."
        ),
    ),
    "premium_comic_poster_v2": CatstyleRenderStyleProfile(
        key="premium_comic_poster_v2",
        label="Premium comic poster v2 (battle hardlock)",
        description=(
            "Strongest Catstyle premium battle-poster profile: collectible comic-cover / cinematic duel splash energy "
            "with explicit anti-nursery / anti-sticker discipline and monumental arena staging bias."
        ),
        image_prompt_opening_line=(
            "Premium cinematic comic-poster illustration — poster-grade comic splash illustration — high-drama heroic "
            "comic-cover battle splash featuring anthropomorphic planet-cats; hand-painted stylized 2D/2.5D comic feel "
            "(NOT photoreal, NOT 3D CGI, NOT game splash render), collectible-cover polish, monumental duel staging, "
            "layered foreground/midground/background depth, dramatic focal and rim-impact lighting, bold authoritative "
            "silhouettes, painterly cel-shaded polished comic rendering—prioritize premium battle poster reads over "
            "cute mascot simplicity."
        ),
        style_hardlock_block=(
            "Prioritize dramatic poster composition over cute simplicity—reject nursery-book softness, kawaii sticker "
            "flattening, and bland mascot idle posing. Stage as premium comic cover / heroic battle splash: decisive "
            "focal hierarchy, meaningful environment depth behind the duel (never empty flats), dynamic body-on-body "
            "interaction with pose authority, cinematic rim or impact lighting sculpting forms—never floating mascots "
            "on void backdrops or emoji-flat icon staging. Texture rule: use only large and medium texture groups "
            "(no dense microtexture layering). Background rule: arena and zodiac floor stay epic but simplified and "
            "less detailed than characters. Lighting rule: dramatic but clean; use separation, never overload."
        ),
        style_core_line=(
            "Ultra-premium cinematic comic POSTER battle illustration—movie-one-sheet and collectible cover clarity "
            "with heroic duel gravity; polished contours plus disciplined painterly cel modeling (rich planes, no mush); "
            "explicitly NOT nursery softness, NOT kawaii cute flattening, NOT cheap chibi novelty, NOT flat mobile-game "
            "icon gloss, NOT simplistic clip mascot staging."
        ),
        composition_line=(
            "Poster-grade heroic framing: monumental scale read via FG/MG/BG layering—foreground bodies dominate with "
            "authority; midground carries arena architecture weight; background opens into consequential cosmic depth; "
            "reject centered sticker tableaus and empty minimalist staging."
        ),
        linework_line=(
            "Bold authoritative contours anchoring heroic silhouette reads—comic illustration clarity without "
            "devolving into flat emoji-outline boredom."
        ),
        shading_line=(
            "Painterly cel discipline—directional modeling on round comic bodies with crisp plane shifts and stylized "
            "hand-painted comic shading; avoid muddy baby-soft gradients, noisy grit stacks, and hyper-detailed AI texture."
        ),
        lighting_line=(
            "High-drama keyed light plus cinematic rim and impact accents—battle splash readability without HDR "
            "photoreal spam."
        ),
        environment_line=(
            "World-scale heroic staging locked to template beats—arena/coliseum reads monumental (floating celestial "
            "battle disk / cosmic coliseum rim), atmospheric depth (stars, nebula void, rim glow)—never toy sandbox "
            "flatness."
        ),
        detail_line=(
            "Purposeful heroic medium-detail only—emblems, armor stripes, arena sparks in controlled amounts; density "
            "serves focal hierarchy, not ornamental clutter or micro-detail overload."
        ),
        color_line=(
            "Vivid disciplined harmonic contrasts supporting duel focal thrust while honoring canon palettes."
        ),
        facial_expression_line=(
            "Intense theatrical heroic acting—readable eyes/jaws/paws selling contest stakes with comic gravitas "
            "(not infant cute mush)."
        ),
        must_have_lines=[
            "Collectible comic-cover / battle splash poster energy.",
            "Heroic cinematic staging with clear duel focal thrust.",
            "Layered depth planes that sell monumental arena consequence.",
            "Bold silhouette authority on both planet-cats at thumbnail.",
            "Polished painterly cel comic finish with disciplined richness.",
            "Canon + identity markers remain unmistakable—never generic animals.",
        ],
        avoid_lines=[
            "Nursery bedtime softness or toddler-story easing.",
            "Kawaii cute dominance flattening drama.",
            "Sticker mascot center-float on empty backdrops.",
            "Cheap chibi / emoji-flat icon reads.",
            "Mobile-game idle icon bland staging.",
            "Flat vector simplicity masquerading as polish.",
            "Weak ambiguous compositions lacking heroic thrust.",
            "Photoreal fur/skin/HDR portrait cues.",
            "3D CGI figurine finish or glossy game-engine materials.",
            "Hyper-detailed AI-render texture clutter and tiny crack noise.",
            "Overcomplicated architecture that steals focus from characters.",
        ],
        negative_prompt_additions=[
            "childish nursery illustration style",
            "kawaii or chibi mascot flattening",
            "sticker mascot center-float posing",
            "flat vector / cheap icon / mobile-game icon look",
            "photoreal / hyperreal / CGI / 3D game render finish",
            "hyper-detailed microtexture noise and tiny crack clutter",
            "excess sparks and particles clutter",
            "over-rendered fur strands and material noise",
            "cluttered architecture micro-detail spam",
            "weak bland composition with disconnected characters",
        ],
        short_prompt_line=(
            "V2 premium battle poster—heroic coliseum-scale duel splash, dramatic rim/impact light, anti-nursery discipline."
        ),
    ),
    "premium_cg_keyart_v1": CatstyleRenderStyleProfile(
        key="premium_cg_keyart_v1",
        label="Premium CG key art v1",
        description=(
            "Premium CG key art / polished 2.5D–3D-hybrid game poster finish: crisp silhouettes, clean edges, strong "
            "material separation, high-contrast volumetric lighting, and cinematic depth—Catstyle catplanets, arena, "
            "flags, and zodiac floor preserved."
        ),
        image_prompt_opening_line=(
            "Premium CG key art illustration of anthropomorphic planet-cats — polished 2.5D / 3D-hybrid game key-art poster "
            "finish with crisp silhouette readability, clean hard edges, strong material separation, high-contrast keyed "
            "lighting, volumetric light, and cinematic depth (NOT watercolor, NOT gouache, NOT soft painterly storybook "
            "illustration, NOT sketchbook texture, NOT photoreal portrait, NOT flat mascot sticker art); "
            "collectible splash-art CG polish with monumental cosmic coliseum scale, epic dramatic staging, and "
            "brand-consistent catplanet identity—game key-art surface clarity over hand-painted comic brush dominance."
        ),
        style_hardlock_block=(
            "HARDLOCK premium CG key-art finish: prioritize polished 2.5D / 3D-hybrid poster rendering with crisp edges, "
            "readable silhouettes, separated materials, and volumetric cinematic lighting—reject watercolor washes, gouache "
            "softness, painterly illustration dominance, storybook / children's-book painted look, sketchbook texture, fuzzy "
            "brush stacks, flat comic doodle simplicity, and visible hand-painted ink-wash mush. "
            "Catstyle universe non-negotiable: catplanet bodies (not ordinary cats), monumental cosmic coliseum, engraved "
            "zodiac floor wheel, faction flags with canonical planetary glyphs woven in cloth (readable heraldic gold), "
            "cosmic scale, epic duel or alliance staging—characters remain focal hierarchy. "
            "Texture: medium CG material groups with clean specular planes—no micro-noise speckle, no mushy airbrush fog. "
            "Lighting: high-contrast dramatic separation with volumetric depth—no HDR photoreal skin, no murky noir crush."
        ),
        style_core_line=(
            "Ultra-premium CG KEY-ART / game splash-art presentation—polished 2.5D–3D-hybrid poster clarity with heroic "
            "epic gravity; crisp surfaces, clean edges, controlled CG specular and strong material reads (readable planes, "
            "no mush); explicitly NOT watercolor, gouache, soft painterly illustration, storybook or sketchbook dominance, "
            "NOT dominant hand-painted comic brush texture, NOT photoreal fur/skin/HDR portrait, NOT flat comic doodle or "
            "cheap chibi novelty."
        ),
        composition_line=(
            "Premium key-art poster framing: monumental arena scale via FG/MG/BG layering—foreground catplanets dominate "
            "with crisp silhouette authority; midground coliseum weight; background cosmic depth; premium poster composition "
            "readable at thumbnail—reject centered sticker tableaus and empty flats."
        ),
        linework_line=(
            "Clean graphic edge discipline for CG silhouette reads—crisp contour separation without mushy ink-wash or "
            "fuzzy brushstroke dominance."
        ),
        shading_line=(
            "Stylized CG shading with clear plane shifts, material separation, and polished surface modeling—volumetric "
            "form reads, not soft painterly gradient mush, gouache bloom, or gritty comic speckle stacks."
        ),
        lighting_line=(
            "High-contrast volumetric cinematic key light plus rim and impact accents—game key-art readability with depth "
            "and separation; no flat ambient mush, no photoreal bounce spam."
        ),
        environment_line=(
            "Catstyle arena staging locked to template beats—monumental coliseum, engraved zodiac floor readability, "
            "cosmic rim and starfield depth—environment supports focal thrust without stealing characters."
        ),
        detail_line=(
            "Purposeful CG medium-detail—armor planes, arena stone, flag cloth, readable glyph stamps; density serves "
            "focal hierarchy, not ornamental micro-clutter or painterly noise."
        ),
        color_line=(
            "Vivid disciplined high-contrast palette supporting key-art focal thrust while honoring canon planet palettes."
        ),
        facial_expression_line=(
            "Theatrical heroic acting with crisp readable eyes/jaws/paws—stylized CG clarity, not infant cute mush."
        ),
        must_have_lines=[
            "Premium CG key art / polished 2.5D–3D-hybrid game poster finish at thumbnail.",
            "Crisp silhouette readability and clean hard edges on both catplanets.",
            "Strong material separation and polished CG surfaces.",
            "High-contrast keyed lighting with volumetric depth and cinematic separation.",
            "Catstyle universe preserved: epic arena, zodiac floor, readable flag glyphs, cosmic scale.",
            "Premium poster composition with clear heroic focal thrust.",
            "Brand-consistent catplanet identity—never generic animals.",
        ],
        avoid_lines=[
            "Watercolor, gouache, or soft painterly illustration dominance.",
            "Storybook, sketchbook, or hand-painted children's-book softness.",
            "Dominant hand-painted comic brush texture and visible ink-wash mush.",
            "Fuzzy brush texture stacks without CG polish.",
            "Flat comic doodle or cheap vector icon simplicity.",
            "Rough sketchy painted texture without material separation.",
            "Flat sticker mascot center-float on empty backdrops.",
            "Photoreal fur/skin pores and HDR portrait lighting.",
            "Hyper-microtexture noise and tiny crack clutter.",
            "Weak bland compositions lacking heroic thrust.",
        ],
        negative_prompt_additions=[
            "watercolor illustration",
            "watercolor wash dominance",
            "gouache painting look",
            "soft painterly illustration dominance",
            "hand-painted storybook illustration",
            "children's picture-book painted look",
            "sketchbook illustration texture",
            "fuzzy brush texture dominance",
            "flat comic doodle look",
            "ink-wash mush dominance",
            "visible hand-painted comic brushstroke mush",
            "rough hand-painted texture dominance",
            "soft airbrush illustration mush",
            "pastel storybook softness",
            "nursery bedtime illustration softness",
            "kawaii or chibi mascot flattening",
            "sticker mascot center-float posing",
            "flat vector / cheap icon look",
            "photoreal / hyperreal portrait skin pores HDR",
            "hyper-detailed microtexture noise and tiny crack clutter",
            "muddy painterly gradient mush without readable planes",
            "weak bland composition with disconnected characters",
            "2D flat comic panel without volumetric depth",
        ],
        short_prompt_line=(
            "Premium CG key art—2.5D/3D-hybrid game poster polish, crisp edges, high-contrast volumetric light, anti-watercolor lock."
        ),
    ),
    "clean_cartoon_action_v1": CatstyleRenderStyleProfile(
        key="clean_cartoon_action_v1",
        label="Clean cartoon action v1",
        description=(
            "Secondary finish: smoother graphic cartoon action with cel clarity - "
            "less painterly texture noise than premium poster mode while staying cinematic."
        ),
        image_prompt_opening_line=(
            "Clean premium cartoon-action illustration of anthropomorphic planet-cats, bold outlines, smooth cel "
            "shading, simplified but polished forms, readable action, cinematic staging without noisy micro-texture."
        ),
        style_core_line=(
            "Cleaner graphic cartoon action illustration - premium cinematic staging "
            "with smoother cel-friendly surfaces and purposeful simplicity."
        ),
        composition_line=(
            "Dynamic readable poses with crisp silhouette staging - poster clarity "
            "without painterly noise buildup."
        ),
        linework_line=(
            "Bold confident outlines with controlled taper - graphic cartoon clarity "
            "preferring smooth contour reads."
        ),
        shading_line=(
            "Smooth cel shading blocks with gentle gradients - simpler planes than painterly poster mode; "
            "avoid gritty grain overlays."
        ),
        lighting_line=(
            "Bright cinematic highlights with crisp shadow shapes - comic cel discipline "
            "without harsh photoreal bounce."
        ),
        environment_line=(
            "Streamlined environment silhouettes supporting action beat - "
            "fewer micro-details than poster mode but still staged depth."
        ),
        detail_line=(
            "Purposeful graphic props/emblems only - smooth readable surfaces over ornamental grit."
        ),
        color_line=(
            "Bold flat-friendly palette ramps with punchy accents - disciplined hue separation."
        ),
        facial_expression_line=(
            "Expressive graphic cartoon acting - bigger readable facial beats suited to cel clarity."
        ),
        must_have_lines=[
            "Graphic cartoon action readability across frame.",
            "Smooth cel-ready shading discipline.",
            "Cinematic staging without noisy painterly texture.",
            "Strong silhouettes on motion-heavy poses.",
        ],
        avoid_lines=[
            "Hyper-detailed gritty painterly texture stacks.",
            "Arena micro-detail noise clutter.",
            "Photoreal shading cues.",
            "Flat sticker emptiness.",
        ],
        negative_prompt_additions=[
            "simple flat children's cartoon",
            "toddler-book illustration",
            "sticker mascot style",
            "cheap vector icon",
            "low-detail kawaii look",
            "nursery cartoon softness",
            "flat-color-only rendering",
            "empty simple background",
            "overly minimal character rendering",
            "speckled gritty painterly noise texture",
            "hyper-detailed gritty arena clutter",
            "over-rendered rocky texture spam",
            "photoreal skin fur HDR shading",
            "flat sticker centered mascot emptiness",
            "muddy gradient mush without readable planes",
        ],
        short_prompt_line=(
            "Clean cel cartoon action finish - smooth shading, bold outlines, cinematic staging minus gritty noise."
        ),
    ),
}


def _validate_registry(profiles: dict[str, CatstyleRenderStyleProfile]) -> None:
    text_fields = (
        "label",
        "description",
        "image_prompt_opening_line",
        "style_core_line",
        "composition_line",
        "linework_line",
        "shading_line",
        "lighting_line",
        "environment_line",
        "detail_line",
        "color_line",
        "facial_expression_line",
        "short_prompt_line",
    )
    for dict_key, prof in profiles.items():
        if dict_key != prof.key:
            raise ValueError(f"Render style registry key mismatch: dict {dict_key!r} vs profile.key {prof.key!r}.")
        for name in text_fields:
            val = getattr(prof, name)
            if not isinstance(val, str) or not str(val).strip():
                raise ValueError(f"Render style profile {prof.key!r} field {name!r} must be non-empty text.")
        if not prof.must_have_lines or not prof.avoid_lines or not prof.negative_prompt_additions:
            raise ValueError(f"Render style profile {prof.key!r} lists must be non-empty.")
        for lst_name in ("must_have_lines", "avoid_lines", "negative_prompt_additions"):
            lst = getattr(prof, lst_name)
            for i, item in enumerate(lst):
                if not isinstance(item, str) or not item.strip():
                    raise ValueError(f"Render style profile {prof.key!r} {lst_name}[{i}] must be non-empty.")


_validate_registry(RENDER_STYLE_PROFILES)


def normalize_render_style_profile_key(raw: str) -> str:
    key = (raw or "").strip().lower().replace("-", "_")
    if key not in RENDER_STYLE_PROFILES:
        known = ", ".join(sorted(RENDER_STYLE_PROFILES))
        raise ValueError(f"Unknown Catstyle render style profile {raw!r}. Known keys: {known}.")
    return key


def get_render_style_profile(key: str) -> CatstyleRenderStyleProfile:
    return RENDER_STYLE_PROFILES[normalize_render_style_profile_key(key)]


def list_render_style_profiles() -> list[CatstyleRenderStyleProfile]:
    return [RENDER_STYLE_PROFILES[k] for k in sorted(RENDER_STYLE_PROFILES)]


def format_render_style_prompt_block(profile: CatstyleRenderStyleProfile) -> str:
    must_have = " | ".join(profile.must_have_lines)
    avoid = " | ".join(profile.avoid_lines)
    return (
        f"[RENDER STYLE v1 - high-priority visual finish] {profile.label}: {profile.style_core_line} "
        f"Composition: {profile.composition_line} "
        f"Linework: {profile.linework_line} "
        f"Shading: {profile.shading_line} "
        f"Lighting: {profile.lighting_line} "
        f"Environment: {profile.environment_line} "
        f"Detail control: {profile.detail_line} "
        f"Color: {profile.color_line} "
        f"Facial acting: {profile.facial_expression_line} "
        f"Must have: {must_have} "
        f"Avoid: {avoid}. "
        f"Compact cue: {profile.short_prompt_line}"
    )


def format_render_style_prompt_block_for_flow(profile: CatstyleRenderStyleProfile) -> str:
    """
    Flow-mode render finish: same premium poster discipline as v2, without duel/battle vocabulary.

    Non-v2 profiles keep the standard block (already lighter on explicit duel language).
    """
    if profile.key != "premium_comic_poster_v2":
        return format_render_style_prompt_block(profile)
    must_have = " | ".join(
        [
            "Collectible comic-cover / alliance discovery poster energy.",
            "Cinematic staging with shared focal pull toward horizon, portal, atlas, or open chart beat.",
            "Layered depth planes that sell monumental arena consequence without tournament clash read.",
            "Bold silhouette authority on both planet-cats at thumbnail.",
            "Polished painterly cel comic finish with disciplined richness.",
            "Canon + identity markers remain unmistakable—never generic animals.",
            "Bright readable heroic poster lighting with luminous midtones and Instagram-mobile legible faces.",
            "Luminous golden opportunity portal treated as central key light with warm bounce on both subjects.",
        ]
    )
    avoid = " | ".join(
        list(profile.avoid_lines)
        + [
            "versus duel or showdown symmetry as primary read",
            "squared-off combat tournament clash staging",
            "MMA brawl collision framing as dominant read",
            "underexposed overall scene",
            "muddy crushed shadows",
            "black-crushed unreadable background",
            "characters disappearing into darkness",
            "overly dark noir lighting",
            "horror gloom darkness dominance",
        ]
    )
    return (
        f"[RENDER STYLE v1 - high-priority visual finish] {profile.label} (FLOW alliance read): "
        "Ultra-premium cinematic comic POSTER illustration—movie-one-sheet and collectible cover clarity with "
        "discovery-opportunity gravity (not combat contest); polished contours plus disciplined painterly cel modeling "
        "(rich planes, no mush); explicitly NOT nursery softness, NOT kawaii cute flattening, NOT cheap chibi novelty, "
        "NOT flat mobile-game icon gloss, NOT simplistic clip mascot staging. "
        f"Composition: Poster-grade allied framing: monumental scale via FG/MG/BG layering—foreground duo shares a "
        "co-directed gesture or joint motion toward a visible shared objective (star map, portal rim, horizon band, open atlas); "
        "midground carries arena architecture weight; background opens into consequential cosmic depth; "
        "reject centered sticker tableaus and empty minimalist staging. "
        f"Linework: {profile.linework_line} "
        f"Shading: {profile.shading_line} "
        "Lighting (flow readability): bright readable heroic poster lighting—preserve deep cosmic arena mood but lift "
        "overall exposure for faces, portal aperture, faction banners, and distant Earth impact cue to Instagram-thumb "
        "clarity; treat a luminous golden opportunity portal as the central key light with warm reflected fill across "
        "both muzzles and paws; add soft cool Mercury rim light and warm Jupiter generous fill so banded and rocky "
        "sphere reads stay dimensional; keep dramatic contrast with clean luminous midtones—reject murky mud, clipped "
        "black voids, horror/noir underexposure, or characters vanishing into shadow. "
        f"Environment: {profile.environment_line} "
        f"Detail control: {profile.detail_line} "
        "Color: Vivid disciplined harmonic contrasts supporting co-discovery focal pull while honoring canon palettes. "
        "Facial acting: Warm intelligent theatrical acting—curiosity, wonder, generous focus—readable eyes/jaws/paws selling "
        "alliance stakes with comic gravitas (not infant cute mush). "
        f"Must have: {must_have} "
        f"Avoid: {avoid}. "
        "Compact cue: V2 premium alliance-discovery poster—monumental cosmic opportunity staging, luminous golden portal "
        "key light, dramatic clean rim/fill balance, anti-nursery discipline, Instagram-mobile readable polish."
    )


__all__ = [
    "DEFAULT_RENDER_STYLE_PROFILE_KEY",
    "RENDER_STYLE_PROFILES",
    "format_render_style_prompt_block",
    "format_render_style_prompt_block_for_flow",
    "get_render_style_profile",
    "list_render_style_profiles",
    "normalize_render_style_profile_key",
]
