"""Tests for Catstyle image generation jobs v0 (no APIs)."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from astro_content_agent.content.catstyle.models import (
    CatstyleCandidate,
    CatstyleCandidateRankingResult,
    CatstyleDailyPackResult,
    CatstylePromptPack,
)
from astro_content_agent.content.catstyle.render_style_profiles_v1 import get_render_style_profile
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    CatstyleImageGenerationJobsResult,
    _write_utf8_text,
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
    assert "jupiter_mars_square_tension_approved" in (r.jobs[0].style_reference_image_path or "").replace("\\", "/").lower()
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


def test_build_jobs_jobs_count_one_daily_pack(tmp_path: Path) -> None:
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            editorial_profile="charged",
            output_dir=tmp_path / "jobs1",
            jobs_count=1,
        )
    assert len(r.jobs) == 1
    assert r.jobs[0].prompt_index == 1
    assert r.jobs[0].prompt_text == "prompt line one"
    assert r.jobs[0].shot_role == "hero_poster"
    assert r.jobs[0].job_id == "catstyle-2026-05-02-001"


def test_jobs_count_two_requires_two_prompts(tmp_path: Path) -> None:
    """Without registry refresh, a single-line pack cannot satisfy jobs_count=2."""
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_moon_saturn_square_tension(),
    ):
        with pytest.raises(ValueError, match="requires at least 2"):
            build_catstyle_image_generation_jobs(
                date(2026, 5, 3),
                output_dir=tmp_path / "x",
                jobs_count=2,
                disable_approved_reference_auto=True,
            )


def test_jobs_count_invalid_raises() -> None:
    with pytest.raises(ValueError, match="jobs_count must be"):
        build_catstyle_image_generation_jobs(date(2026, 5, 2), jobs_count=5)


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
    assert manifest["sky_scan_mode"] == "day-window"
    assert manifest["sky_scan_step_hours_utc"] == 2
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


def test_output_jobs_count_one_writes_single_prompt_file(tmp_path: Path) -> None:
    out = tmp_path / "out_one"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_daily_pack",
        return_value=_fake_pack_one_primary(),
    ):
        r = build_catstyle_image_generation_jobs(date(2026, 5, 2), output_dir=out, jobs_count=1)
    assert len(r.jobs) == 1
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert len(manifest["jobs"]) == 1
    assert (out / "job_01_prompt.txt").is_file()
    assert not (out / "job_02_prompt.txt").exists()
    assert "job_02_prompt.txt" not in r.files_written
    assert manifest["style_reference"]["source"] == "approved_registry"
    assert manifest["jobs"][0]["shot_role"] == "hero_poster"
    assert "neg body" in (out / "negative_prompt.txt").read_text(encoding="utf-8")
    assert "anim body" in (out / "animation_prompt.txt").read_text(encoding="utf-8")
    assert "image_generation_jobs.json" in r.files_written


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


def test_parse_manual_aspect_override_accepts_flow() -> None:
    assert parse_manual_aspect_override_fields("Mercury", "Jupiter", "sextile", "flow") == (
        "Mercury",
        "Jupiter",
        "sextile",
        "flow",
    )
    assert parse_manual_aspect_override_fields("Mercury", "Jupiter", "sextile", "FLOW") == (
        "Mercury",
        "Jupiter",
        "sextile",
        "flow",
    )


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
                scan_mode="noon",
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
        "aspect_source": "manual_editorial",
    }
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "approved_registry"
    assert "pluto_mars_approved" in (r.jobs[0].style_reference_image_path or "").replace("\\", "/").lower()

    manifest = json.loads((tmp_path / "ov" / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["manual_aspect_override"]["enabled"] is True
    assert manifest["manual_aspect_override"]["planet_a"] == "Pluto"
    assert manifest["selected_candidate"]["manual_aspect_override"] is True
    assert manifest["secondary_supportive_candidate"] is None
    assert manifest["sky_scan_mode"] == "manual_override"
    assert manifest["sky_scan_step_hours_utc"] is None
    assert manifest["aspect_source"] == "manual_editorial"
    assert manifest["selected_candidate"]["aspect_source"] == "manual_editorial"
    summary = (tmp_path / "ov" / "manifest_summary.txt").read_text(encoding="utf-8")
    assert "Manual aspect override" in summary


def test_manual_override_jobs_count_one_prompt_variant(tmp_path: Path) -> None:
    fake = CatstylePromptPack(
        image_prompts=["only one"],
        image_prompt_shot_roles=["hero_poster"],
        animation_prompt="anim",
        negative_prompt="neg",
        carousel_idea="car",
    )
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_prompt_pack",
        return_value=fake,
    ) as m_pack:
        r = build_catstyle_image_generation_jobs(
            date(2026, 5, 2),
            editorial_profile="charged",
            output_dir=tmp_path / "ov1",
            planet_a_override="Pluto",
            planet_b_override="Mars",
            aspect_type_override="square",
            mode_override="tension",
            jobs_count=1,
            scan_mode="noon",
        )
    req = m_pack.call_args[0][0]
    assert req.variants_count == 1
    assert len(r.jobs) == 1


def test_manual_override_mercury_jupiter_flow_resolves_registry(tmp_path: Path) -> None:
    fake = CatstylePromptPack(
        image_prompts=["mj one", "mj two"],
        image_prompt_shot_roles=["hero_poster", "alternate_action_angle"],
        animation_prompt="anim",
        negative_prompt="neg",
        carousel_idea="car",
    )
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_prompt_pack",
        return_value=fake,
    ):
        r = build_catstyle_image_generation_jobs(
            date(2026, 6, 1),
            editorial_profile="charged",
            output_dir=tmp_path / "mj_flow",
            planet_a_override="Mercury",
            planet_b_override="Jupiter",
            aspect_type_override="sextile",
            mode_override="flow",
        )
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "approved_registry"
    assert r.style_reference_meta.get("registry_key") == "mercury_jupiter_sextile_flow_v1"
    p = (r.jobs[0].style_reference_image_path or "").replace("\\", "/").lower()
    assert "catstyle_mercury_jupiter_sextile_flow_approved" in p
    assert r.jobs[0].mode == "flow"


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
            scan_mode="noon",
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


def test_manual_override_real_prompt_pack_mercury_jupiter_sextile_flow(tmp_path: Path) -> None:
    """Integration: flow mode + registry-backed Mercury/Jupiter sextile."""
    r = build_catstyle_image_generation_jobs(
        date(2026, 6, 1),
        editorial_profile="charged",
        output_dir=tmp_path / "mj_real",
        planet_a_override="Mercury",
        planet_b_override="Jupiter",
        aspect_type_override="sextile",
        mode_override="flow",
    )
    assert len(r.jobs) >= 1
    assert r.jobs[0].prompt_text.strip()
    assert r.jobs[0].mode == "flow"
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("registry_key") == "mercury_jupiter_sextile_flow_v1"


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
    assert Path(r.jobs[0].style_reference_image_path or "").resolve() == Path("C:/refs/pluto_mars_style.png").resolve()
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("source") == "explicit"
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert Path(manifest["jobs"][0]["style_reference_image_path"]).resolve() == Path(
        "C:/refs/pluto_mars_style.png"
    ).resolve()
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
    assert "catstyle_moon_saturn_square_tension_approved" in p


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
    assert "Using approved Catstyle reference image" in out


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


def test_moon_saturn_prompt_text_keeps_unicode_glyphs_no_mojibake(tmp_path: Path) -> None:
    out = tmp_path / "glyph_jobs"
    r = build_catstyle_image_generation_jobs(
        date(2026, 5, 8),
        output_dir=out,
        planet_a_override="Moon",
        planet_b_override="Saturn",
        aspect_type_override="square",
        mode_override="tension",
        shot_mode="epic_arena_showdown",
        editorial_profile="charged",
    )
    assert r.jobs, "expected at least one generated job"
    blob = r.jobs[0].prompt_text
    # Reference glyphs appear as overlay targets in [IDENTITY MARKERS] / canon text (encoding must stay UTF-8).
    assert "\u263e" in blob or "\u263d" in blob or "☾" in blob
    assert "\u2644" in blob or "♄" in blob
    assert "—" in blob
    assert "â˜¾" not in blob
    assert "â™„" not in blob
    assert "â€”" not in blob


def test_utf8_writer_roundtrip_preserves_glyphs_and_em_dash(tmp_path: Path) -> None:
    p = tmp_path / "roundtrip_prompt.txt"
    body = "Moon ☾ attacks Saturn ♄ — diagonal swing."
    _write_utf8_text(p, body)
    got = p.read_text(encoding="utf-8")
    assert "☾" in got
    assert "♄" in got
    assert "—" in got
    assert "â˜¾" not in got
    assert "â™„" not in got
    assert "â€”" not in got


def test_manual_override_day_window_merges_timing_when_scan_matches(tmp_path: Path) -> None:
    c = CatstyleCandidate(
        planet_a="Jupiter",
        planet_b="Mercury",
        aspect_type="sextile",
        mode_recommendation="flow",
        visual_score=6,
        emotional_score=6,
        comedy_score=6,
        clarity_score=6,
        total_score=30,
        reason="unit",
        recommended_scene_angle="x",
        orb=0.5,
        source="seed",
        closest_hour_utc=10,
        window_first_seen_hour_utc=0,
        window_last_seen_hour_utc=22,
        window_samples_seen=12,
    )
    fake = CatstylePromptPack(
        image_prompts=["a"],
        image_prompt_shot_roles=["hero_poster"],
        animation_prompt="anim",
        negative_prompt="neg",
        carousel_idea="car",
    )
    out = tmp_path / "mw"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_prompt_pack",
        return_value=fake,
    ):
        with patch(
            "astro_content_agent.services.content.catstyle_manual_override_timing.scan_catstyle_sky_aspect_windows",
            return_value=CatstyleCandidateRankingResult(ranked=[c], unsupported=[]),
        ) as m_scan:
            r = build_catstyle_image_generation_jobs(
                date(2026, 6, 10),
                editorial_profile="charged",
                output_dir=out,
                planet_a_override="Mercury",
                planet_b_override="Jupiter",
                aspect_type_override="sextile",
                mode_override="flow",
                scan_mode="day-window",
                step_hours=2,
            )
    m_scan.assert_called_once()
    assert r.selected_candidate is not None
    assert r.selected_candidate.get("manual_override_sky_timing_match") is True
    assert r.selected_candidate.get("closest_hour_utc") == 10
    assert r.selected_candidate.get("window_start_hour_utc") == 0
    assert r.selected_candidate.get("window_end_hour_utc") == 22
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["sky_scan_mode"] == "day-window"
    assert manifest["sky_scan_step_hours_utc"] == 2


def test_manual_override_day_window_honest_miss_when_scan_empty(tmp_path: Path) -> None:
    fake = CatstylePromptPack(
        image_prompts=["a"],
        image_prompt_shot_roles=["hero_poster"],
        animation_prompt="anim",
        negative_prompt="neg",
        carousel_idea="car",
    )
    out = tmp_path / "mw_miss"
    with patch(
        "astro_content_agent.services.content.catstyle_image_generation_jobs.generate_catstyle_prompt_pack",
        return_value=fake,
    ):
        with patch(
            "astro_content_agent.services.content.catstyle_manual_override_timing.scan_catstyle_sky_aspect_windows",
            return_value=CatstyleCandidateRankingResult(ranked=[], unsupported=[]),
        ):
            r = build_catstyle_image_generation_jobs(
                date(2026, 6, 10),
                editorial_profile="charged",
                output_dir=out,
                planet_a_override="Mercury",
                planet_b_override="Jupiter",
                aspect_type_override="sextile",
                mode_override="flow",
                scan_mode="day-window",
            )
    assert r.selected_candidate.get("manual_override_sky_timing_match") is False
    assert r.selected_candidate.get("closest_hour_utc") is None
    manifest = json.loads((out / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["sky_scan_mode"] == "day-window"


def test_sun_uranus_manual_override_attaches_approved_reference_image(tmp_path: Path) -> None:
    r = build_catstyle_image_generation_jobs(
        date(2099, 9, 1),
        output_dir=tmp_path / "sun_uranus_jobs",
        planet_a_override="Sun",
        planet_b_override="Uranus",
        aspect_type_override="conjunction",
        mode_override="tension",
        jobs_count=1,
        scan_mode="noon",
        render_style_profile_key="premium_comic_poster_v2",
        world_template_key="cosmic_zodiac_arena",
        shot_mode="epic_arena_showdown",
    )
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("approved_reference_used") is True
    assert r.style_reference_meta.get("registry_key") == "sun_uranus_conjunction_tension_v1"
    ref_path = r.style_reference_meta.get("approved_reference_image_path")
    assert ref_path
    assert r.jobs[0].style_reference_image_path == ref_path
    assert "sun_uranus" in ref_path.replace("\\", "/").lower()
    assert r.message and "Using approved Catstyle reference image" in r.message
    manifest = json.loads((tmp_path / "sun_uranus_jobs" / "image_generation_jobs.json").read_text(encoding="utf-8"))
    sr = manifest["style_reference"]
    assert sr["approved_reference_used"] is True
    assert sr["approved_reference_registry_key"] == "sun_uranus_conjunction_tension_v1"
    assert sr["approved_reference_image_path"] == ref_path
    assert sr["style_reference_image_path"] == ref_path
    assert manifest["jobs"][0]["style_reference_image_path"] == ref_path


def test_explicit_style_reference_overrides_approved_registry(tmp_path: Path) -> None:
    from astro_content_agent.tests.catstyle_reference_test_helpers import write_valid_reference_png

    explicit = tmp_path / "operator_ref.png"
    write_valid_reference_png(explicit)
    r = build_catstyle_image_generation_jobs(
        date(2099, 9, 2),
        output_dir=tmp_path / "explicit_ref",
        planet_a_override="Sun",
        planet_b_override="Uranus",
        aspect_type_override="conjunction",
        mode_override="tension",
        jobs_count=1,
        scan_mode="noon",
        style_reference_image_path=str(explicit),
    )
    resolved = str(explicit.resolve())
    assert r.style_reference_meta.get("source") == "explicit"
    assert r.style_reference_meta.get("approved_reference_used") is False
    assert r.jobs[0].style_reference_image_path == resolved
    manifest = json.loads((tmp_path / "explicit_ref" / "image_generation_jobs.json").read_text(encoding="utf-8"))
    assert manifest["style_reference"]["style_reference_image_path"] == resolved


def test_unstable_pair_without_approved_reference_does_not_set_used(tmp_path: Path) -> None:
    r = build_catstyle_image_generation_jobs(
        date(2099, 9, 3),
        output_dir=tmp_path / "unstable",
        planet_a_override="Jupiter",
        planet_b_override="Moon",
        aspect_type_override="square",
        mode_override="tension",
        jobs_count=1,
        scan_mode="noon",
    )
    assert r.jobs[0].style_reference_image_path is None
    assert r.style_reference_meta is not None
    assert r.style_reference_meta.get("approved_reference_used") is False
    assert r.style_reference_meta.get("reference_tier") == "none"
    assert r.style_reference_meta.get("source") == "none"
