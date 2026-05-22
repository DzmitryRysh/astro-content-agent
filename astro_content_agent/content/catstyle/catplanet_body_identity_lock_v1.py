"""Catplanet body identity and Sun/Uranus pair-specific body locks (visual fidelity)."""
from __future__ import annotations

from typing import Final

CATPLANET_BODY_IDENTITY_LOCK_BLOCK: Final[str] = (
    "[CATPLANET BODY IDENTITY LOCK v1] The fighters are **anthropomorphic cat-planets, not ordinary cats in costumes**. "
    "Keep cute feline anatomy, but **body material, surface texture, glow, silhouette, and aura** must unmistakably "
    "express planetary identity—**living planetary bodies**, not generic cats with elemental effects. "
    "Planet identity via **body material, surface texture, aura, props, silhouette**; "
    "avoid ordinary fur-cat look without strong planetary texture; avoid mascot simplification."
)

SUN_CATPLANET_BODY_LOCK_BLOCK: Final[str] = (
    "[SUN CATPLANET BODY LOCK v1] Sun must read as a **living solar cat-planet**: "
    "**orange-gold solar-core body**, **molten plasma / star-surface texture**, **controlled corona / flame halo**, "
    "**royal Leo-coded solar authority**—not just an orange cat with fire."
)

URANUS_CATPLANET_BODY_LOCK_BLOCK: Final[str] = (
    "[URANUS CATPLANET BODY LOCK v1] Uranus must read as an **ice-gas electric cat-planet**: "
    "**cyan / blue-green atmospheric planetary surface**, subtle **ice-gas bands or cloud texture**, "
    "**tilted-axis / orbital / magnetic-field motif**, **electric disruptor identity**; "
    "**floating rocks / orbital debris / fractured electric geometry** allowed—"
    "not a soft blue cat, not plush, not striped tiger."
)

CATPLANET_BODY_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "ordinary cats with effects",
    "generic elemental cats",
    "weak planet texture",
    "plush toy body",
    "mascot redraw",
)


def sun_uranus_catplanet_body_lock_blocks() -> str:
    """Compact Sun + Uranus body locks for conjunction+tension prompts."""
    return " ".join((SUN_CATPLANET_BODY_LOCK_BLOCK, URANUS_CATPLANET_BODY_LOCK_BLOCK)).strip()


def sun_uranus_body_and_flag_lock_blocks() -> str:
    """Backward-compatible alias: body locks only (flag fidelity lives in flag_glyph_fidelity_lock_v1)."""
    return sun_uranus_catplanet_body_lock_blocks()


__all__ = [
    "CATPLANET_BODY_IDENTITY_LOCK_BLOCK",
    "CATPLANET_BODY_NEGATIVE_EXTRAS",
    "SUN_CATPLANET_BODY_LOCK_BLOCK",
    "URANUS_CATPLANET_BODY_LOCK_BLOCK",
    "sun_uranus_body_and_flag_lock_blocks",
    "sun_uranus_catplanet_body_lock_blocks",
]
