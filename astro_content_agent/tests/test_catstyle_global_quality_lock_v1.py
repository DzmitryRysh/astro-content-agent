"""Global Catstyle premium quality lock in prompts and negatives."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _req() -> CatstylePromptRequest:
    return CatstylePromptRequest(
        planet_a="Mercury",
        planet_b="Jupiter",
        aspect_type="sextile",
        mode="flow",
        variants_count=1,
        premium_art_direction=True,
        world_template_key="cosmic_zodiac_arena",
        render_style_profile_key="premium_comic_poster_v2",
    )


def test_global_lock_in_image_prompt() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    joined = "\n".join(pack.image_prompts)
    assert "[CATSTYLE GLOBAL QUALITY LOCK v1]" in joined
    assert "premium cinematic comic-poster" in joined.lower()
    assert "coliseum" in joined.lower()
    assert "earth" in joined.lower()
    assert "zodiac" in joined.lower()
    assert "rim lighting" in joined.lower() or "rim-impact" in joined.lower()


def test_global_anti_storybook_negatives() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    neg = pack.negative_prompt.lower()
    assert "storybook" in neg
    assert "children-book" in neg or "children-book style" in neg
    assert "watercolor" in neg
    assert "toy-like" in neg
