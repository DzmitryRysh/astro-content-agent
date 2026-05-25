# Catstyle style reference images

This folder holds **approved visual style reference** images for the Catstyle image pipeline. They anchor illustration look-and-feel when providers support image-conditioned generation.

Pass a reference file when building job manifests with:

`--style-reference-image <path>`

**Recommended file (current):**

`references/catstyle_jupiter_mars_approved.png`

## Banner glyph crops (optional)

Narrow **banner-only** glyph references (not full scenes) for higher flag fidelity:

- `references/banner_glyphs/{planet}_banner_glyph.png` (e.g. `sun_banner_glyph.png`, `uranus_banner_glyph.png`)
- Left/port banner = planet A; right/starboard = planet B
- Set explicitly on prompt requests via `banner_glyph_reference_planet_a` / `banner_glyph_reference_planet_b`, or rely on auto-discovery when files exist.
