"""Catstyle Square Conflict Law v1 tests."""
from __future__ import annotations

from astro_content_agent.content.catstyle.arena_pool_registry_v1 import DEFAULT_ARENA_POOL_KEY
from astro_content_agent.content.catstyle.catstyle_clean_refs_v1 import (
    CLEAN_PROMPT_MAX_CHARS,
    build_clean_refs_image_prompt,
    generate_catstyle_clean_refs_prompt_pack,
)
from astro_content_agent.content.catstyle.catstyle_square_conflict_law_v1 import (
    SQUARE_CONFLICT_LAW_BLOCK,
    build_square_conflict_law_block,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest


def test_mars_uranus_clean_refs_square_conflict_law() -> None:
    prompt = build_clean_refs_image_prompt(
        "Mars",
        "Uranus",
        "square",
        "tension",
        arena_environment_reference_attached=True,
        arena_pool_key=DEFAULT_ARENA_POOL_KEY,
    )
    low = prompt.lower()
    assert "[square conflict law v1]" in low
    assert "attack vs resistance" in low or "force vs obstruction" in low
    assert "explosive impact" in low or "shield vs lightning" in low
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS
    assert "catstyle visual composition hardlock" not in low


def test_venus_saturn_clean_refs_square_conflict_law() -> None:
    prompt = build_clean_refs_image_prompt("Venus", "Saturn", "square", "tension")
    low = prompt.lower()
    assert "[square conflict law v1]" in low
    assert "venus square saturn" in low
    assert "cold restriction" in low or "chains" in low
    assert "peaceful romantic" in low
    assert len(prompt) <= CLEAN_PROMPT_MAX_CHARS


def test_mercury_neptune_clean_refs_keeps_signal_vs_fog_conflict() -> None:
    prompt = build_clean_refs_image_prompt("Mercury", "Neptune", "square", "tension")
    low = prompt.lower()
    assert "[square conflict law v1]" in low
    assert "signal" in low and ("fog" in low or "tide" in low or "dissolv" in low)
    assert "dissolving wave-force" in low or "glyph beam distorted" in low or "dream-force" in low

    pack = generate_catstyle_clean_refs_prompt_pack(
        CatstylePromptRequest(
            planet_a="Mercury",
            planet_b="Neptune",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            clean_refs_mode=True,
        )
    )
    neg = pack.negative_prompt.lower()
    assert "calm face-off" in neg
    assert "polite magical exchange" in neg
    assert "no visible conflict" in neg


def test_square_conflict_law_block_exact_marker() -> None:
    assert SQUARE_CONFLICT_LAW_BLOCK.startswith("[SQUARE CONFLICT LAW v1]")
    block = build_square_conflict_law_block("Mars", "Uranus", "square", "tension")
    assert block.startswith("[SQUARE CONFLICT LAW v1]")
    assert build_square_conflict_law_block("Mars", "Uranus", "trine", "tension") == ""
