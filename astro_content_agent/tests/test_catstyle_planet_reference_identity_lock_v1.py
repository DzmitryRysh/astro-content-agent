"""Tests for planet-reference identity hardlocks and premium CGI anti-painterly wording."""
from __future__ import annotations

from pathlib import Path

import pytest

from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
    APPROVED_PLANET_REFERENCE_LOCK_MARKER,
    ApprovedPlanetReferenceEntry,
    write_planet_registry_entries,
)
from astro_content_agent.content.catstyle.catstyle_aspect_staging_locks_v1 import (
    CATSTYLE_PREMIUM_CGI_RENDER_LOCK_BLOCK,
    build_visual_composition_hardlock_layer,
)
from astro_content_agent.content.catstyle.catstyle_planet_reference_identity_lock_v1 import (
    NEPTUNE_ANTI_GENERIC_IDENTITY_BLOCK,
    NEPTUNE_PREMIUM_IDENTITY_HARDLOCK_BLOCK,
    PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER,
    URANUS_FEATURE_HARDLOCK_BLOCK,
    build_planet_reference_identity_hardlock_layer,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_prompt_generator import (
    _IMAGE_PROMPT_SAFE_MAX_CHARS,
    generate_catstyle_prompt_pack,
)


def test_premium_cgi_lock_rejects_painterly_and_requires_cinematic_3d() -> None:
    low = CATSTYLE_PREMIUM_CGI_RENDER_LOCK_BLOCK.lower()
    assert "painted poster feel" in low
    assert "hand-painted fantasy illustration" in low
    assert "matte painting look" in low
    assert "brush-texture rendering" in low
    assert "storybook shading" in low
    assert "physically based materials" in low
    assert "sculpted volumetric character rendering" in low
    assert "polished game-cinematic finish" in low


def test_visual_composition_layer_includes_strengthened_cgi() -> None:
    layer = build_visual_composition_hardlock_layer().lower()
    assert "physically based materials" in layer
    assert "dry canvas feel" in layer


def test_identity_hardlock_injects_per_planet_blocks(tmp_path: Path) -> None:
    neptune_png = tmp_path / "neptune.png"
    mercury_png = tmp_path / "mercury.png"
    neptune_png.write_bytes(b"n")
    mercury_png.write_bytes(b"m")
    meta = {
        "planet_a": {
            "planet": "Neptune",
            "used": True,
            "image_path": str(neptune_png),
        },
        "planet_b": {
            "planet": "Mercury",
            "used": True,
            "image_path": str(mercury_png),
        },
    }
    layer = build_planet_reference_identity_hardlock_layer("Neptune", "Mercury", meta)
    assert PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER in layer
    assert "[PLANET A IDENTITY HARDLOCK — Neptune]" in layer
    assert "[PLANET B IDENTITY HARDLOCK — Mercury]" in layer
    assert NEPTUNE_ANTI_GENERIC_IDENTITY_BLOCK in layer
    assert NEPTUNE_PREMIUM_IDENTITY_HARDLOCK_BLOCK in layer
    assert "flat monochrome blue fur" in layer.lower()
    assert "generic colored cat" in layer.lower()
    assert "normal house-cat face" in layer.lower()


def test_mars_uranus_identity_layer_includes_uranus_feature_hardlock(tmp_path: Path) -> None:
    mars_png = tmp_path / "mars.png"
    uranus_png = tmp_path / "uranus.png"
    mars_png.write_bytes(b"m")
    uranus_png.write_bytes(b"u")
    meta = {
        "planet_a": {"planet": "Mars", "used": True, "image_path": str(mars_png)},
        "planet_b": {"planet": "Uranus", "used": True, "image_path": str(uranus_png)},
    }
    layer = build_planet_reference_identity_hardlock_layer("Mars", "Uranus", meta)
    assert URANUS_FEATURE_HARDLOCK_BLOCK in layer
    assert "orbital electric ring" in layer.lower()


def test_neptune_mercury_square_prompt_priority_and_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reg = tmp_path / "approved_planet_references.json"
    neptune_png = tmp_path / "neptune.png"
    mercury_png = tmp_path / "mercury.png"
    neptune_png.write_bytes(b"n")
    mercury_png.write_bytes(b"m")
    write_planet_registry_entries(
        reg,
        [
            ApprovedPlanetReferenceEntry(
                registry_key="neptune_v1",
                planet="Neptune",
                image_path=str(neptune_png),
                priority=100,
                active=True,
            ),
            ApprovedPlanetReferenceEntry(
                registry_key="mercury_v1",
                planet="Mercury",
                image_path=str(mercury_png),
                priority=100,
                active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        "astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1.approved_planet_references_json_path",
        lambda: reg,
    )
    pack = generate_catstyle_prompt_pack(
        CatstylePromptRequest(
            planet_a="Neptune",
            planet_b="Mercury",
            aspect_type="square",
            mode="tension",
            variants_count=1,
            use_planet_reference_auto=True,
            render_style_profile_key="premium_cg_keyart_v1",
        )
    )
    blob = pack.image_prompts[0]
    low = blob.lower()
    assert PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER in blob
    assert NEPTUNE_ANTI_GENERIC_IDENTITY_BLOCK in blob
    assert "just a blue cat" in low
    assert "[catstyle visual composition hardlock v1]" in low
    assert "[catstyle premium cgi render lock v1]" in low
    assert "[tense aspect choreography v2 - square]" in low
    comp_ix = low.find("[catstyle visual composition hardlock v1]")
    identity_ix = low.find(PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER.lower())
    tense_ix = low.find("[tense aspect choreography v2 - square]")
    scene_ix = low.find("scene beat:")
    assert comp_ix >= 0 and identity_ix > comp_ix
    assert tense_ix > identity_ix
    assert scene_ix > tense_ix
    assert APPROVED_PLANET_REFERENCE_LOCK_MARKER in blob
    assert len(blob) <= _IMAGE_PROMPT_SAFE_MAX_CHARS
