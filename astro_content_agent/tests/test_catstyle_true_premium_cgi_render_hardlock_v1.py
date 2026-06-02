"""True premium CGI render hardlock tests (clean refs + premium_cg_keyart_v1)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.arena_pool_registry_v1 import DEFAULT_ARENA_POOL_KEY
from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
    CLEAN_PROMPT_MAX_CHARS,
    build_clean_refs_image_prompt,
    generate_catstyle_clean_refs_prompt_pack,
)
from astro_content_agent.content.catstyle.catstyle_true_premium_cgi_render_hardlock_v1 import (
    CLEAN_REFS_TRUE_PREMIUM_CGI_RENDER_HARDLOCK_BLOCK,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def test_clean_refs_true_premium_cgi_render_hardlock_mars_uranus() -> None:
    prompt = build_clean_refs_image_prompt(
        "Mars",
        "Uranus",
        "square",
        "tension",
        arena_environment_reference_attached=True,
        arena_pool_key=DEFAULT_ARENA_POOL_KEY,
    )
    low = prompt.lower()
    assert "[true premium cgi render hardlock v1]" in low
    assert "high-end cinematic 3d cgi key art" in low
    assert "physically based rendering" in low
    assert "pbr metal" in low
    assert "sculpted 3d fur" in low
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
    assert "catstyle visual composition hardlock" not in low


def test_clean_refs_true_premium_cgi_render_hardlock_venus_saturn_negatives() -> None:
    prompt = build_clean_refs_image_prompt("Venus", "Saturn", "square", "tension")
    assert CLEAN_REFS_TRUE_PREMIUM_CGI_RENDER_HARDLOCK_BLOCK in prompt
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS

    pack = generate_catstyle_clean_refs_prompt_pack(
        CatstylePromptRequest(
            planet_a="Venus",
            planet_b="Saturn",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            clean_refs_mode=True,
        )
    )
    neg = pack.negative_prompt.lower()
    assert "digital painting look" in neg
    assert "painted fantasy illustration" in neg
    assert "non-3d illustration" in neg


def test_premium_cg_keyart_includes_true_premium_cgi_render_hardlock() -> None:
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Jupiter",
            planet_b="Mars",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            render_style_profile_key="premium_cg_keyart_v1",
        )
    )
    low = pack.image_prompts[0].lower()
    assert "[true premium cgi render hardlock v1]" in low
    assert "physically based rendering" in low
    neg = pack.negative_prompt.lower()
    assert "digital painting look" in neg
    assert "non-3d illustration" in neg
