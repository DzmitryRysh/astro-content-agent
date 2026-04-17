"""Tests for Money Astrology Knowledge Layer v2.

Covers:
- VENUS_MONEY_BEHAVIOR: all 12 signs present with required fields
- MONEY_FROM_EFFORT: all 12 signs present with required fields
- PLANET_FUNCTIONS: all 10 planets have descriptions
- HOUSE_ENERGY_SUMMARIES: all 12 houses present
- get_save_or_spend_strategy: earth/water -> farmer, fire/air -> predator, scorpio -> mixed
- interpret_2nd_house_ruler: output structure and content
- MoneyKnowledgeBase.to_dict: all required keys, all 12 signs covered
- MoneyKnowledgeBase.to_prompt_hints: non-empty structured string
- Service injection: money_knowledge_v2 present in planner payload
"""

from __future__ import annotations

import types
import uuid
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.content.money_astrology import (
    HOUSE_ENERGY_SUMMARIES,
    MONEY_FROM_EFFORT,
    PLANET_FUNCTIONS,
    SIGN_ELEMENTS,
    STRATEGY_DESCRIPTIONS,
    VENUS_MONEY_BEHAVIOR,
    MoneyKnowledgeBase,
    get_save_or_spend_strategy,
    interpret_2nd_house_ruler,
)

ALL_SIGNS = list(SIGN_ELEMENTS.keys())
EARTH_WATER_SIGNS = [s for s, el in SIGN_ELEMENTS.items() if el in ("earth", "water") and s != "scorpio"]
FIRE_AIR_SIGNS = [s for s, el in SIGN_ELEMENTS.items() if el in ("fire", "air")]


def _make_astro_day(signal_keys: list[str]) -> AstroDayPayload:
    return AstroDayPayload(
        day=date(2026, 4, 2),
        engine_version="test-1.0",
        generated_at=datetime(2026, 4, 2, 8, 0, 0),
        signals=[
            TransitSignal(key=k, headline=f"Signal: {k}", summary="test", intensity=0.7)
            for k in signal_keys
        ],
    )


# ---------------------------------------------------------------------------
# VENUS_MONEY_BEHAVIOR
# ---------------------------------------------------------------------------

class TestVenusMoneyBehavior:
    REQUIRED_FIELDS = ["unconscious_pattern", "spending_style", "risk", "content_hook"]

    def test_all_12_signs_present(self) -> None:
        assert set(VENUS_MONEY_BEHAVIOR.keys()) == set(ALL_SIGNS)

    def test_all_required_fields(self) -> None:
        for sign, profile in VENUS_MONEY_BEHAVIOR.items():
            for f in self.REQUIRED_FIELDS:
                assert f in profile, f"Venus {sign} missing field {f}"
                assert profile[f], f"Venus {sign} field {f} is empty"

    def test_capricorn_mentions_fear(self) -> None:
        risk = VENUS_MONEY_BEHAVIOR["capricorn"]["risk"].lower()
        assert "страх" in risk or "не заслуживаю" in risk

    def test_pisces_mentions_fog_or_unclear(self) -> None:
        hook = VENUS_MONEY_BEHAVIOR["pisces"]["content_hook"].lower()
        assert "туман" in hook or "неясн" in hook or "размыт" in hook

    def test_aries_mentions_burning_or_fast(self) -> None:
        hook = VENUS_MONEY_BEHAVIOR["aries"]["content_hook"].lower()
        assert "быстро" in hook or "сгорают" in hook or "интересн" in hook


# ---------------------------------------------------------------------------
# MONEY_FROM_EFFORT
# ---------------------------------------------------------------------------

class TestMoneyFromEffort:
    REQUIRED_FIELDS = ["style", "phrase", "grows_when"]

    def test_all_12_signs_present(self) -> None:
        assert set(MONEY_FROM_EFFORT.keys()) == set(ALL_SIGNS)

    def test_all_required_fields(self) -> None:
        for sign, profile in MONEY_FROM_EFFORT.items():
            for f in self.REQUIRED_FIELDS:
                assert f in profile, f"Effort {sign} missing field {f}"

    def test_phrases_start_with_money(self) -> None:
        for sign, profile in MONEY_FROM_EFFORT.items():
            assert "Деньги" in profile["phrase"] or "деньги" in profile["phrase"], \
                f"Effort phrase for {sign} should mention деньги"

    def test_gemini_mentions_communication(self) -> None:
        phrase = MONEY_FROM_EFFORT["gemini"]["phrase"].lower()
        assert "общени" in phrase or "информаци" in phrase or "контакт" in phrase


