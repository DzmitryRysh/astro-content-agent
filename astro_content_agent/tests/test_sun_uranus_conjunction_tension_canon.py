"""Sun conjunct Uranus (tension) pair-specific visual canon and glyph staging."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.content.catstyle.pair_flag_glyph_resolution_v1 import (
    resolved_pair_flag_glyph_system_block,
)
from astro_content_agent.content.catstyle.sun_uranus_conjunction_tension_canon_v1 import (
    SUN_URANUS_CONJUNCTION_TENSION_VISUAL_CANON,
    is_sun_uranus_conjunction_tension,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _req(*, pa: str = "Sun", pb: str = "Uranus") -> CatstylePromptRequest:
    return CatstylePromptRequest(
        planet_a=pa,
        planet_b=pb,
        aspect_type="conjunction",
        mode="tension",
        variants_count=1,
        premium_art_direction=True,
        world_template_key="cosmic_zodiac_arena",
        render_style_profile_key="premium_comic_poster_v2",
        shot_mode="epic_arena_showdown",
    )


def test_is_sun_uranus_conjunction_tension_detector() -> None:
    assert is_sun_uranus_conjunction_tension("Sun", "Uranus", "conjunction", "tension")
    assert not is_sun_uranus_conjunction_tension("Sun", "Uranus", "square", "tension")
    assert not is_sun_uranus_conjunction_tension("Sun", "Uranus", "conjunction", "flow")


def test_resolved_flags_sun_left_uranus_right() -> None:
    txt = resolved_pair_flag_glyph_system_block("Uranus", "Sun", "conjunction", "tension")
    assert "Left/port faction banner = Sun" in txt
    assert "right/starboard faction banner = Uranus" in txt
    assert "\u2609" in txt
    assert "\u2645" in txt


def test_prompt_includes_pair_canon_and_fusion_language() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    joined = "\n".join(pack.image_prompts)
    assert "[SUN-URANUS CONJUNCTION TENSION VISUAL CANON v1]" in joined
    assert "solar flare" in joined.lower()
    assert "lightning" in joined.lower()
    assert "fusion" in joined.lower() or "overload" in joined.lower()
    assert "shockwave" in joined.lower() or "shock" in joined.lower()
    assert "coliseum" in joined.lower()
    assert "earth" in joined.lower()


def test_prompt_rejects_storybook_and_static_argument() -> None:
    pack = generate_catstyle_prompt_pack(_req(pa="Sun", pb="Uranus"))
    joined = "\n".join(pack.image_prompts)
    assert "storybook" in joined.lower()
    assert "children-book" in joined.lower() or "children-book style" in joined.lower()
    assert "watercolor" in joined.lower()
    assert "pointing at each other" in joined.lower() or "merely pointing" in joined.lower()
    assert "static" in joined.lower()


def test_prompt_requires_canonical_glyphs() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    joined = "\n".join(pack.image_prompts)
    assert "\u2609" in joined
    assert "\u2645" in joined
    assert "Sun glyph" in joined or "Sun (\u2609)" in joined


def test_negative_prompt_includes_pair_and_global_anti_storybook() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    neg = pack.negative_prompt.lower()
    assert "storybook" in neg
    assert "watercolor" in neg
    assert "pointing at each other" in neg or "static face-off" in neg
    assert "trickster" in neg or "yellow cat" in neg
