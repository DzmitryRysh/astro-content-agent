"""Validate local PNG files before Catstyle approved-reference copy/approval."""
from __future__ import annotations

from pathlib import Path

PNG_SIGNATURE: bytes = b"\x89PNG\r\n\x1a\n"
MIN_REFERENCE_IMAGE_BYTES: int = 10 * 1024


class CatstyleReferenceImageValidationError(ValueError):
    """Source or target reference image failed safety checks."""


def reference_image_quality_ok(path: Path | str) -> bool:
    """Return True when *path* meets minimum production reference image checks."""
    try:
        validate_reference_image_source(path)
        return True
    except CatstyleReferenceImageValidationError:
        return False


def validate_reference_image_source(
    path: Path | str,
    *,
    min_bytes: int = MIN_REFERENCE_IMAGE_BYTES,
) -> Path:
    """
    Ensure *path* is a real reference candidate (not a stub/header-only PNG).

    Raises :class:`CatstyleReferenceImageValidationError` with an operator-clear message.
    """
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise CatstyleReferenceImageValidationError(
            f"Reference image does not exist or is not a file: {p}"
        )

    size = p.stat().st_size
    if size == len(PNG_SIGNATURE) and p.read_bytes() == PNG_SIGNATURE:
        raise CatstyleReferenceImageValidationError(
            f"Reference image is only an 8-byte PNG signature stub ({p.name}); "
            "use a full rendered PNG export, not a test placeholder."
        )
    if size < min_bytes:
        raise CatstyleReferenceImageValidationError(
            f"Reference image is too small ({size} bytes, minimum {min_bytes} bytes): {p}. "
            "Stub/placeholder PNGs cannot be approved as production references."
        )

    with p.open("rb") as fh:
        header = fh.read(len(PNG_SIGNATURE))
    if header != PNG_SIGNATURE:
        raise CatstyleReferenceImageValidationError(
            f"Reference image is not a PNG (missing \\x89PNG header): {p}"
        )

    try:
        from PIL import Image
    except ImportError:
        return p

    try:
        with Image.open(p) as im:
            im.verify()
    except Exception as exc:
        raise CatstyleReferenceImageValidationError(
            f"Reference image failed PNG structure check ({p}): {exc}"
        ) from exc

    return p


__all__ = [
    "MIN_REFERENCE_IMAGE_BYTES",
    "PNG_SIGNATURE",
    "CatstyleReferenceImageValidationError",
    "reference_image_quality_ok",
    "validate_reference_image_source",
]
