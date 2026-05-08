"""Tests for Catstyle image generation jobs v0 (no APIs)."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.models import CatstyleDailyPackResult
from astro_content_agent.content.catstyle.render_style_profiles_v1 import get_render_style_profile
from astro_content_agent.content.catstyle.models import CatstylePromptPack
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    CatstyleImageGenerationJobsResult,
    build_catstyle_image_generation_jobs,
    parse_manual_aspect_override_fields,
)
from astro_content_agent.services.content.catstyle_post_package import build_catstyle_post_package


def _fake_pack_one_primary() -> CatstyleDailyPackResult:
    primary = {
        "planet_a": "Jupiter",
        "planet_b": "Mars",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 38,
        "orb": 1.2,
        "source": "seed",
        "editorial_bonus": 5,
        "editorial_selection_score": 43,
    }
    secondary = {
        "planet_a": "Saturn",
        "planet_b": "Venus",
        "aspect_type": "sextile",
        "mode_recommendation": "compensation",
        "total_score": 46,
        "source": "deep",
    }
    return CatstyleDailyPackResult(
        date="2026-05-02",
        scan_mode="day-window",
        step_hours=2,
        editorial_profile="charged",
        ranked_candidates_count=2,
        selected_count=1,
        ranked_candidates=[dict(primary)],
        selected_candidates=[primary],
        primary_candidate=primary,
        secondary_supportive_candidate=secondary,
        prompt_packs=[
            {
                "image_prompts": ["prompt line one", "prompt line two"],
                "image_prompt_shot_roles": ["hero_poster", "alternate_action_angle"],
                "animation_prompt": "anim body",
                "negative_prompt": "neg body",
                "carousel_idea": "carousel body",
                "art_direction_profile": {
                    "version": "catstyle-art-direction-v0",
                    "energy": "charged",
                    "editorial_profile": "charged",
                    "mode": "tension",
                    "planet_a": "Jupiter",
                    "planet_b": "Mars",
                    "skin_a": None,
                    "skin_b": None,
                },
                "world_template_profile": {"template_key": "cosmic_zodiac_arena", "display_name": "Cosmic Zodiac Arena"},
                "scene_template_profile": {"template_key": "mars_spartan_cliff_kick", "display_name": "Kick"},
                "render_style_profile": get_render_style_profile("premium_comic_poster_v1").model_dump(mode="json"),
            }
        ],
    )


def _fake_pack_moon_saturn_square_tension() -> CatstyleDailyPackResult:
    primary = {
        "planet_a": "Moon",
        "planet_b": "Saturn",
        "aspect_type": "square",
        "mode_recommendation": "tension",
        "total_score": 40,
        "orb": 0.9,
        "source": "seed",
        "editorial_selection_score": 40,
    }
    return CatstyleDailyPackResult(
        date="2026-05-03",
        scan_mode="day-window",
        step_hours=2,
        editorial_profile="charged",
        ranked_candidates_count=1,
        selected_count=1,
        ranked_candidates=[dict(primary)],
        selected_candidates=[primary],
        primary_candidate=primary,
        secondary_supportive_candidate=None,
        prompt_packs=[
            {
                "image_prompts": ["moon saturn prompt"],
                "image_prompt_shot_roles": ["hero_poster"],
                "animation_prompt": "anim",
                "negative_prompt": "neg",
                "carousel_idea": "car",
                "art_direction_profile": None,
                "world_template_profile": None,
                "scene_template_profile": None,
                "render_style_profile": get_render_style_profile("premium_comic_poster_v1").model_dump(mode="json"),
            }
        ],
    )


def _fake_pack_empty() -> CatstyleDailyPackResult:
    return CatstyleDailyPackResult(
        date="2026-06-01",
        scan_mode="day-window",
        step_hours=2,
        editorial_profile="charged",
        ranked_candidates_count=0,
        selected_count=0,
        ranked_candidates=[],
        selected_candidates=[],
        prompt_packs=[],
    )


def test_build_jobs_two_prompts_all_pending(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            editorial_profile="charged",
            output_dir=tmp_path / "jobs",
        )
    assert isinstance(r, CatstyleImageGenerationJobsResult)
    assert len(r.jobs) == 2
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "approved_registry"
    assert r.jobs[0].style_reference_image_path
    assert "jupiter_mars_approved" in (r.jobs[0].style_reference_image_path or "").replace("\\", "/").lower()
    assert all(j.status == "pending" for j in r.jobs)
    assert r.jobs[0].planet_a == "Jupiter" and r.jobs[0].planet_b == "Mars"
    assert r.jobs[0].prompt_index == 1
    assert r.jobs[0].shot_role == "hero_poster"
    assert r.jobs[1].shot_role == "alternate_action_angle"
    assert r.jobs[0].prompt_text == "prompt line one"
    assert r.jobs[0].negative_prompt == "neg body"
    assert r.jobs[0].animation_prompt == "anim body"
    assert r.jobs[0].carousel_idea == "carousel body"
    assert r.jobs[0].art_direction_profile is not None
    assert r.jobs[0].art_direction_profile.get("energy") == "charged"
    assert r.jobs[0].world_template_key == "cosmic_zodiac_arena"
    assert r.jobs[0].scene_template_key == "mars_spartan_cliff_kick"
    assert r.jobs[0].world_template_profile is not None
    assert r.jobs[0].scene_template_profile is not None
    assert r.jobs[0].render_style_profile_key == "premium_comic_poster_v1"
    assert r.jobs[0].render_style_profile is not None
    assert r.jobs[0].selection_score == 43
    assert r.jobs[0].orb == pytest.approx(1.2)
    assert r.jobs[0].job_id == "catstyle-2026-05-02-001"
    assert "jupiter_mars_square" in r.jobs[0].suggested_output_name


def test_variants_per_prompt_duplicates_jobs(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            variants_per_prompt=2,
            output_dir=tmp_path / "v",
        )
    assert len(r.jobs) == 4
    assert r.jobs[0].prompt_index == 1 and r.jobs[0].variant_index == 0
    assert r.jobs[1].prompt_index == 1 and r.jobs[1].variant_index == 1
    assert r.jobs[0].prompt_text == r.jobs[1].prompt_text
    assert r.jobs[0].shot_role == "hero_poster" and r.jobs[1].shot_role == "hero_poster"
    assert r.jobs[2].prompt_index == 2 and r.jobs[2].variant_index == 0
    assert r.jobs[2].shot_role == "alternate_action_angle"


def test_output_writes_manifest_and_prompt_files(tmp_path: Path) -> None:
    out = tmp_path / "out"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(date(2026, 5, 2), output_dir=out)
    assert (out / "image_generation_jobs.json").is_file()
    assert (out / "job_01_prompt.txt").read_text(encoding="utf-8").strip() == "prompt line one"
    assert (out / "job_02_prompt.txt").read_text(encoding="utf-8").strip() == "prompt line two"
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["style_reference"]["source"] == "approved_registry"
    assert manifest["jobs"][0]["shot_role"] == "hero_poster"
    assert manifest["jobs"][1]["shot_role"] == "alternate_action_angle"
    assert "neg body" in (out / "negative_prompt.txt").read_text(encoding="utf-8")
    assert "anim body" in (out / "animation_prompt.txt").read_text(encoding="utf-8")
    summary = (out / "manifest_summary.txt").read_text(encoding="utf-8")
    assert "Saturn" in summary and "Venus" in summary
    assert "Secondary supportive" in summary
    assert "Style reference" in summary
    assert "image_generation_jobs.json" in r.files_written
    assert "manifest_summary.txt" in r.files_written


def test_no_selected_returns_empty_jobs_no_files(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_empty(),
    ):
        r = build_catstyle_image_generation_jobs(date(2026, 6, 1), output_dir=tmp_path / "empty")
    assert r.jobs == []
    assert r.message
    assert r.files_written == []
    assert not (tmp_path / "empty").exists()


def test_pack_passes_skins_to_daily_pack(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ) as m:
        build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            output_dir=tmp_path / "s",
            skin_a=None,
            skin_b="spartan_king",
        )
    m.assert_called_once()
    kw = m.call_args.kwargs
    assert kw.get("skin_b") == "spartan_king"


def test_parse_manual_aspect_override_partial_raises() -> None:
    with pytest.raises(ValueError, match="all four flags"):
        parse_manual_aspect_override_fields("Pluto", None, "square", "tension")
    with pytest.raises(ValueError, match="all four flags"):
        parse_manual_aspect_override_fields(None, None, None, "tension")


def test_parse_manual_aspect_override_invalid_mode() -> None:
    with pytest.raises(ValueError, match="--mode must be one of"):
        parse_manual_aspect_override_fields("Pluto", "Mars", "square", "bananas")


def test_manual_override_build_jobs_and_manifest(tmp_path: Path) -> None:
    fake = CatstylePromptPack(
        image_prompts=["override prompt one", "override prompt two"],
        image_prompt_shot_roles=["hero_poster", "alternate_action_angle"],
        animation_prompt="anim",
        negative_prompt="neg",
        carousel_idea="car",
    )
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_prompt_pack",
        return_value=fake,
    ) as m_pack:
        with patch(
            "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack"
        ) as m_daily:
            r = build_catstyle_image_generation_jobs(
                date(2026, 5, 2),
                editorial_profile="charged",
                output_dir=tmp_path / "ov",
                planet_a_override="Pluto",
                planet_b_override="Mars",
                aspect_type_override="square",
                mode_override="tension",
            )
    m_daily.assert_not_called()
    m_pack.assert_called_once()
    req = m_pack.call_args[0][0]
    assert req.planet_a == "Pluto" and req.planet_b == "Mars"
    assert req.aspect_type == "square" and req.mode == "tension"

    assert len(r.jobs) == 2
    assert r.jobs[0].planet_a == "Pluto" and r.jobs[0].planet_b == "Mars"
    assert r.jobs[0].aspect_type == "square" and r.jobs[0].mode == "tension"
    assert r.jobs[0].source == "manual_override"
    assert r.selected_candidate is not None
    assert r.selected_candidate.get("source") == "manual_override"
    assert r.secondary_supportive_candidate is None
    assert r.manual_aspect_override == {
        "enabled": True,
        "planet_a": "Pluto",
        "planet_b": "Mars",
        "aspect_type": "square",
        "mode": "tension",
    }
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "approved_registry"
    assert "pluto_mars_approved" in (r.jobs[0].style_reference_image_path or "").replace("\\", "/").lower()

    manifest = json.loads((tmp_path / "ov" / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["manual_aspect_override"]["enabled"] is True
    assert manifest["manual_aspect_override"]["planet_a"] == "Pluto"
    assert manifest["selected_candidate"]["manual_aspect_override"] is True
    assert manifest["secondary_supportive_candidate"] is None
    summary = (tmp_path / "ov" / "manifest_summary.txt").read_text(encoding="utf-8")
    assert "Manual aspect override" in summary


def test_manual_override_post_package_roundtrip(tmp_path: Path) -> None:
    fake = CatstylePromptPack(
        image_prompts=["only"],
        image_prompt_shot_roles=["hero_poster"],
        animation_prompt="a",
        negative_prompt="n",
        carousel_idea="c",
    )
    out = tmp_path / "jobs_ov"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_prompt_pack",
        return_value=fake,
    ):
        build_catstyle_image_generation_jobs(
            date(2026, 7, 15),
            editorial_profile="charged",
            output_dir=out,
            planet_a_override="Venus",
            planet_b_override="Pluto",
            aspect_type_override="opposition",
            mode_override="tension",
        )
    mp = out / "image_generation_jobs.json"
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    job_file = str(manifest["jobs"][0]["suggested_output_name"])
    gen = tmp_path / "gen_ov"
    gen.mkdir()
    (gen / job_file).write_bytes(b"\x89PNG\r\n\x1a\n")

    pkg = build_catstyle_post_package(mp, generated_images_dir=gen)
    assert pkg.manual_aspect_override is not None
    assert pkg.manual_aspect_override["planet_a"] == "Venus"
    assert pkg.manual_aspect_override["aspect_type"] == "opposition"
    assert pkg.aspect_summary and "Venus" in pkg.aspect_summary


def test_manual_override_real_prompt_pack_pluto_mars_square(tmp_path: Path) -> None:
    """Integration: real deterministic prompt generator for a supported pair (no sky scan)."""
    r = build_catstyle_image_generation_jobs(
        date(2026, 5, 2),
        editorial_profile="charged",
        output_dir=tmp_path / "real",
        planet_a_override="Pluto",
        planet_b_override="Mars",
        aspect_type_override="square",
        mode_override="tension",
    )
    assert len(r.jobs) >= 1
    assert r.jobs[0].prompt_text.strip()
    assert r.manual_aspect_override is not None


def test_manifest_includes_style_reference_image_path(tmp_path: Path) -> None:
    out = tmp_path / "jobs_ref"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            output_dir=out,
            style_reference_image_path="C:/refs/pluto_mars_style.png",
        )
    assert r.jobs[0].style_reference_image_path == "C:/refs/pluto_mars_style.png"
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "explicit"
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["jobs"][0]["style_reference_image_path"] == "C:/refs/pluto_mars_style.png"
    assert manifest["style_reference"]["source"] == "explicit"


def test_approved_reference_auto_resolves_moon_saturn(tmp_path: Path) -> None:
    out = tmp_path / "jobs_ms"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_moon_saturn_square_tension(),
    ):
        r = build_catstyle_image_generation_jobs(date(2026, 5, 3), output_dir=out)
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "approved_registry"
    assert r.style_reference_meta.get("registry_key") == "moon_saturn_square_tension_v1"
    p = (r.jobs[0].style_reference_image_path or "").replace("\\", "/").lower()
    assert "catstyle_moon_saturn_approved" in p


def test_disable_approved_reference_auto_skips_registry(tmp_path: Path) -> None:
    out = tmp_path / "jobs_noauto"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_moon_saturn_square_tension(),
    ):
        r = build_catstyle_image_generation_jobs(
            date(2026, 5, 3),
            output_dir=out,
            disable_approved_reference_auto=True,
        )
    assert r.jobs[0].style_reference_image_path is None
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "none"
    assert r.style_reference_meta.get("auto_resolve_disabled") is True


def test_build_catstyle_image_generation_jobs_cli_shows_auto_resolved_reference(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "build_catstyle_image_generation_jobs.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_image_jobs_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    old = sys.argv[:]
    try:
        with patch(
            "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
            return_value=_fake_pack_moon_saturn_square_tension(),
        ):
            sys.argv = [
                "build_catstyle_image_generation_jobs.py",
                "--date",
                "2026-05-03",
                "--output-dir",
                str(tmp_path / "cli_out"),
            ]
            assert mod.main() == 0
    finally:
        sys.argv = old
    out = capsys.readouterr().out
    assert "approved reference auto-resolved:" in out


def test_build_catstyle_image_generation_jobs_cli_explicit_style_reference_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "build_catstyle_image_generation_jobs.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_image_jobs_cli2", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    old = sys.argv[:]
    try:
        with patch(
            "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
            return_value=_fake_pack_one_primary(),
        ):
            sys.argv = [
                "build_catstyle_image_generation_jobs.py",
                "--date",
                "2026-05-02",
                "--output-dir",
                str(tmp_path / "cli_exp"),
                "--style-reference-image",
                "D:/explicit/ref.png",
            ]
            assert mod.main() == 0
    finally:
        sys.argv = old
    assert "explicit style reference:" in capsys.readouterr().out


def test_build_catstyle_image_generation_jobs_cli_no_reference_when_disabled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "build_catstyle_image_generation_jobs.py"
    spec = importlib.util.spec_from_file_location("_build_catstyle_image_jobs_cli3", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    old = sys.argv[:]
    try:
        with patch(
            "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
            return_value=_fake_pack_moon_saturn_square_tension(),
        ):
            sys.argv = [
                "build_catstyle_image_generation_jobs.py",
                "--date",
                "2026-05-03",
                "--output-dir",
                str(tmp_path / "cli_nr"),
                "--disable-approved-reference-auto",
            ]
            assert mod.main() == 0
    finally:
        sys.argv = old
    assert "no reference selected" in capsys.readouterr().out
