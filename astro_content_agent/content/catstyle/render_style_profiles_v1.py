"""Catstyle render style profiles v1 (premium illustration finish cues)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstyleRenderStyleProfile

DEFAULT_RENDER_STYLE_PROFILE_KEY = "premium_comic_poster_v1"

RENDER_STYLE_PROFILES: dict[str, CatstyleRenderStyleProfile] = {
    "premium_comic_poster_v1": CatstyleRenderStyleProfile(
        key="premium_comic_poster_v1",
        label="Premium comic poster v1",
        description=(
            "Primary Catstyle finish target: cinematic comic splash-page / movie-poster illustration clarity "
            "with decisive staging and disciplined polish."
        ),
        style_core_line=(
            "Premium cinematic comic illustration with movie-poster / splash-panel presence - "
            "reads like a finished high-quality comic one-sheet or collectible poster mock-up "
            "(still stylized Catstyle planet-cats, never photoreal portraiture)."
        ),
        composition_line=(
            "Poster-grade framing with decisive foreground / midground / background separation; "
            "one focal interaction readable at thumbnail size; reject bland centered mascot tableau."
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
            "One decisive hero beat moment (interaction staged intentionally).",
            "Strong silhouette legibility on both planet-cats at thumbnail.",
            "Polished digital painting finish balanced against cartoon abstraction.",
            "Poster-readable staging consistent with locked canon/markers/world/scene cues.",
        ],
        avoid_lines=[
            "Flat mascot clip-art blandness.",
            "Cheap nursery bedtime softness.",
            "Simple sticker centered-float posing.",
            "Weak ambiguous compositions lacking focal thrust.",
            "Over-simplified mobile game idle icons.",
            "Noisy hyper-microtexture overlays.",
            "Photoreal bodies/furs/skin shaders.",
            "Low-effort generic clipart vibes.",
        ],
        negative_prompt_additions=[
            "flat mascot sticker aesthetic",
            "cheap children's cartoon softness",
            "symmetrical dull sticker posing centered with empty backdrop",
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
    "clean_cartoon_action_v1": CatstyleRenderStyleProfile(
        key="clean_cartoon_action_v1",
        label="Clean cartoon action v1",
        description=(
            "Secondary finish: smoother graphic cartoon action with cel clarity - "
            "less painterly texture noise than premium poster mode while staying cinematic."
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


__all__ = [
    "DEFAULT_RENDER_STYLE_PROFILE_KEY",
    "RENDER_STYLE_PROFILES",
    "format_render_style_prompt_block",
    "get_render_style_profile",
    "list_render_style_profiles",
    "normalize_render_style_profile_key",
]