# ---------------------------------------------------------------------------
# PLANET_FUNCTIONS
# ---------------------------------------------------------------------------

class TestPlanetFunctions:
    REQUIRED_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

    def test_all_planets_present(self) -> None:
        for planet in self.REQUIRED_PLANETS:
            assert planet in PLANET_FUNCTIONS, f"Missing planet: {planet}"

    def test_all_non_empty(self) -> None:
        for planet, func in PLANET_FUNCTIONS.items():
            assert func, f"Planet {planet} function is empty"

    def test_venus_mentions_beauty_or_harmony(self) -> None:
        assert "красоту" in PLANET_FUNCTIONS["venus"] or "гармони" in PLANET_FUNCTIONS["venus"]

    def test_saturn_mentions_structure(self) -> None:
        assert "структур" in PLANET_FUNCTIONS["saturn"]


# ---------------------------------------------------------------------------
# HOUSE_ENERGY_SUMMARIES
# ---------------------------------------------------------------------------

class TestHouseEnergySummaries:
    def test_all_12_houses_present(self) -> None:
        for i in range(1, 13):
            assert i in HOUSE_ENERGY_SUMMARIES, f"Missing house {i}"

    def test_house_2_mentions_money(self) -> None:
        assert "деньги" in HOUSE_ENERGY_SUMMARIES[2].lower()

    def test_house_10_mentions_career(self) -> None:
        assert "карьер" in HOUSE_ENERGY_SUMMARIES[10].lower()

    def test_house_8_mentions_transformation_or_risk(self) -> None:
        entry = HOUSE_ENERGY_SUMMARIES[8].lower()
        assert "трансформ" in entry or "риск" in entry or "чужие" in entry


# ---------------------------------------------------------------------------
# get_save_or_spend_strategy
# ---------------------------------------------------------------------------

class TestSaveOrSpendStrategy:
    @pytest.mark.parametrize("sign", EARTH_WATER_SIGNS)
    def test_earth_water_signs_are_farmer(self, sign: str) -> None:
        assert get_save_or_spend_strategy(sign) == "farmer", f"{sign} should be farmer"

    @pytest.mark.parametrize("sign", FIRE_AIR_SIGNS)
    def test_fire_air_signs_are_predator(self, sign: str) -> None:
        assert get_save_or_spend_strategy(sign) == "predator", f"{sign} should be predator"

    def test_scorpio_is_mixed(self) -> None:
        assert get_save_or_spend_strategy("scorpio") == "mixed"

    def test_case_insensitive(self) -> None:
        assert get_save_or_spend_strategy("Taurus") == "farmer"
        assert get_save_or_spend_strategy("ARIES") == "predator"

    def test_unknown_sign_returns_mixed(self) -> None:
        assert get_save_or_spend_strategy("unknown_sign") == "mixed"

    def test_all_signs_return_valid_strategy(self) -> None:
        valid = {"farmer", "predator", "mixed"}
        for sign in ALL_SIGNS:
            result = get_save_or_spend_strategy(sign)
            assert result in valid, f"{sign} returned invalid strategy: {result}"


# ---------------------------------------------------------------------------
# interpret_2nd_house_ruler
# ---------------------------------------------------------------------------

class TestInterpret2ndHouseRuler:
    def test_contains_planet_name(self) -> None:
        result = interpret_2nd_house_ruler("venus", 7)
        assert "Венера" in result

    def test_contains_house_number(self) -> None:
        result = interpret_2nd_house_ruler("saturn", 10)
        assert "10" in result

    def test_contains_house_energy(self) -> None:
        result = interpret_2nd_house_ruler("saturn", 10)
        assert "карьер" in result.lower() or "10" in result

    def test_contains_money_route_phrase(self) -> None:
        result = interpret_2nd_house_ruler("mercury", 3)
        assert "маршрут" in result.lower() or "денеж" in result.lower()

    def test_all_known_planets_work(self) -> None:
        for planet in PLANET_FUNCTIONS:
            result = interpret_2nd_house_ruler(planet, 5)
            assert len(result) > 50, f"Result for {planet} seems too short"

    def test_all_houses_work(self) -> None:
        for house in range(1, 13):
            result = interpret_2nd_house_ruler("venus", house)
            assert str(house) in result


# ---------------------------------------------------------------------------
# MoneyKnowledgeBase.to_dict
# ---------------------------------------------------------------------------

