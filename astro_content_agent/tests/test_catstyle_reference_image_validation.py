"""Catstyle approved-reference image validation (stub PNG safety)."""
from __future__ import annotations

from pathlib import Path

import pytest

from astro_content_agent.services.content.catstyle_reference_image_validation import (
    MIN_REFERENCE_IMAGE_BYTES,
    CatstyleReferenceImageValidationError,
    validate_reference_image_source,
)
from astro_content_agent.tests.catstyle_reference_test_helpers import (
    write_png_signature_stub,
    write_valid_reference_png,
)


def test_rejects_eight_byte_png_signature_file(tmp_path: Path) -> None:
    stub = tmp_path / "sig_only.png"
    write_png_signature_stub(stub)
    assert stub.stat().st_size == 8
    with pytest.raises(CatstyleReferenceImageValidationError, match="8-byte PNG signature stub"):
        validate_reference_image_source(stub)


def test_rejects_tiny_png_below_minimum(tmp_path: Path) -> None:
    tiny = tmp_path / "tiny.png"
    tiny.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 32)
    with pytest.raises(CatstyleReferenceImageValidationError, match="too small"):
        validate_reference_image_source(tiny)


def test_accepts_valid_png_fixture(tmp_path: Path) -> None:
    good = tmp_path / "valid.png"
    write_valid_reference_png(good)
    assert good.stat().st_size > MIN_REFERENCE_IMAGE_BYTES
    out = validate_reference_image_source(good)
    assert out == good.resolve()
