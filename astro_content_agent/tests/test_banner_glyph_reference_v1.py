"""Banner glyph reference assist — prompts, banner-only discipline, Sun/Uranus roles."""
from __future__ import annotations

import re
from pathlib import Path

from astro_content_agent.content.catstyle.banner_glyph_reference_v1 import (
    BANNER_ONLY_FORBIDDEN_IDENTITY_PHRASES,
    BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK,
    banner_only_prompt_forbidden_phrases,
    build_banner_glyph_reference_assist,
    format_banner_glyph_reference_roles_block,
    identity_marker_block_forbidden_in_banner_only,
    resolve_banner_glyph_reference_paths,
    sanitize_assembled_prompt_for_banner_only,
    sanitize_marker_field_for_banner_only,
)
from astro_content_agent.content.catstyle.planet_identity_markers_v1 import (
    format_identity_markers_prompt_block,
    get_planet_identity_marker_profile,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_banner_only_discipline_forbids_extra_glyph_locations() -> None:
    low = BANNER_ONLY_GLYPH_DISCIPLINE_BLOCK.lower()
    assert "exactly one" in low
    assert "left/port" in low or "left" in low
    assert "right/starboard" in low or "starboard" in low
    assert "chest" in low
    assert "armor" in low
    assert "costume jewelry" in low
    assert "accessory" in low or "accessories" in low
    assert "portal rim" in low
    assert "floating" in low
    assert "central dot" in low
    assert "zodiac coliseum" in low or "cosmic zodiac coliseum" in low
    assert "zodiac floor" in low
    assert "earth disk" in low


def test_sanitize_sun_primary_removes_body_emblem_zones() -> None:
    raw = get_planet_identity_marker_profile("Sun").primary_marker
    cleaned = sanitize_marker_field_for_banner_only("Sun", raw, field="primary")
    assert identity_marker_block_forbidden_in_banner_only(cleaned) == []
    assert "banner" in cleaned.lower()


def test_banner_only_identity_blocks_suppress_conflicting_phrases() -> None:
    for planet in ("Sun", "Uranus", "Moon", "Venus", "Mars"):
        block = format_identity_markers_prompt_block(
            planet,
            get_planet_identity_marker_profile(planet),
            has_skin=False,
            banner_only_glyph=True,
        )
        assert identity_marker_block_forbidden_in_banner_only(block) == [], (
            f"{planet}: {identity_marker_block_forbidden_in_banner_only(block)}"
        )
        assert "banner cloth only" in block.lower()
    sun_block = format_identity_markers_prompt_block(
        "Sun",
        get_planet_identity_marker_profile("Sun"),
        has_skin=False,
        banner_only_glyph=True,
    )
    assert "central dot" in sun_block.lower()


def _identity_marker_sections(blob: str) -> str:
    """Extract only ``[IDENTITY MARKERS v1] for {Planet}:`` blocks (not art-direction name-drops)."""
    end_patterns = (
        r"\[IDENTITY MARKERS v1\] for \w+:",
        r"\w+ planet-cat \[CANON",
        r"\[CATSTYLE ",
        r"Premium comic direction \(deterministic",
        r"\[FLAG GLYPH",
        r"\[RENDER STYLE",
        r"\[WORLD ",
    )
    parts: list[str] = []
    for m in re.finditer(r"\[IDENTITY MARKERS v1\] for (\w+):", blob):
        start = m.start()
        tail = blob[m.end() :]
        end_rel = len(tail)
        for pat in end_patterns:
            hit = re.search(pat, tail)
            if hit:
                end_rel = min(end_rel, hit.start())
        parts.append(blob[start : m.end() + end_rel])
    return "\n".join(parts)


_BROKEN_FRAGMENTS = (
    "flat, , or",
    "flat, ,",
    "nner appears",
    ", , or",
    "Reserve a large flat",
    "emblem zone large enough",
)
_FORBIDDEN_LEAKS = (
    "emblem-ready",
    "reserved emblem zone",
    "prop stamps",
    "prop stamp",
    "stamp zone",
    "chest emblem",
    "crown medallion",
    "portal rim medallion",
    "blank chest/crown",
    "blank chest",
    "solar medallion",
    "stage medallion",
    "flat sun medallion",
    "beside faces/bodies",
)


def test_banner_only_sun_identity_no_broken_fragments_or_leaks() -> None:
    block = format_identity_markers_prompt_block(
        "Sun",
        get_planet_identity_marker_profile("Sun"),
        has_skin=False,
        banner_only_glyph=True,
    )
    low = block.lower()
    for frag in _BROKEN_FRAGMENTS:
        assert frag.lower() not in low, f"broken fragment: {frag}"
    for phrase in _FORBIDDEN_LEAKS:
        assert phrase not in low, f"forbidden leak: {phrase}"
    assert "corona" in low
    assert "solar-core" in low or "solar-core body" in low
    assert "golden armor" in low
    assert "central dot" in low
    assert "placement guidance:" in low
    assert ", ," not in block


def test_banner_only_uranus_identity_no_broken_fragments_or_leaks() -> None:
    block = format_identity_markers_prompt_block(
        "Uranus",
        get_planet_identity_marker_profile("Uranus"),
        has_skin=False,
        banner_only_glyph=True,
    )
    low = block.lower()
    for frag in _BROKEN_FRAGMENTS:
        assert frag.lower() not in low, f"broken fragment: {frag}"
    for phrase in _FORBIDDEN_LEAKS:
        assert phrase not in low, f"forbidden leak: {phrase}"
    assert "portal hoop" in low
    assert "cyan ice-gas" in low
    assert "lightning tail" in low


def test_sanitize_assembled_prompt_strips_sun_canon_medallion_language() -> None:
    raw = (
        "Sun planet-cat [CANON v1 base]: golden cat. "
        "Signature props: Tiny foldable director's chair; flat sun medallion collar (icon only, no readable text). "
        "[PLANET CANON v1 - Sun] Signature props: Solar medallion, subtle regal collar motifs, banner-like drape."
    )
    cleaned = sanitize_assembled_prompt_for_banner_only(raw)
    low = cleaned.lower()
    assert "medallion" not in low
    assert "solar-core body accent" in low or "neck corona line" in low
    assert "circular chest badge" not in low


def test_sun_uranus_assembled_prompt_no_medallion_or_glyph_attractors() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_comic_poster_v2",
            shot_mode="epic_arena_showdown",
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    joined = "\n".join(pack.image_prompts)
    low = joined.lower()
    for phrase in _FORBIDDEN_LEAKS + ("medallion", "flat sun medallion", "solar medallion", "stage medallion"):
        assert phrase not in low, f"leak in assembled prompt: {phrase}"
    for frag in _BROKEN_FRAGMENTS:
        assert frag.lower() not in low, f"broken fragment in assembled prompt: {frag}"
    assert banner_only_prompt_forbidden_phrases(joined) == []
    assert "[catstyle banner-only glyph discipline v1]" in low
    assert "left/port" in low and "sun" in low
    assert "right/starboard" in low and "uranus" in low
    assert "central dot" in low
    assert "corona" in low or "solar-core" in low
    assert "zodiac floor" in low or "zodiac wheel" in low
    assert "coliseum" in low
    assert "earth disk" in low or "earth above" in low
    assert "premium cg" in low or "key-art" in low or "volumetric" in low


def test_sun_uranus_pack_banner_only_identity_and_world_locks() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_comic_poster_v2",
            shot_mode="epic_arena_showdown",
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    joined = "\n".join(pack.image_prompts)
    low = joined.lower()
    assert banner_only_prompt_forbidden_phrases(joined) == []
    assert "medallion" not in low
    assert "zodiac floor" in low or "zodiac wheel" in low or "engraved zodiac" in low
    assert "coliseum" in low or "cosmic zodiac" in low
    assert "starfield" in low or "star field" in low or "nebula" in low
    assert "earth disk" in low or "earth above" in low
    assert "central dot" in low
    assert "[CATSTYLE BANNER-ONLY GLYPH DISCIPLINE v1]" in joined


def test_reference_roles_block_image_a_b_c(tmp_path: Path) -> None:
    sun_crop = tmp_path / "sun_banner.png"
    ura_crop = tmp_path / "uranus_banner.png"
    sun_crop.write_bytes(b"\x89PNG\r\n\x1a\n")
    ura_crop.write_bytes(b"\x89PNG\r\n\x1a\n")
    block = format_banner_glyph_reference_roles_block(
        "Sun",
        "Uranus",
        style_reference_present=True,
        glyph_ref_planet_a=str(sun_crop),
        glyph_ref_planet_b=str(ura_crop),
    )
    assert "[CATSTYLE REFERENCE IMAGE ROLES v1]" in block
    assert "Image A" in block
    assert "Image B" in block
    assert "Image C" in block
    assert "left/port" in block.lower()
    assert "right/starboard" in block.lower()
    assert "\u2609" in block or "Sun" in block
    assert "\u2645" in block or "Uranus" in block
    assert "floating sticker" in block.lower()


def test_resolve_explicit_banner_glyph_paths(tmp_path: Path) -> None:
    pa = tmp_path / "mercury_glyph.png"
    pb = tmp_path / "uranus_glyph.png"
    pa.write_bytes(b"x")
    pb.write_bytes(b"x")
    a, b = resolve_banner_glyph_reference_paths(
        "Mercury",
        "Uranus",
        explicit_planet_a=str(pa),
        explicit_planet_b=str(pb),
        use_auto_discovery=False,
    )
    assert a == str(pa.resolve())
    assert b == str(pb.resolve())


def test_sun_uranus_prompt_banner_glyph_roles_and_banner_only(tmp_path: Path) -> None:
    sun_ref = tmp_path / "sun_left_banner_glyph.png"
    ura_ref = tmp_path / "uranus_right_banner_glyph.png"
    sun_ref.write_bytes(b"\x89PNG\r\n\x1a\n")
    ura_ref.write_bytes(b"\x89PNG\r\n\x1a\n")
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Sun",
            planet_b="Uranus",
            aspect_type="conjunction",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_comic_poster_v2",
            shot_mode="epic_arena_showdown",
            banner_glyph_reference_planet_a=str(sun_ref),
            banner_glyph_reference_planet_b=str(ura_ref),
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    joined = "\n".join(pack.image_prompts)
    assert "[CATSTYLE BANNER-ONLY GLYPH DISCIPLINE v1]" in joined
    assert "[CATSTYLE REFERENCE IMAGE ROLES v1]" in joined
    assert "Image A" in joined and "Image B" in joined
    assert "left/port" in joined.lower() and "Sun" in joined
    assert "right/starboard" in joined.lower() and "Uranus" in joined
    assert "left/port" in joined.lower()
    assert "right/starboard" in joined.lower()
    assert pack.banner_glyph_reference_assist is not None
    assert pack.banner_glyph_reference_assist["banner_glyph_reference_planet_a_path"]
    assert pack.banner_glyph_reference_assist["banner_glyph_reference_planet_b_path"]
    assert "[FLAG GLYPH FIDELITY LOCK v1]" in joined


def test_prompt_includes_pair_flag_system_without_glyph_refs() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mars",
            planet_b="Jupiter",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            use_banner_glyph_reference_auto=False,
            disable_approved_reference_prompt_lock=True,
        )
    )
    joined = "\n".join(pack.image_prompts)
    assert "[CATSTYLE PAIR FLAG GLYPH SYSTEM v1]" in joined
    assert "[CATSTYLE BANNER-ONLY GLYPH DISCIPLINE v1]" in joined
    assert "[CATSTYLE REFERENCE IMAGE ROLES v1]" not in joined


def test_build_assist_metadata_none_without_resolved_paths() -> None:
    assist = build_banner_glyph_reference_assist(
        "Sun",
        "Uranus",
        explicit_glyph_a="/nonexistent/sun.png",
        explicit_glyph_b=None,
        use_auto_discovery=False,
    )
    assert assist is None
