"""Tests for Money Astrology Knowledge Layer v1.

Covers:
- extract_planets_from_signal_key: correct extraction from various key formats
- MoneyAstrologyContext.from_astro_day: correct planet/distortion/hook derivation
- to_prompt_hint: structured non-empty output with expected sections
- to_dict: all required keys present
- Planet profiles: all known planets have complete profiles
- Service-layer injection: money_astrology_context present in planner/caption/reel payloads
- Strategy angle preference: money-oriented hints present when known money planets are in play
"""

from __future__ import annotations

import types
import uuid
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.content.money_astrology import (
    EARNING_CHANNELS,
    HOUSE_MONEY_PROFILES,
    MONEY_CONTENT_FORMULA,
    MONEY_PROBLEM_TYPES,
    PLANET_MONEY_PROFILES,
    MoneyAstrologyContext,
    extract_planets_from_signal_key,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_astro_day(signal_keys: list[str]) -> AstroDayPayload:
    signals = [
        TransitSignal(
            key=k,
            headline=f"Signal: {k}",
            summary="Test signal",
            intensity=0.7,
        )
        for k in signal_keys
    ]
    return AstroDayPayload(
        day=date(2026, 4, 2),
        engine_version="test-1.0",
        generated_at=datetime(2026, 4, 2, 8, 0, 0),
        signals=signals,
    )


# ---------------------------------------------------------------------------
# extract_planets_from_signal_key
# ---------------------------------------------------------------------------

class TestExtractPlanets:
    def test_single_planet(self) -> None:
        assert extract_planets_from_signal_key("mercury_retrograde") == ["mercury"]

    def test_two_planets_aspect(self) -> None:
        result = extract_planets_from_signal_key("venus_square_saturn")
        assert result == ["venus", "saturn"]

    def test_trine_aspect(self) -> None:
        result = extract_planets_from_signal_key("moon_trine_jupiter")
        assert result == ["moon", "jupiter"]

    def test_conjunction(self) -> None:
        result = extract_planets_from_signal_key("sun_conjunct_uranus")
        assert result == ["sun", "uranus"]

    def test_opposition(self) -> None:
        result = extract_planets_from_signal_key("mars_opposition_neptune")
        assert result == ["mars", "neptune"]

    def test_no_planet(self) -> None:
        result = extract_planets_from_signal_key("void_of_course")
        assert result == []

    def test_all_lowercase(self) -> None:
        result = extract_planets_from_signal_key("VENUS_TRINE_JUPITER")
        assert result == ["venus", "jupiter"]

    def test_no_duplicates(self) -> None:
        result = extract_planets_from_signal_key("venus_square_venus")
        assert result == ["venus"]

    def test_pluto_included(self) -> None:
        result = extract_planets_from_signal_key("pluto_trine_moon")
        assert "pluto" in result
        assert "moon" in result

    def test_all_known_planets(self) -> None:
        for planet in ["moon", "sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]:
            result = extract_planets_from_signal_key(f"{planet}_retrograde")
            assert planet in result, f"Expected {planet} to be extracted"


# ---------------------------------------------------------------------------
# PLANET_MONEY_PROFILES completeness
# ---------------------------------------------------------------------------

class TestPlanetMoneyProfiles:
    REQUIRED_PLANETS = ["moon", "sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
    REQUIRED_FIELDS = ["archetype", "distortion", "healthy", "content_hook"]

    def test_all_planets_present(self) -> None:
        for planet in self.REQUIRED_PLANETS:
            assert planet in PLANET_MONEY_PROFILES, f"Missing profile for {planet}"

    def test_all_fields_present(self) -> None:
        for planet, profile in PLANET_MONEY_PROFILES.items():
            for field in self.REQUIRED_FIELDS:
                assert field in profile, f"Planet {planet} missing field {field}"
                assert profile[field], f"Planet {planet} field {field} is empty"

    def test_venus_distortion_mentions_underpricing(self) -> None:
        assert "underpric" in PLANET_MONEY_PROFILES["venus"]["distortion"].lower()

    def test_saturn_distortion_mentions_fear(self) -> None:
        assert "fear" in PLANET_MONEY_PROFILES["saturn"]["distortion"].lower()

    def test_neptune_distortion_mentions_fog(self) -> None:
        assert "fog" in PLANET_MONEY_PROFILES["neptune"]["distortion"].lower()

    def test_moon_distortion_mentions_poverty_fear(self) -> None:
        assert "poverty" in PLANET_MONEY_PROFILES["moon"]["distortion"].lower()


# ---------------------------------------------------------------------------
# MoneyAstrologyContext.from_astro_day
# ---------------------------------------------------------------------------

class TestFromAstroDay:
    def test_single_signal_venus_saturn(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert "venus" in ctx.planets_in_play
        assert "saturn" in ctx.planets_in_play

    def test_distortions_populated(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert len(ctx.active_distortions) >= 2
        distortion_text = " ".join(ctx.active_distortions).lower()
        assert "venus" in distortion_text or "saturn" in distortion_text

    def test_archetypes_populated(self) -> None:
        astro_day = _make_astro_day(["mars_opposition_neptune"])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert any("mars" in a.lower() or "neptune" in a.lower() for a in ctx.active_archetypes)

    def test_hooks_populated(self) -> None:
        astro_day = _make_astro_day(["moon_trine_jupiter"])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert len(ctx.active_hooks) >= 2

    def test_empty_signals(self) -> None:
        astro_day = _make_astro_day([])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert ctx.planets_in_play == []
        assert ctx.active_distortions == []

    def test_no_duplicate_planets(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn", "venus_trine_jupiter"])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert ctx.planets_in_play.count("venus") == 1

    def test_problem_types_always_present(self) -> None:
        astro_day = _make_astro_day(["mercury_retrograde"])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert len(ctx.problem_types) > 0

    def test_unknown_signal_key_no_crash(self) -> None:
        astro_day = _make_astro_day(["void_of_course_moon_energy"])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        # moon should still be extracted
        assert "moon" in ctx.planets_in_play


# ---------------------------------------------------------------------------
# to_prompt_hint
# ---------------------------------------------------------------------------

class TestToPromptHint:
    def test_empty_context_returns_empty_string(self) -> None:
        astro_day = _make_astro_day([])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert ctx.to_prompt_hint() == ""

    def test_hint_contains_planet_names(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        hint = MoneyAstrologyContext.from_astro_day(astro_day).to_prompt_hint()
        assert "Venus" in hint
        assert "Saturn" in hint

    def test_hint_contains_money_context_header(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        hint = MoneyAstrologyContext.from_astro_day(astro_day).to_prompt_hint()
        assert "MONEY ASTROLOGY CONTEXT" in hint

    def test_hint_contains_6_step_formula(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        hint = MoneyAstrologyContext.from_astro_day(astro_day).to_prompt_hint()
        assert "6" in hint or "шаг" in hint.lower() or "Формула" in hint

    def test_hint_contains_house_references(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        hint = MoneyAstrologyContext.from_astro_day(astro_day).to_prompt_hint()
        assert "2 дом" in hint or "house_2" in hint.lower() or "дом" in hint

    def test_hint_contains_distortions_section(self) -> None:
        astro_day = _make_astro_day(["mars_opposition_neptune"])
        hint = MoneyAstrologyContext.from_astro_day(astro_day).to_prompt_hint()
        assert "искажени" in hint.lower() or "distortion" in hint.lower()


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

class TestToDict:
    REQUIRED_KEYS = [
        "planets_in_play",
        "active_archetypes",
        "active_distortions",
        "active_hooks",
        "problem_types",
        "content_formula",
        "house_2_angle",
        "house_8_angle",
    ]

    def test_all_required_keys_present(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        d = MoneyAstrologyContext.from_astro_day(astro_day).to_dict()
        for key in self.REQUIRED_KEYS:
            assert key in d, f"Missing key: {key}"

    def test_content_formula_is_string(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        d = MoneyAstrologyContext.from_astro_day(astro_day).to_dict()
        assert isinstance(d["content_formula"], str)
        assert len(d["content_formula"]) > 50

    def test_house_angles_are_strings(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        d = MoneyAstrologyContext.from_astro_day(astro_day).to_dict()
        assert isinstance(d["house_2_angle"], str)
        assert isinstance(d["house_8_angle"], str)

    def test_lists_are_lists(self) -> None:
        astro_day = _make_astro_day(["venus_square_saturn"])
        d = MoneyAstrologyContext.from_astro_day(astro_day).to_dict()
        for key in ["planets_in_play", "active_archetypes", "active_distortions", "active_hooks", "problem_types"]:
            assert isinstance(d[key], list), f"{key} should be a list"


# ---------------------------------------------------------------------------
# MONEY_CONTENT_FORMULA
# ---------------------------------------------------------------------------

class TestMoneyContentFormula:
    def test_formula_has_6_steps(self) -> None:
        steps = [str(i) for i in range(1, 7)]
        for step in steps:
            assert step in MONEY_CONTENT_FORMULA, f"Step {step} missing from formula"

    def test_formula_mentions_risk(self) -> None:
        assert "Риск" in MONEY_CONTENT_FORMULA or "риск" in MONEY_CONTENT_FORMULA

    def test_formula_mentions_practice(self) -> None:
        assert "Практик" in MONEY_CONTENT_FORMULA


# ---------------------------------------------------------------------------
# House profiles
# ---------------------------------------------------------------------------

class TestHouseProfiles:
    def test_2nd_house_present(self) -> None:
        assert "2nd" in HOUSE_MONEY_PROFILES
        assert "content_angle" in HOUSE_MONEY_PROFILES["2nd"]

    def test_8th_house_present(self) -> None:
        assert "8th" in HOUSE_MONEY_PROFILES
        assert "content_angle" in HOUSE_MONEY_PROFILES["8th"]

    def test_2nd_house_mentions_personal_money(self) -> None:
        angle = HOUSE_MONEY_PROFILES["2nd"]["content_angle"].lower()
        assert "личн" in angle or "собств" in angle or "personal" in angle

    def test_8th_house_mentions_shared_or_investment(self) -> None:
        angle = HOUSE_MONEY_PROFILES["8th"]["content_angle"].lower()
        assert "партнёр" in angle or "инвест" in angle or "shared" in angle


# ---------------------------------------------------------------------------
# Integration: money_astrology_context appears in planner input payload
# ---------------------------------------------------------------------------

class TestPlannerMoneyContextInjection:
    """Verify money_astrology_context key is present in the payload sent to AI."""

    def test_planner_injects_money_context(self) -> None:
        from astro_content_agent.services.strategy.planner import StrategyPlannerService

        captured_payload: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured_payload.update(input_payload)
            from astro_content_agent.schemas.strategy import DayPlanPayload, DayPlanItem
            return DayPlanPayload(
                day=date(2026, 4, 2),
                items=[
                    DayPlanItem(
                        slot=1,
                        format="post",
                        primary_angle="test angle",
                        creative_brief="test brief",
                        signal_keys=["venus_square_saturn"],
                        content_pillar="education",
                        face_led_preference=False,
                    )
                ],
            )

        mock_runner = MagicMock()
        mock_runner.run_json.side_effect = fake_run_json

        brand = types.SimpleNamespace(
            id=str(uuid.uuid4()),
            name="Test",
            description="Test brand",
            tone_preset="educational_warm",
            banned_terms=[],
            default_hashtags=[],
            face_led_preferred=0,
            content_language="ru",
        )

        astro_day = _make_astro_day(["venus_square_saturn"])
        from astro_content_agent.schemas.astro import AstroSignalRecordResponse

        mock_deps = MagicMock()
        mock_deps.brand_repo.get.return_value = brand
        mock_deps.pillar_repo.list_for_brand.return_value = []
        mock_deps.pillar_balancer.get_recent_pillar_usage.return_value = {}
        mock_deps.pillar_balancer.to_prompt_hint.return_value = ""
        mock_deps.plan_repo.upsert.return_value = MagicMock(
            id=str(uuid.uuid4()),
            payload={"day": "2026-04-02", "items": [], "notes": []},
        )

        astro_signal_record = MagicMock()
        astro_signal_record.id = str(uuid.uuid4())
        astro_signal_record.payload = astro_day.model_dump(mode="json")
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = astro_signal_record

        svc = StrategyPlannerService(runner=mock_runner, deps=mock_deps)

        mock_db = MagicMock()
        svc.generate_day_plan(
            db=mock_db,
            brand_profile_id=brand.id,
            day=date(2026, 4, 2),
            generate_astro_if_missing=False,
        )

        assert "money_astrology_context" in captured_payload, \
            "money_astrology_context must be injected into planner input payload"
        ctx = captured_payload["money_astrology_context"]
        assert "planets_in_play" in ctx
        assert "venus" in ctx["planets_in_play"]
        assert "saturn" in ctx["planets_in_play"]
        assert "content_formula" in ctx


class TestCaptionServiceMoneyContextInjection:
    """Verify money_astrology_context key is present in caption service payload."""

    def test_caption_injects_money_context(self) -> None:
        from astro_content_agent.services.content.caption_service import CaptionService

        captured_payload: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured_payload.update(input_payload)
            from astro_content_agent.schemas.drafts import PostDraftPayload
            return PostDraftPayload(
                title="Test",
                hook="Тест зацепка",
                caption="Тест текст поста",
                cta="Напиши 👇",
                hashtags=["#астрология"],
                voice_note="test",
                metadata={},
            )

        mock_runner = MagicMock()
        mock_runner.run_json.side_effect = fake_run_json

        brand = types.SimpleNamespace(
            id=str(uuid.uuid4()),
            name="Test",
            description="Test brand",
            tone_preset="educational_warm",
            banned_terms=[],
            default_hashtags=[],
            face_led_preferred=0,
            content_language="ru",
        )

        astro_day = _make_astro_day(["mars_opposition_neptune"])
        astro_signal_record = MagicMock()
        astro_signal_record.id = str(uuid.uuid4())
        astro_signal_record.payload = astro_day.model_dump(mode="json")

        mock_deps = MagicMock()
        mock_deps.brand_repo.get.return_value = brand
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = astro_signal_record
        mock_deps.drafts_repo.create.return_value = MagicMock(id=str(uuid.uuid4()))

        with patch(
            "astro_content_agent.services.content.caption_service.AntiRepeatContext.from_recent_drafts"
        ) as mock_anti:
            mock_anti.return_value = MagicMock(to_prompt_hint=lambda: "")
            svc = CaptionService(runner=mock_runner, deps=mock_deps)
            mock_db = MagicMock()
            svc.generate_post_draft(
                db=mock_db,
                brand_profile_id=brand.id,
                day=date(2026, 4, 2),
                content_plan=None,
                plan_slot=None,
            )

        assert "money_astrology_context" in captured_payload
        ctx = captured_payload["money_astrology_context"]
        assert "mars" in ctx["planets_in_play"]
        assert "neptune" in ctx["planets_in_play"]
