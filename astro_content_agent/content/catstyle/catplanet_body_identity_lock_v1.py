"""Catplanet body identity and Sun/Uranus flag-glyph precision locks (visual fidelity)."""
from __future__ import annotations

from typing import Final

CATPLANET_BODY_IDENTITY_LOCK_BLOCK: Final[str] = (
    "[CATPLANET BODY IDENTITY LOCK v1] Characters must read as **anthropomorphic planet-cats (catplanets)**—"
    "not ordinary cats in costumes or pets with elemental effects pasted on. "
    "**Body surface** must show **planetary texture/material** (not ordinary fur-only pets). "
    "Planet identity must read through **body material, aura, props, and silhouette**. "
    "Reject **generic cat with elemental glow** (fire/lightning on a normal cat body)."
)

SUN_CATPLANET_BODY_LOCK_BLOCK: Final[str] = (
    "[SUN CATPLANET BODY LOCK v1] Sun = **living solar core / plasma catplanet**: "
    "**orange-gold solar surface texture**, **molten plasma pattern**, **corona mane / fire halo**, "
    "**radiant star-core glow**—not an orange cat with fire effects only."
)

URANUS_CATPLANET_BODY_LOCK_BLOCK: Final[str] = (
    "[URANUS CATPLANET BODY LOCK v1] Uranus = **ice-gas planet catplanet**: "
    "**cyan/blue-green planetary surface**, subtle **atmospheric bands** or **icy cloud texture**, "
    "**tilted-axis identity**, **orbital ring / magnetic-field motif**, **fractured electric geometry**—"
    "not striped like a tiger, not plush, not an ordinary blue cat with lightning."
)

FLAG_GLYPH_PRECISION_LOCK_SUN_URANUS_BLOCK: Final[str] = (
    "[FLAG GLYPH PRECISION LOCK v1] **Sun flag:** canonical **\u2609 (☉)**—**circle with central dot**, "
    "large, complete, clean, **painted into cloth**. **Uranus flag:** canonical **\u2645 (♅)**—**full glyph** "
    "with **vertical stem, side arcs, lower circle**, complete and readable on cloth. "
    "Glyphs must be **integrated heraldic paint**—not partial, cropped, fake, approximate, or random rune; "
    "reject incomplete glyph reads."
)

CATPLANET_BODY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "ordinary cats with effects",
    "generic elemental cats",
    "weak planet texture",
    "plush toy body",
)

SUN_URANUS_BODY_FLAG_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "incomplete flag glyphs",
    "fake Uranus glyph",
    "partial Sun glyph",
)


def sun_uranus_body_and_flag_lock_blocks() -> str:
    """Compact stack for Sun–Uranus conjunction+tension prompts."""
    return " ".join(
        (
            SUN_CATPLANET_BODY_LOCK_BLOCK,
            URANUS_CATPLANET_BODY_LOCK_BLOCK,
            FLAG_GLYPH_PRECISION_LOCK_SUN_URANUS_BLOCK,
        )
    ).strip()


__all__ = [
    "CATPLANET_BODY_IDENTITY_LOCK_BLOCK",
    "CATPLANET_BODY_NEGATIVE_EXTRAS",
    "FLAG_GLYPH_PRECISION_LOCK_SUN_URANUS_BLOCK",
    "SUN_CATPLANET_BODY_LOCK_BLOCK",
    "SUN_URANUS_BODY_FLAG_NEGATIVE_EXTRAS",
    "URANUS_CATPLANET_BODY_LOCK_BLOCK",
    "sun_uranus_body_and_flag_lock_blocks",
]
