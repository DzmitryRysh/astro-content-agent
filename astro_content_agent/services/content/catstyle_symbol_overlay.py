"""Experimental local glyph compositing for Catstyle images (Pillow).

**Not** the default Catstyle publication strategy: normal posts should use the
**image model** to paint integrated heraldic planetary glyphs **into flag cloth**.

This module remains for **manual / repair** workflows only (e.g. quick fixes
when a provider artifact is unusable). It writes sibling files such as
``*_overlay`` / ``*_symbols_fixed`` and never replaces the source render.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Final

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from astro_content_agent.content.catstyle.planet_glyph_registry_v1 import (
    CANONICAL_PLANET_GLYPHS,
    canonical_glyph_char,
)

# Backward-compatible alias for CLI/tests (same mapping as ``CANONICAL_PLANET_GLYPHS``).
PLANET_GLYPHS: Final[dict[str, str]] = CANONICAL_PLANET_GLYPHS

SYMBOLS_FIXED_STEM_TAG: Final[str] = "_symbols_fixed"

# Normalized anchors (0–1): character A / left faction flag, character B / right faction flag.
FLAG_LAYOUT_PRESETS: Final[dict[str, dict[str, tuple[float, float]]]] = {
    "poster_ab": {
        "a": (0.28, 0.36),
        "b": (0.72, 0.36),
    },
}


def glyph_for_planet(planet_name: str) -> str | None:
    """Return the canonical glyph character for *planet_name*, or ``None`` if unknown."""
    return canonical_glyph_char(planet_name or "")


def default_overlay_output_path(input_path: Path) -> Path:
    """``stem_overlay.ext`` next to the source file (single-glyph legacy)."""
    p = Path(input_path)
    return p.with_name(f"{p.stem}_overlay{p.suffix}")


def default_symbols_fixed_output_path(input_path: Path) -> Path:
    """``stem_symbols_fixed.ext`` — experimental manual dual-glyph output (not default publish)."""
    p = Path(input_path)
    return p.with_name(f"{p.stem}{SYMBOLS_FIXED_STEM_TAG}{p.suffix}")


def is_symbols_fixed_path(path: Path) -> bool:
    """True if *path* stem ends with ``_symbols_fixed`` (experimental manual output naming)."""
    return Path(path).stem.endswith(SYMBOLS_FIXED_STEM_TAG)


def assert_publication_uses_symbols_fixed(path: Path) -> None:
    """Optional QA helper for **manual** pipelines that intentionally ship overlay files.

    **Do not** use for standard Catstyle IG publishing (prefer model-painted flag glyphs).

    Raises ``ValueError`` if the filename does not end with ``_symbols_fixed``.
    """
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"Publication path must exist: {p}")
    if not p.stem.endswith(SYMBOLS_FIXED_STEM_TAG):
        raise ValueError(
            f"Manual overlay QA: expected filename ending with {SYMBOLS_FIXED_STEM_TAG!r}. Got {p.name!r}."
        )


def _resolve_font(size_px: int, font_path: Path | None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[Path] = []
    if font_path is not None:
        candidates.append(Path(font_path))
    candidates.extend(
        [
            Path(r"C:\Windows\Fonts\seguiemj.ttf"),
            Path(r"C:\Windows\Fonts\seguisym.ttf"),
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]
    )
    for p in candidates:
        if p.is_file():
            try:
                return ImageFont.truetype(str(p), size=int(size_px))
            except OSError:
                continue
    return ImageFont.load_default()


def _composite_premium_glyph(
    target: Image.Image,
    glyph: str,
    xy_px: tuple[int, int],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    *,
    fill: str = "#f7f2e4",
    stroke_width: int = 3,
    stroke_fill: str = "#14081f",
    glow_blur_radius: int = 7,
    glow_under_scale: float = 1.12,
) -> None:
    """Draw one glyph onto *target* (RGBA) with soft gold glow under a crisp cream + ink stroke."""
    w, h = target.size
    px, py = xy_px
    glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)
    glow_font = font
    try:
        base_size = int(getattr(font, "size", 0) or 0)
        fpath = getattr(font, "path", None)
        if base_size > 0 and fpath:
            glow_font = ImageFont.truetype(str(fpath), int(base_size * glow_under_scale))
    except (OSError, AttributeError, TypeError, ValueError):
        glow_font = font
    # Warm gold halo (reads on dark flags / mobile)
    gdraw.text(
        (px, py),
        glyph.strip(),
        font=glow_font,
        fill=(255, 228, 170, 255),
        stroke_width=int(stroke_width) + 5,
        stroke_fill=(255, 210, 130, 255),
        anchor="mm",
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=int(glow_blur_radius)))
    target.alpha_composite(glow_layer)
    sharp = ImageDraw.Draw(target)
    sharp.text(
        (px, py),
        glyph.strip(),
        font=font,
        fill=fill,
        stroke_width=int(stroke_width),
        stroke_fill=stroke_fill,
        anchor="mm",
    )


def apply_symbol_overlay(
    input_path: Path,
    output_path: Path,
    *,
    glyph: str,
    x_norm: float,
    y_norm: float,
    size_px: int,
    font_path: Path | None = None,
    fill: str = "#f7f2e4",
    stroke_width: int = 3,
    stroke_fill: str = "#14081f",
    premium_glow: bool = True,
) -> Path:
    """Draw *glyph* on a copy of the image; the file at *input_path* is never modified.

    *x_norm* and *y_norm* are fractions of image width/height (0.0–1.0) for anchor ``mm``.
    When *premium_glow* is True, adds a soft gold blur under the crisp glyph (poster polish).
    """
    inp = Path(input_path).expanduser().resolve()
    outp = Path(output_path).expanduser().resolve()
    if not inp.is_file():
        raise FileNotFoundError(f"Input image not found: {inp}")
    if not (glyph or "").strip():
        raise ValueError("glyph must be non-empty")
    if not (0.0 <= float(x_norm) <= 1.0 and 0.0 <= float(y_norm) <= 1.0):
        raise ValueError("x_norm and y_norm must be between 0 and 1")
    outp.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(inp) as im0:
        im = im0.convert("RGBA")
    w, h = im.size
    px = int(float(x_norm) * w)
    py = int(float(y_norm) * h)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    font = _resolve_font(size_px, font_path)
    if premium_glow:
        _composite_premium_glyph(
            layer,
            glyph.strip(),
            (px, py),
            font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
    else:
        draw = ImageDraw.Draw(layer)
        draw.text(
            (px, py),
            glyph.strip(),
            font=font,
            fill=fill,
            stroke_width=int(stroke_width),
            stroke_fill=stroke_fill,
            anchor="mm",
        )
    out = Image.alpha_composite(im, layer)
    if outp.suffix.lower() in (".jpg", ".jpeg"):
        out.convert("RGB").save(outp, quality=95)
    else:
        out.save(outp)
    return outp


def apply_dual_flag_symbol_overlay(
    input_path: Path,
    output_path: Path,
    *,
    planet_a: str,
    planet_b: str,
    layout_preset: str = "poster_ab",
    size_px: int = 128,
    font_path: Path | None = None,
    fill: str = "#f7f2e4",
    stroke_width: int = 3,
    stroke_fill: str = "#14081f",
    a_xy: tuple[float, float] | None = None,
    b_xy: tuple[float, float] | None = None,
) -> Path:
    """Place **planet A** (left) and **planet B** (right) canonical glyphs on flag emblem zones.

    Writes a new image; *input_path* is never modified. Overlay is drawn last so it
    **dominates** any soft/wrong model-painted marks in the same region.
    """
    ga = glyph_for_planet(planet_a)
    gb = glyph_for_planet(planet_b)
    if not ga:
        raise ValueError(f"Unknown planet_a: {planet_a!r}")
    if not gb:
        raise ValueError(f"Unknown planet_b: {planet_b!r}")
    preset = FLAG_LAYOUT_PRESETS.get((layout_preset or "").strip().lower())
    if preset is None:
        keys = ", ".join(sorted(FLAG_LAYOUT_PRESETS))
        raise ValueError(f"Unknown layout_preset {layout_preset!r}; choose one of: {keys}")
    ax, ay = a_xy if a_xy is not None else preset["a"]
    bx, by = b_xy if b_xy is not None else preset["b"]

    inp = Path(input_path).expanduser().resolve()
    outp = Path(output_path).expanduser().resolve()
    if not inp.is_file():
        raise FileNotFoundError(f"Input image not found: {inp}")
    for u, v, label in ((ax, ay, "A"), (bx, by, "B")):
        if not (0.0 <= float(u) <= 1.0 and 0.0 <= float(v) <= 1.0):
            raise ValueError(f"Normalized coordinates for {label} must be in [0, 1]")

    outp.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(inp) as im0:
        im = im0.convert("RGBA")
    w, h = im.size
    font = _resolve_font(size_px, font_path)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    _composite_premium_glyph(
        layer,
        ga,
        (int(ax * w), int(ay * h)),
        font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )
    _composite_premium_glyph(
        layer,
        gb,
        (int(bx * w), int(by * h)),
        font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )
    out = Image.alpha_composite(im, layer)
    if outp.suffix.lower() in (".jpg", ".jpeg"):
        out.convert("RGB").save(outp, quality=95)
    else:
        out.save(outp)
    return outp


def copy_for_overlay_pipeline(input_path: Path, work_dir: Path | None = None) -> Path:
    """Optional: copy source into *work_dir* before editing (keeps original path untouched)."""
    src = Path(input_path).expanduser().resolve()
    if work_dir is None:
        return src
    work_dir = Path(work_dir).expanduser().resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    dst = work_dir / src.name
    shutil.copy2(src, dst)
    return dst


__all__ = [
    "FLAG_LAYOUT_PRESETS",
    "PLANET_GLYPHS",
    "SYMBOLS_FIXED_STEM_TAG",
    "apply_dual_flag_symbol_overlay",
    "apply_symbol_overlay",
    "assert_publication_uses_symbols_fixed",
    "copy_for_overlay_pipeline",
    "default_overlay_output_path",
    "default_symbols_fixed_output_path",
    "glyph_for_planet",
    "is_symbols_fixed_path",
]
