"""Shared helpers for Catstyle approved-reference approval tests."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from astro_content_agent.services.content.catstyle_reference_image_validation import (
    MIN_REFERENCE_IMAGE_BYTES,
    PNG_SIGNATURE,
)


def write_valid_reference_png(
    path: Path,
    *,
    min_bytes: int = MIN_REFERENCE_IMAGE_BYTES + 512,
    color: tuple[int, int, int] = (40, 80, 120),
) -> None:
    """Write a real PNG file large enough for production reference approval."""
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 64, 64
    while True:
        img = Image.new("RGB", (w, h), color=color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()
        if len(data) >= min_bytes:
            path.write_bytes(data)
            return
        w, h = w * 2, h * 2


def write_png_signature_stub(path: Path) -> None:
    """Write only the 8-byte PNG signature (invalid production reference)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG_SIGNATURE)


__all__ = ["PNG_SIGNATURE", "write_png_signature_stub", "write_valid_reference_png"]