class TestMoneyKnowledgeBaseToDict:
    REQUIRED_KEYS = [
        "venus_money_patterns",
        "save_or_spend_strategies",
        "earning_effort_styles",
        "career_money_angles",
        "content_angle_templates",
        "formula_engine_example",
        "planet_functions",
        "house_energy_summaries",
    ]

    def test_all_required_keys_present(self) -> None:
        d = MoneyKnowledgeBase.to_dict()
        for key in self.REQUIRED_KEYS:
            assert key in d, f"Missing key: {key}"

    def test_venus_patterns_has_all_12_signs(self) -> None:
        d = MoneyKnowledgeBase.to_dict()
        assert set(d["venus_money_patterns"].keys()) == set(ALL_SIGNS)

    def test_earning_effort_has_all_12_signs(self) -> None:
        d = MoneyKnowledgeBase.to_dict()
        assert set(d["earning_effort_styles"].keys()) == set(ALL_SIGNS)

    def test_save_or_spend_has_all_12_signs(self) -> None:
        d = MoneyKnowledgeBase.to_dict()
        assert set(d["save_or_spend_strategies"].keys()) == set(ALL_SIGNS)

    def test_content_angle_templates_non_empty(self) -> None:
        d = MoneyKnowledgeBase.to_dict()
        assert len(d["content_angle_templates"]) >= 6

    def test_formula_engine_example_is_string(self) -> None:
        d = MoneyKnowledgeBase.to_dict()
        assert isinstance(d["formula_engine_example"], str)
        assert len(d["formula_engine_example"]) > 50

    def test_planet_functions_has_10_planets(self) -> None:
        d = MoneyKnowledgeBase.to_dict()
        assert len(d["planet_functions"]) == 10

    def test_house_energy_has_12_entries(self) -> None:
        d = MoneyKnowledgeBase.to_dict()
        assert len(d["house_energy_summaries"]) == 12


# ---------------------------------------------------------------------------
# MoneyKnowledgeBase.to_prompt_hints
# ---------------------------------------------------------------------------

class TestMoneyKnowledgeBaseToPromptHints:
    def test_non_empty(self) -> None:
        hints = MoneyKnowledgeBase.to_prompt_hints()
        assert len(hints) > 200

    def test_contains_v2_header(self) -> None:
        hints = MoneyKnowledgeBase.to_prompt_hints()
        assert "MONEY KNOWLEDGE v2" in hints

    def test_contains_farmer_predator(self) -> None:
        hints = MoneyKnowledgeBase.to_prompt_hints()
        assert "фермер" in hints.lower() or "farmer" in hints.lower()
        assert "хищник" in hints.lower() or "predator" in hints.lower()

    def test_contains_venus_reference(self) -> None:
        hints = MoneyKnowledgeBase.to_prompt_hints()
        assert "Венер" in hints

    def test_contains_formula_engine_example(self) -> None:
        hints = MoneyKnowledgeBase.to_prompt_hints()
        assert "маршрут" in hints.lower() or "Управитель" in hints


# ---------------------------------------------------------------------------
# Service injection: money_knowledge_v2 in planner payload
# ---------------------------------------------------------------------------

class TestPlannerV2Injection:
    def test_planner_injects_money_knowledge_v2(self) -> None:
        from astro_content_agent.services.strategy.planner import StrategyPlannerService

        captured: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured.update(input_payload)
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
        astro_signal_record = MagicMock()
        astro_signal_record.id = str(uuid.uuid4())
        astro_signal_record.payload = astro_day.model_dump(mode="json")

        mock_deps = MagicMock()
        mock_deps.brand_repo.get.return_value = brand
        mock_deps.pillar_repo.list_for_brand.return_value = []
        mock_deps.pillar_balancer.get_recent_pillar_usage.return_value = {}
        mock_deps.pillar_balancer.to_prompt_hint.return_value = ""
        mock_deps.plan_repo.upsert.return_value = MagicMock(
            id=str(uuid.uuid4()),
            payload={"day": "2026-04-02", "items": [], "notes": []},
        )
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = astro_signal_record

        svc = StrategyPlannerService(runner=mock_runner, deps=mock_deps)
        mock_db = MagicMock()
        svc.generate_day_plan(
            db=mock_db,
            brand_profile_id=brand.id,
            day=date(2026, 4, 2),
            generate_astro_if_missing=False,
        )

        assert "money_knowledge_v2" in captured, "money_knowledge_v2 must be in planner payload"
        v2 = captured["money_knowledge_v2"]
        assert "venus_money_patterns" in v2
        assert "save_or_spend_strategies" in v2
        assert "earning_effort_styles" in v2
        assert "content_angle_templates" in v2
        assert len(v2["content_angle_templates"]) >= 6
