"""Premium cosmic zodiac arena environment baseline in assembled prompts."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_premium_cg_epic_arena_injects_environment_baseline() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            premium_art_direction=True,
            world_template_key="cosmic_zodiac_arena",
            render_style_profile_key="premium_cg_keyart_v1",
            shot_mode="epic_arena_showdown",
            disable_approved_reference_prompt_lock=True,
        )
    )
    low = "\n".join(pack.image_prompts).lower()
    assert "[cosmic zodiac arena premium environment v1]" in low
    assert "[cosmic zodiac arena premium coliseum v1]" in low
    assert "[cosmic zodiac arena premium sky v1]" in low
    assert "[cosmic zodiac arena premium spectacle v1]" in low
    assert "colorful milky way" in low or "galaxy band" in low
    assert "illuminated arches" in low
    assert "[shot/composition profile v4 - epic_arena_showdown]" in low
