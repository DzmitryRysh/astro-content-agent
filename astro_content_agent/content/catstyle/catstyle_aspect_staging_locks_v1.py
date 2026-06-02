"""Global aspect staging locks: arena scale, framing, CGI render, environment dominance (v1/v2)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.planet_glyph_registry_v1 import (
    canonical_glyph_char,
    glyph_prompt_label,
)

# Back-compat alias: tests and docs may still reference v1 marker string in historical prompts.
CATSTYLE_ARENA_SCALE_LOCK_BLOCK: Final[str] = (
    "[CATSTYLE ARENA SCALE LOCK v2] The scene must read as a gigantic monumental cosmic zodiac colosseum—not a "
    "small room, generic hall, simple circular wall, or flat backdrop. Show at least three visible tiers of stone "
    "arches / arena structure with strong architectural depth and vertical scale. Keep visible upper curvature, "
    "upper coliseum structure, balconies, and sky vault above the rim. The arena must feel huge around the fighters; "
    "the environment remains a major compositional element, not a shallow ring behind the characters. Keep the "
    "engraved zodiac floor broad, physically integrated, and clearly part of the colosseum. Reject tight cropped "
    "rooms, shallow circular walls with no tier depth, tiny floor slices, and generic fantasy interiors."
)

CATSTYLE_CAMERA_FRAMING_LOCK_BLOCK: Final[str] = (
    "[CATSTYLE CAMERA / FRAMING LOCK v1] Use wide cinematic framing: full-body planet-cats with readable faces and "
    "gestures, generous surrounding negative space, and visible arena floor plus large coliseum architecture "
    "above and behind. Characters must not crop or fill the entire image—preserve the grandeur of the arena. "
    "Medium-wide to wide poster framing only; reject extreme close-up, tight portrait crop, or character-dominant "
    "composition that collapses the environment."
)

CATSTYLE_PREMIUM_CGI_RENDER_LOCK_BLOCK: Final[str] = (
    "[CATSTYLE PREMIUM CGI RENDER LOCK v1] Render as high-end cinematic 3D key art with physically based materials, "
    "sculpted volumetric character rendering, polished game-cinematic finish, crisp light behavior, and clean "
    "specular response. Explicitly reject painted poster feel, hand-painted fantasy illustration feel, matte "
    "painting look, brush-texture rendering, dry canvas feel, storybook shading, soft illustrated finish, "
    "watercolor dominance, gouache wash, fuzzy diffusion softness, and children's-book illustration diffusion."
)

CATSTYLE_ENVIRONMENT_DOMINANCE_BLOCK: Final[str] = (
    "[CATSTYLE ENVIRONMENT DOMINANCE v1] The coliseum must remain visually dominant: fighters exist inside a "
    "colossal environment, not on a small stage. Use scale cues—distant seating rows, balconies, repeating arches, "
    "torch lines, layered depth, visible upper structure, cosmic sky vault. Arena scale must still read clearly "
    "even during combat action; battle energy must not erase architectural monumentality."
)

PLANET_CAT_BODY_MATERIAL_INTENSITY_BLOCK: Final[str] = (
    "[PLANET-CAT BODY MATERIAL INTENSITY v1] The body itself must read as living planetary matter, not ordinary fur "
    "with costume and VFX. Show visible planetary surface material on face, torso, limbs, paws, and tail. Costume "
    "and props must follow the planet-body design instead of hiding it. Preserve feline anatomy, but planetary "
    "material must dominate over pet-cat fur."
)

REFERENCE_ROLE_DECLARATION_MARKER: Final[str] = "[REFERENCE ROLE DECLARATION v1]"

REFERENCE_ROLE_DECLARATION_BODY: Final[str] = (
    "Approved planet reference images are primary character identity anchors. "
    "Planet A reference controls Planet A face style, body proportions, silhouette, planetary material, palette, "
    "aura, costume logic, and core identity. "
    "Planet B reference controls Planet B face style, body proportions, silhouette, planetary material, palette, "
    "aura, costume logic, and core identity. "
    "Arena reference, if present, controls only environment scale, colosseum structure, floor design, sky depth, "
    "and banner placement. "
    "Pair/style reference, if present, is secondary and must not override Planet A or Planet B approved references. "
    "Do not let arena or pair style references replace the selected planet-cat identities."
)

ARENA_SCALE_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "small room backdrop instead of colosseum",
    "generic fantasy hall instead of zodiac arena",
    "cropped wall backdrop",
    "tiny arena floor slice",
    "shallow flat backdrop",
    "simple circular wall with no tier depth",
    "flat ring wall instead of monumental colosseum",
    "characters filling frame with no visible arena architecture",
    "extreme close-up crop with no colosseum architecture",
    "character-dominant framing that collapses environment",
)

CGI_RENDER_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "painted poster feel",
    "hand-painted fantasy illustration feel",
    "matte painting look",
    "brush-texture rendering",
    "dry canvas feel",
    "storybook shading",
    "soft illustrated finish",
    "painterly illustration dominance",
    "watercolor storybook softness",
    "soft fuzzy rendering",
    "illustrated children's-book diffusion",
    "gouache wash dominance",
)

BANNER_GLYPH_SWAP_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "swapped planet banner glyphs",
    "wrong planet glyph on faction banner",
    "venus glyph on mars banner",
    "mars glyph on venus banner",
    "invented pseudo-rune banner marks",
    "floating sticker banner overlays",
)


def build_planet_banner_glyph_lock_block(planet_a: str, planet_b: str) -> str:
    """Strict left/port = planet A, right/starboard = planet B glyph binding."""
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    ga = canonical_glyph_char(pa)
    gb = canonical_glyph_char(pb)
    if not ga or not gb:
        return ""
    la = glyph_prompt_label(pa) or pa
    lb = glyph_prompt_label(pb) or pb
    return (
        "[PLANET BANNER GLYPH LOCK v2] "
        f"Left/port banner belongs only to Planet A ({pa}) and must show exactly one large canonical glyph for "
        f"Planet A: **{pa} glyph {ga} only**. "
        f"Right/starboard banner belongs only to Planet B ({pb}) and must show exactly one large canonical glyph for "
        f"Planet B: **{pb} glyph {gb} only**. "
        "Do not swap glyphs between planets. Do not invent alternate symbols. Do not use unrelated planet glyphs. "
        "Do not use Venus glyph for Mars, Mars glyph for Venus, Saturn glyph for Uranus, or any wrong substitution. "
        "Glyphs must be bold, centered, simple, complete, and readable as heraldic gold/embroidered cloth marks. "
        "If glyph clarity is at risk, simplify the banner and glyph rather than changing the symbol. "
        "No pseudo-runes, no fake occult signs, no decorative approximations, no floating sticker overlays. "
        f"Banner glyphs are identity markers and must match the selected planets exactly ({la} left/port; {lb} right/starboard)."
    )


def build_reference_role_declaration_block(
    planet_a: str,
    planet_b: str,
    *,
    planet_refs_active: bool = False,
    arena_ref_present: bool = False,
    pair_style_ref_present: bool = False,
) -> str:
    """Reference role declaration when approved planet refs (and optional arena/pair refs) are in play."""
    if not planet_refs_active:
        return ""
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    extras: list[str] = []
    if arena_ref_present:
        extras.append(
            "Arena reference is active: use it only for environment scale, colosseum structure, floor, sky, "
            "and banner placement—not for character identity."
        )
    if pair_style_ref_present:
        extras.append(
            "Pair/style reference is active: secondary mood/finish cue only—must not override approved planet references."
        )
    tail = " ".join(extras)
    return f"{REFERENCE_ROLE_DECLARATION_MARKER} {REFERENCE_ROLE_DECLARATION_BODY} Planet A = {pa}. Planet B = {pb}. {tail}".strip()


CATSTYLE_VISUAL_COMPOSITION_HARDLOCK_MARKER: Final[str] = "[CATSTYLE VISUAL COMPOSITION HARDLOCK v1]"


def build_visual_composition_hardlock_layer() -> str:
    """Arena scale, framing, CGI render, and environment dominance—global for aspect prompts."""
    body = " ".join(
        [
            CATSTYLE_ARENA_SCALE_LOCK_BLOCK,
            CATSTYLE_CAMERA_FRAMING_LOCK_BLOCK,
            CATSTYLE_PREMIUM_CGI_RENDER_LOCK_BLOCK,
            CATSTYLE_ENVIRONMENT_DOMINANCE_BLOCK,
        ]
    ).strip()
    return f"{CATSTYLE_VISUAL_COMPOSITION_HARDLOCK_MARKER} {body}"


def build_aspect_staging_lock_layer(
    planet_a: str,
    planet_b: str,
    *,
    planet_refs_active: bool = False,
    arena_ref_present: bool = False,
    pair_style_ref_present: bool = False,
) -> str:
    """Arena scale, camera, premium CGI, and environment dominance (composition only)."""
    _ = (planet_a, planet_b, planet_refs_active, arena_ref_present, pair_style_ref_present)
    return build_visual_composition_hardlock_layer()


__all__ = [
    "ARENA_SCALE_NEGATIVE_EXTRAS",
    "BANNER_GLYPH_SWAP_NEGATIVE_EXTRAS",
    "CATSTYLE_ARENA_SCALE_LOCK_BLOCK",
    "CATSTYLE_CAMERA_FRAMING_LOCK_BLOCK",
    "CATSTYLE_ENVIRONMENT_DOMINANCE_BLOCK",
    "CATSTYLE_PREMIUM_CGI_RENDER_LOCK_BLOCK",
    "CGI_RENDER_NEGATIVE_EXTRAS",
    "PLANET_CAT_BODY_MATERIAL_INTENSITY_BLOCK",
    "REFERENCE_ROLE_DECLARATION_BODY",
    "REFERENCE_ROLE_DECLARATION_MARKER",
    "build_aspect_staging_lock_layer",
    "build_planet_banner_glyph_lock_block",
    "build_reference_role_declaration_block",
    "build_visual_composition_hardlock_layer",
    "CATSTYLE_VISUAL_COMPOSITION_HARDLOCK_MARKER",
]
