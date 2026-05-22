"""Mars square Pluto (tension) pair-specific visual canon and glyph staging."""
from __future__ import annotations

from astro_content_agent.content.catstyle.mars_pluto_square_tension_canon_v1 import (
    MARS_PLUTO_SQUARE_TENSION_VISUAL_CANON,
    is_mars_pluto_square_tension,
)
from astro_content_agent.content.catstyle.pair_flag_glyph_resolution_v1 import (
    resolved_pair_flag_glyph_system_block,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _req(*, pa: str, pb: str) -> CatstylePromptRequest:
    return CatstylePromptRequest(
        planet_a=pa,
        planet_b=pb,
        aspect_type="square",
        mode="tension",
        variants_count=1,
        premium_art_direction=True,
        world_template_key="cosmic_zodiac_arena",
        render_style_profile_key="premium_comic_poster_v2",
        shot_mode="epic_arena_showdown",
    )


def test_resolved_flags_pluto_left_mars_right_ordering() -> None:
    txt = resolved_pair_flag_glyph_system_block("Mars", "Pluto", "square", "tension")
    assert "Left/port faction banner = Pluto" in txt
    assert "right/starboard faction banner = Mars" in txt
    assert "\u2647" in txt
    assert "\u2642" in txt


def test_resolved_flags_order_independent_for_mars_pluto_tension() -> None:
    a = resolved_pair_flag_glyph_system_block("Mars", "Pluto", "square", "tension")
    b = resolved_pair_flag_glyph_system_block("Pluto", "Mars", "square", "tension")
    assert a == b


def test_other_pairs_use_request_flag_order() -> None:
    jm = resolved_pair_flag_glyph_system_block("Jupiter", "Mars", "square", "tension")
    assert "Left/port faction banner = Jupiter" in jm
    assert "right/starboard faction banner = Mars" in jm


def test_prompt_includes_pair_canon_concept_arena_and_glyphs() -> None:
    pack = generate_catstyle_prompt_pack(_req(pa="Mars", pb="Pluto"))
    joined = "\n".join(pack.image_prompts)
    assert MARS_PLUTO_SQUARE_TENSION_VISUAL_CANON.split()[0] in joined
    assert "coliseum" in joined.lower()
    assert "earth" in joined.lower()
    assert "LEFT" in joined
    assert "RIGHT" in joined
    assert "Pluto" in joined and "Mars" in joined
    assert "\u2647" in joined
    assert "\u2642" in joined
    assert "underworld" in joined.lower() or "reactor-core" in joined.lower()
    assert "frontal" in joined.lower() or "combat heat" in joined.lower()


def test_prompt_disallows_venus_glyph_explicitly() -> None:
    pack = generate_catstyle_prompt_pack(_req(pa="Pluto", pb="Mars"))
    joined = "\n".join(pack.image_prompts)
    assert "Venus glyph" in joined
    assert "\u2640" in joined
    assert "never" in joined.lower()


def test_goofy_drift_negatives_present() -> None:
    pack = generate_catstyle_prompt_pack(_req(pa="Mars", pb="Pluto"))
    joined = "\n".join(pack.image_prompts)
    assert "kawaii" in joined.lower()
    assert "toy" in joined.lower()
    assert "cute mascot" in joined.lower()


def test_negative_prompt_merges_mars_pluto_extras() -> None:
    pack = generate_catstyle_prompt_pack(_req(pa="Mars", pb="Pluto"))
    neg = pack.negative_prompt.lower()
    assert "venus glyph" in neg
    assert "wrong planetary glyph" in neg


def test_compensation_mode_skips_mars_pluto_tension_canon() -> None:
    req = CatstylePromptRequest(
        planet_a="Mars",
        planet_b="Pluto",
        aspect_type="square",
        mode="compensation",
        variants_count=1,
        premium_art_direction=False,
    )
    assert not is_mars_pluto_square_tension("Mars", "Pluto", "square", "compensation")
    pack = generate_catstyle_prompt_pack(req)
    joined = "\n".join(pack.image_prompts)
    assert "[MARS-PLUTO SQUARE TENSION VISUAL CANON v1]" not in joined
