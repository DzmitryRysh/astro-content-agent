"""True premium CGI / 3D render fidelity hardlock (v1)."""
from __future__ import annotations

from typing import Final

TRUE_PREMIUM_CGI_RENDER_HARDLOCK_MARKER: Final[str] = "[TRUE PREMIUM CGI RENDER HARDLOCK v1]"

TRUE_PREMIUM_CGI_RENDER_HARDLOCK_BLOCK: Final[str] = (
    "[TRUE PREMIUM CGI RENDER HARDLOCK v1] High-end cinematic 3D CGI key art—not painted fantasy illustration. "
    "Physically based rendering: PBR metal, PBR stone, realistic fabric, sculpted 3D fur, crisp specular highlights, "
    "volumetric torchlight, cinematic depth, game-cinematic material separation—premium 3D sculpted figures, not flat mascots. "
    "Stone, armor, chains, weapons, gems, fabric, fur = distinct physical materials. "
    "Reject painterly brush texture, digital painting softness, storybook/watercolor/gouache, matte painting background, "
    "flat poster art, soft airbrushed mascot look."
)

CLEAN_REFS_TRUE_PREMIUM_CGI_RENDER_HARDLOCK_BLOCK: Final[str] = (
    "[TRUE PREMIUM CGI RENDER HARDLOCK v1] High-end cinematic 3D CGI key art—not painted fantasy illustration. "
    "Physically based rendering: PBR metal, PBR stone, realistic fabric, sculpted 3D fur, crisp specular highlights, "
    "volumetric torchlight, cinematic depth, material separation—premium 3D figures, not flat mascots. "
    "Reject painterly brush texture, digital painting softness, flat poster art, soft airbrushed mascot look."
)

TRUE_PREMIUM_CGI_RENDER_NEGATIVE_EXTRAS: Final[tuple[str, ...]] = (
    "digital painting look",
    "painted fantasy illustration",
    "storybook fantasy art",
    "flat poster art",
    "soft airbrushed mascot",
    "brush texture",
    "matte painting background",
    "non-3d illustration",
    "flat painted fur",
    "flat painted armor",
    "low material separation",
    "plastic toy look",
    "mobile game mascot render",
)

__all__ = [
    "CLEAN_REFS_TRUE_PREMIUM_CGI_RENDER_HARDLOCK_BLOCK",
    "TRUE_PREMIUM_CGI_RENDER_HARDLOCK_BLOCK",
    "TRUE_PREMIUM_CGI_RENDER_HARDLOCK_MARKER",
    "TRUE_PREMIUM_CGI_RENDER_NEGATIVE_EXTRAS",
]
