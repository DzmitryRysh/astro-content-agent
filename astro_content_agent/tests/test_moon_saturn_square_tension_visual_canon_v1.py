"""Moon square Saturn (tension) pair-specific visual canon v1."""
from __future__ import annotations

from datetime import date

from astro_content_agent.content.catstyle.moon_saturn_square_tension_visual_canon_v1 import (
    MOON_SATURN_ARENA_PAIR_LOCK,
    MOON_SATURN_SATURN_IDENTITY_HARD_LOCK,
    MOON_SATURN_SQUARE_TENSION_VISUAL_CANON,
    is_moon_saturn_square_tension,
)
from astro_content_agent.content.catstyle.models import CatstylePromptRequest
from astro_content_agent.services.content.catstyle_image_generation_jobs import (
    build_catstyle_image_generation_jobs,
)
from astro_content_agent.services.content.catstyle_prompt_generator import generate_catstyle_prompt_pack


def _req(**kwargs) -> CatstylePromptRequest:
    base = dict(
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        variants_count=1,
        world_template_key="cosmic_zodiac_arena",
        render_style_profile_key="premium_cg_keyart_v1",
        shot_mode="epic_arena_showdown",
        disable_approved_reference_prompt_lock=True,
        disable_arena_reference_auto=True,
    )
    base.update(kwargs)
    return CatstylePromptRequest(**base)


def _blob(pack) -> str:
    return "\n".join(pack.image_prompts)


def test_is_moon_saturn_square_tension_order_independent() -> None:
    assert is_moon_saturn_square_tension("Moon", "Saturn", "square", "tension")
    assert is_moon_saturn_square_tension("Saturn", "Moon", "square", "tension")
    assert not is_moon_saturn_square_tension("Moon", "Saturn", "opposition", "tension")
    assert not is_moon_saturn_square_tension("Moon", "Saturn", "square", "flow")


def test_prompt_includes_canon_marker_and_sickle_weapon() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    assert "[moon-saturn square tension visual canon v1]" in blob
    assert "crescent sickle" in blob
    assert "main weapon" in blob or "primary" in blob


def test_prompt_pillow_cushion_secondary_not_primary() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    assert "secondary" in blob and ("cushion" in blob or "sleep relic" in blob)
    assert "pillow strike" not in blob


def test_saturn_rejects_orange_fire_solar_mars_coding() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    neg = (pack.negative_prompt or "").lower()
    assert "[moon-saturn saturn identity hard lock v1]" in blob
    assert "must not read as sun, mars, or fire" in blob or "must not" in blob and "mars" in blob
    assert "orange" in blob and ("fire" in blob or "fiery" in blob)
    assert "no orange fire aura" in blob or "orange fire aura" in neg
    assert "mars-like" in blob or "mars-like" in neg


def test_saturn_cold_lead_iron_stone_authority() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    assert "lead" in blob and ("iron" in blob or "stone" in blob)
    assert "charcoal" in blob or "lead-gray" in blob or "cold steel" in blob


def test_saturn_lecturer_strategist_enforcer_archetype() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    assert "lecturer" in blob and "strategist" in blob
    assert "psychological enforcer" in blob
    assert "hannibal" in blob or "gustavo" in blob or "polite" in blob
    assert "screaming fire warrior" in blob or "screaming fire" in (pack.negative_prompt or "").lower()


def test_saturn_chain_cane_timekeeper_props() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    assert "chain" in blob
    assert "cane" in blob or "timekeeper" in blob or "pocket watch" in blob


def test_arena_brighter_statues_arcade_asymmetry_visible() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    assert "[moon-saturn arena pair lock v1]" in blob
    assert "clearly visible" in blob
    assert "statue" in blob
    assert "sleep" in blob or "dream" in blob
    assert "time" in blob and ("law" in blob or "fate" in blob)
    assert "warm golden" in blob or "golden arcade" in blob
    assert "asymmetry" in blob or "uneven tiers" in blob
    assert "brighter" in blob or "luminous" in blob
    assert "flat dark semicircle" in blob or "dark semicircle" in blob


def test_prompt_rejects_generic_brawl_and_brute_moon() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    neg = (pack.negative_prompt or "").lower()
    assert "generic brawl" in blob or "generic brawl" in neg
    assert "brute" in blob or "brute warrior" in neg


def test_prompt_excludes_old_visual_correction_patch() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    blob = _blob(pack).lower()
    assert "[moon-saturn visual correction patch v1" not in blob


def test_opposition_does_not_include_square_canon() -> None:
    pack = generate_catstyle_prompt_pack(_req(aspect_type="opposition"))
    assert "[MOON-SATURN SQUARE TENSION VISUAL CANON v1]" not in _blob(pack)


def test_negative_prompt_merges_canon_extras() -> None:
    pack = generate_catstyle_prompt_pack(_req())
    neg = (pack.negative_prompt or "").lower()
    assert "orange fiery solar" in neg or "orange fire aura" in neg
    assert "generic brawl" in neg


def test_canon_module_constants() -> None:
    assert MOON_SATURN_SQUARE_TENSION_VISUAL_CANON.startswith(
        "[MOON-SATURN SQUARE TENSION VISUAL CANON v1]"
    )
    assert MOON_SATURN_SATURN_IDENTITY_HARD_LOCK.startswith("[MOON-SATURN SATURN IDENTITY HARD LOCK v1]")
    assert MOON_SATURN_ARENA_PAIR_LOCK.startswith("[MOON-SATURN ARENA PAIR LOCK v1]")


def test_manual_override_jobs_stay_moon_saturn_square_tension(tmp_path) -> None:
    r = build_catstyle_image_generation_jobs(
        date(2026, 5, 20),
        planet_a_override="Moon",
        planet_b_override="Saturn",
        aspect_type_override="square",
        mode_override="tension",
        shot_mode="epic_arena_showdown",
        render_style_profile_key="premium_cg_keyart_v1",
        disable_approved_reference_auto=True,
        disable_arena_reference_auto=True,
        output_dir=tmp_path / "ms_jobs",
        jobs_count=1,
    )
    assert r.jobs
    assert r.jobs[0].planet_a == "Moon"
    assert r.jobs[0].planet_b == "Saturn"
    assert r.jobs[0].aspect_type == "square"
    assert r.jobs[0].mode == "tension"
    assert r.manual_aspect_override is not None
    prompt = r.jobs[0].prompt_text.lower()
    assert "[moon-saturn square tension visual canon v1]" in prompt
    assert "[moon-saturn saturn identity hard lock v1]" in prompt
    assert "crescent sickle" in prompt
    assert "orange" in prompt and "fire" in prompt
