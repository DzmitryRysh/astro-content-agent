"""Approved arena/environment reference prompt block (environment-only v1)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.approved_arena_reference_registry import ResolvedArenaReference
from astro_content_agent.content.catstyle.models import CatstylePromptPack

CATSTYLE_APPROVED_ARENA_REFERENCE_BLOCK: Final[str] = (
    "[CATSTYLE APPROVED ARENA REFERENCE v1] When an approved **arena/environment** reference image is attached, "
    "use it **only** for **environment richness**—**not** for character identity, planet colors, poses, "
    "aspect choreography, or glyph placement.\n"
    "**Arena reference controls:** brighter premium cosmic zodiac **coliseum** (illuminated arches, deeper readable tiers, "
    "elegant asymmetry), **rich starfield** with **colorful Milky Way / galaxy band**, cosmic dust and nebula depth, "
    "**Earth disk above** the arena, **readable zodiac floor**, premium cinematic vault lighting.\n"
    "**Do NOT copy from arena reference:** Sun/Uranus/Mars/etc. **catplanet bodies**, faces, costumes, accessories, "
    "banner glyphs, chest/collar emblems, aspect-specific action staging, or pair-specific color stories.\n"
    "**Style/aspect reference** (when present) still controls **character campaign DNA**; this arena reference "
    "stabilizes the **world shell** only. Honor text locks for **banner-only glyphs**, **catplanet body material**, "
    "and pair choreography."
)


def build_approved_arena_reference_prompt_block(hit: ResolvedArenaReference) -> str:
    """Full arena-reference lock including registry provenance."""
    label = (hit.label or hit.registry_key).strip()
    return (
        f"{CATSTYLE_APPROVED_ARENA_REFERENCE_BLOCK} "
        f"Registry: {hit.registry_key} ({label}). "
        "Match its **coliseum brightness**, **architectural tiers**, **sky richness**, and **floor readability**—"
        "never transplant characters or glyphs from the reference plate."
    )


def inject_approved_arena_reference_block(prompt: str, block: str) -> str:
    """Append arena block after style opener region when possible."""
    block = block.strip()
    if not block or block.lower() in prompt.lower():
        return prompt
    for anchor in (
        "[CATSTYLE APPROVED ARENA REFERENCE v1]",
        "Aspect type:",
        "[WORLD TEMPLATE v1",
    ):
        idx = prompt.find(anchor)
        if idx > 0:
            return f"{prompt[:idx].rstrip()} {block} {prompt[idx:].lstrip()}"
    return f"{prompt.rstrip()} {block}"


def apply_approved_arena_reference_to_prompt_pack(
    pack: CatstylePromptPack,
    hit: ResolvedArenaReference,
) -> CatstylePromptPack:
    """Inject arena reference lock into the first image prompt."""
    block = build_approved_arena_reference_prompt_block(hit)
    data = pack.model_dump(mode="json")
    prompts = [str(p) for p in (data.get("image_prompts") or [])]
    if prompts:
        prompts[0] = inject_approved_arena_reference_block(prompts[0], block)
        data["image_prompts"] = prompts
    data["arena_reference_assist"] = {
        "registry_key": hit.registry_key,
        "arena_reference_image_path": str(hit.image_path),
        "label": hit.label,
        "notes": hit.notes,
        "priority": hit.priority,
        "prompt_block": block,
    }
    return CatstylePromptPack.model_validate(data)


def format_arena_reference_image_roles_prefix(
    *,
    style_reference_present: bool,
    arena_reference_present: bool,
    banner_glyph_a: bool,
    banner_glyph_b: bool,
) -> str:
    """
    Provider preamble for multi-image edit: A=style, B=arena environment, C/D=banner glyphs.
    """
    if not arena_reference_present and not banner_glyph_a and not banner_glyph_b and not style_reference_present:
        return ""
    lines = [
        "[CATSTYLE REFERENCE IMAGE ROLES v1] When the image API accepts multiple reference images:",
    ]
    letter = ord("A")
    if style_reference_present:
        lines.append(
            "**Image A** = primary **style / character campaign** reference (catplanet finish, lighting density, "
            "material polish)—**NOT** for copying misplaced body glyphs from the plate."
        )
        letter += 1
    if arena_reference_present:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = **approved arena/environment reference ONLY**—copy **coliseum brightness**, "
            "**illuminated arches**, **tier depth**, **rich Milky Way sky**, **Earth above arena**, "
            "**zodiac floor**—**do NOT** copy characters, poses, planet colors, or glyphs from this plate."
        )
        letter += 1
    if banner_glyph_a:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = narrow **left/port banner glyph** crop—heraldic cloth glyph only."
        )
        letter += 1
    if banner_glyph_b:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = narrow **right/starboard banner glyph** crop—heraldic cloth glyph only."
        )
    lines.append(
        "Arena reference must **not** override character identity, glyph discipline, or aspect choreography."
    )
    return " ".join(lines)


__all__ = [
    "CATSTYLE_APPROVED_ARENA_REFERENCE_BLOCK",
    "apply_approved_arena_reference_to_prompt_pack",
    "build_approved_arena_reference_prompt_block",
    "format_arena_reference_image_roles_prefix",
    "inject_approved_arena_reference_block",
]
