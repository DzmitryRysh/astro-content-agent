"""Tests for global aspect visual composition hardlocks."""
from __future__ import annotations

from astro_content_agent.content.catstyle.catstyle_aspect_staging_locks_v1 import (
    build_visual_composition_hardlock_layer,
)


def test_visual_composition_hardlock_layer_includes_all_blocks() -> None:
    layer = build_visual_composition_hardlock_layer()
    low = layer.lower()
    assert "[catstyle visual composition hardlock v1]" in low
    assert "[catstyle arena scale lock v2]" in low
    assert "[catstyle camera / framing lock v1]" in low
    assert "[catstyle premium cgi render lock v1]" in low
    assert "[catstyle environment dominance v1]" in low
    assert "three visible tiers" in low
    assert "painterly" in low or "painted poster feel" in low
    assert "physically based materials" in low
