"""Tests for aspect behavior cards: matching, context building, service injection."""
from __future__ import annotations

import types
import uuid
from datetime import date, datetime
from unittest.mock import MagicMock

from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.content.aspect_behavior_cards import (
    ASPECT_BEHAVIOR_CARD_REGISTRY,
    AspectBehaviorCardsContext,
    MARS_SATURN_CARD,
    pair_key_from_planet_names,
    pair_key_from_signal_key,
    parse_aspect_type_from_signal_key,
    polarity_nuance_ru,
)


def _signal(
    key: str,
    *,
    polarity: str | None = "tense",
    orb: float | None = 1.0,
    signal_class: str = "foreground",
) -> TransitSignal:
    return TransitSignal(
        key=key,
        headline=key.replace("-", " "),
        summary="test",
        intensity=0.8,
        aspect_polarity=polarity,
        orb=orb,
        signal_class=signal_class,
    )


def _day(*signals: TransitSignal) -> AstroDayPayload:
    return AstroDayPayload(
        day=date(2026, 4, 16),
        engine_version="v1.real",
        generated_at=datetime(2026, 4, 16, 12, 0, 0),
        signals=list(signals),
    )


class TestPairKeyAndAspectParsing:
    def test_pair_key_both_orders_hyphen(self) -> None:
        assert pair_key_from_signal_key("mars-square-saturn") == "mars_saturn"
        assert pair_key_from_signal_key("saturn-square-mars") == "mars_saturn"

    def test_pair_key_underscore(self) -> None:
        assert pair_key_from_signal_key("mars_opposition_saturn") == "mars_saturn"

    def test_pair_key_conjunction(self) -> None:
        assert pair_key_from_signal_key("mars-conjunction-saturn") == "mars_saturn"
        assert pair_key_from_signal_key("saturn-conjunct-mars") == "mars_saturn"

    def test_pair_key_trine_sextile(self) -> None:
        assert pair_key_from_signal_key("mars-trine-saturn") == "mars_saturn"
        assert pair_key_from_signal_key("saturn-sextile-mars") == "mars_saturn"

    def test_pair_key_from_planet_names_symmetric(self) -> None:
        assert pair_key_from_planet_names("Saturn", "Mars") == "mars_saturn"

    def test_parse_aspect_square(self) -> None:
        assert parse_aspect_type_from_signal_key("mars-square-saturn") == "square"

    def test_parse_aspect_conjunct_normalized(self) -> None:
        assert parse_aspect_type_from_signal_key("saturn-conjunct-mars") == "conjunction"

    def test_parse_aspect_opposition(self) -> None:
        assert parse_aspect_type_from_signal_key("saturn-opposition-mars") == "opposition"

    def test_polarity_nuance_variants(self) -> None:
        assert "гармоничный" in polarity_nuance_ru("harmonious", "trine").lower()
        assert "напряжённый" in polarity_nuance_ru("tense", "square").lower()
        assert "нейтральный" in polarity_nuance_ru("neutral", "conjunction").lower()


class TestRegistry:
    def test_mars_saturn_card_registered(self) -> None:
        assert "mars_saturn" in ASPECT_BEHAVIOR_CARD_REGISTRY
        assert ASPECT_BEHAVIOR_CARD_REGISTRY["mars_saturn"].pair_key == "mars_saturn"
        assert "Марс–Сатурн" in MARS_SATURN_CARD.core_tension or "Марс" in MARS_SATURN_CARD.core_tension


class TestAspectBehaviorCardsContext:
    def test_empty_when_no_mars_saturn(self) -> None:
        day = _day(_signal("sun-trine-moon"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is False
        assert d["matches"] == []

    def test_match_when_mars_saturn_present(self) -> None:
        day = _day(_signal("mars-square-saturn", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert "mars_saturn" in d["matched_pair_keys"]
        assert len(d["matches"]) == 1
        m0 = d["matches"][0]
        assert m0["pair_key"] == "mars_saturn"
        assert m0["signal_key"] == "mars-square-saturn"
        assert m0["aspect_type"] == "square"
        assert m0["aspect_polarity"] == "tense"
        assert m0["card"]["title"] == MARS_SATURN_CARD.title
        assert len(m0["card"]["language_bank"]) >= 3

    def test_dedupes_same_pair_twice(self) -> None:
        day = _day(
            _signal("mars-square-saturn"),
            _signal("saturn-opposition-mars"),
        )
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        assert len(ctx.matches) == 1

    def test_card_serialization_round_trip(self) -> None:
        day = _day(_signal("mars-trine-saturn", polarity="harmonious"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        assert ctx.to_dict()["matches"][0]["card"]["pair_key"] == "mars_saturn"


class TestServiceInjection:
    def test_planner_payload_includes_aspect_behavior_cards_context(self) -> None:
        from astro_content_agent.services.strategy.planner import StrategyPlannerService

        captured: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured.update(input_payload)
            from astro_content_agent.schemas.strategy import DayPlanItem, DayPlanPayload

            return DayPlanPayload(
                day=date(2026, 4, 16),
                items=[
                    DayPlanItem(
                        slot=1,
                        format="post",
                        primary_angle="x",
                        creative_brief="y",
                        signal_keys=["mars-square-saturn"],
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
            description="d",
            tone_preset="sharp_witty",
            banned_terms=[],
            default_hashtags=[],
            face_led_preferred=0,
            content_language="ru",
        )

        astro_day = _day(_signal("mars-square-saturn"))
        mock_deps = MagicMock()
        mock_deps.brand_repo.get.return_value = brand
        mock_deps.pillar_repo.list_for_brand.return_value = []
        mock_deps.pillar_balancer.get_recent_pillar_usage.return_value = {}
        mock_deps.pillar_balancer.to_prompt_hint.return_value = ""
        mock_deps.plan_repo.upsert.return_value = MagicMock(
            id=str(uuid.uuid4()),
            payload={"day": "2026-04-16", "items": [], "notes": []},
        )
        astro_signal_record = MagicMock()
        astro_signal_record.id = str(uuid.uuid4())
        astro_signal_record.payload = astro_day.model_dump(mode="json")
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = astro_signal_record

        svc = StrategyPlannerService(runner=mock_runner, deps=mock_deps)
        svc.generate_day_plan(
            db=MagicMock(),
            brand_profile_id=brand.id,
            day=date(2026, 4, 16),
            generate_astro_if_missing=False,
        )

        assert "aspect_behavior_cards_context" in captured
        abc = captured["aspect_behavior_cards_context"]
        assert abc["has_behavior_cards"] is True
        assert "mars_saturn" in abc["matched_pair_keys"]


# ---------------------------------------------------------------------------
# Venus–Pluto card tests
# ---------------------------------------------------------------------------

class TestVenusPlutoCard:
    def test_venus_pluto_in_registry(self) -> None:
        from astro_content_agent.services.content.aspect_behavior_cards import (
            VENUS_PLUTO_CARD,
        )
        assert "pluto_venus" in ASPECT_BEHAVIOR_CARD_REGISTRY
        assert ASPECT_BEHAVIOR_CARD_REGISTRY["pluto_venus"].pair_key == "pluto_venus"
        assert "Венера" in VENUS_PLUTO_CARD.core_tension

    def test_venus_pluto_language_bank_not_empty(self) -> None:
        assert len(ASPECT_BEHAVIOR_CARD_REGISTRY["pluto_venus"].language_bank) >= 5

    def test_venus_pluto_reel_template_has_required_fields(self) -> None:
        rt = ASPECT_BEHAVIOR_CARD_REGISTRY["pluto_venus"].reel_template
        for field in ("hook_0_3s", "spoken_hook", "recognition_beat", "compensation_beat", "cta"):
            assert field in rt, f"Missing reel_template field: {field}"

    def test_venus_pluto_pair_key_both_planet_orders(self) -> None:
        # pair_key_from_signal_key always returns alphabetical → pluto_venus
        assert pair_key_from_signal_key("venus-square-pluto") == "pluto_venus"
        assert pair_key_from_signal_key("pluto-square-venus") == "pluto_venus"

    def test_venus_pluto_pair_key_all_aspect_types(self) -> None:
        for asp in ("conjunction", "sextile", "square", "trine", "opposition"):
            assert pair_key_from_signal_key(f"venus-{asp}-pluto") == "pluto_venus"
            assert pair_key_from_signal_key(f"pluto-{asp}-venus") == "pluto_venus"

    def test_context_matches_venus_pluto_signal(self) -> None:
        day = _day(_signal("venus-square-pluto", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert "pluto_venus" in d["matched_pair_keys"]
        m = d["matches"][0]
        assert m["pair_key"] == "pluto_venus"
        assert m["card"]["title"] == "Venus–Pluto Aspect Behavior Card v1"

    def test_context_matches_reverse_order_pluto_venus(self) -> None:
        day = _day(_signal("pluto-trine-venus", polarity="harmonious"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        assert "pluto_venus" in ctx.to_dict()["matched_pair_keys"]

    def test_coexistence_mars_saturn_and_venus_pluto(self) -> None:
        day = _day(
            _signal("mars-square-saturn", polarity="tense"),
            _signal("venus-conjunction-pluto", polarity="neutral"),
        )
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert len(d["matches"]) == 2
        pair_keys = d["matched_pair_keys"]
        assert "mars_saturn" in pair_keys
        assert "pluto_venus" in pair_keys

    def test_venus_pluto_card_to_dict_has_all_fields(self) -> None:
        card_dict = ASPECT_BEHAVIOR_CARD_REGISTRY["pluto_venus"].to_dict()
        for field in (
            "pair_key", "title", "core_tension", "lived_pattern",
            "distortions", "emotional_signature", "money_work_expression",
            "secondary_benefit", "compensation", "supergift",
            "language_bank", "planet_cats_translation",
            "post_template", "reel_template",
            "failure_modes_planet1_dominates", "failure_modes_planet2_dominates",
        ):
            assert field in card_dict, f"Missing card field: {field}"


# ---------------------------------------------------------------------------
# Moon–Saturn card tests
# ---------------------------------------------------------------------------

class TestMoonSaturnCard:
    def test_moon_saturn_in_registry(self) -> None:
        from astro_content_agent.services.content.aspect_behavior_cards import MOON_SATURN_CARD
        assert "moon_saturn" in ASPECT_BEHAVIOR_CARD_REGISTRY
        assert ASPECT_BEHAVIOR_CARD_REGISTRY["moon_saturn"].pair_key == "moon_saturn"
        assert "Луна" in MOON_SATURN_CARD.core_tension

    def test_moon_saturn_pair_key_both_orders(self) -> None:
        # sorted(["moon","saturn"]) = ["moon","saturn"] → moon_saturn
        assert pair_key_from_signal_key("moon-square-saturn") == "moon_saturn"
        assert pair_key_from_signal_key("saturn-square-moon") == "moon_saturn"

    def test_moon_saturn_pair_key_all_aspect_types(self) -> None:
        for asp in ("conjunction", "sextile", "square", "trine", "opposition"):
            assert pair_key_from_signal_key(f"moon-{asp}-saturn") == "moon_saturn"
            assert pair_key_from_signal_key(f"saturn-{asp}-moon") == "moon_saturn"

    def test_context_matches_moon_saturn_signal(self) -> None:
        day = _day(_signal("moon-square-saturn", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert "moon_saturn" in d["matched_pair_keys"]
        m = d["matches"][0]
        assert m["pair_key"] == "moon_saturn"
        assert m["card"]["title"] == "Moon–Saturn Aspect Behavior Card v1"

    def test_context_matches_reverse_order(self) -> None:
        day = _day(_signal("saturn-opposition-moon", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        assert "moon_saturn" in ctx.to_dict()["matched_pair_keys"]

    def test_coexistence_all_three_cards(self) -> None:
        day = _day(
            _signal("moon-square-saturn", polarity="tense"),
            _signal("mars-opposition-saturn", polarity="tense"),
            _signal("venus-conjunction-pluto", polarity="neutral"),
        )
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert len(d["matches"]) == 3
        assert set(d["matched_pair_keys"]) == {"moon_saturn", "mars_saturn", "pluto_venus"}

    def test_moon_saturn_language_bank(self) -> None:
        assert len(ASPECT_BEHAVIOR_CARD_REGISTRY["moon_saturn"].language_bank) >= 5

    def test_moon_saturn_reel_template_fields(self) -> None:
        rt = ASPECT_BEHAVIOR_CARD_REGISTRY["moon_saturn"].reel_template
        for field in ("hook_0_3s", "spoken_hook", "recognition_beat", "compensation_beat", "cta"):
            assert field in rt

    def test_moon_saturn_to_dict_has_all_fields(self) -> None:
        card_dict = ASPECT_BEHAVIOR_CARD_REGISTRY["moon_saturn"].to_dict()
        for field in (
            "pair_key", "title", "core_tension", "lived_pattern",
            "distortions", "emotional_signature", "money_work_expression",
            "secondary_benefit", "compensation", "supergift",
            "language_bank", "planet_cats_translation",
            "post_template", "reel_template",
            "failure_modes_planet1_dominates", "failure_modes_planet2_dominates",
        ):
            assert field in card_dict, f"Missing: {field}"


# ---------------------------------------------------------------------------
# Sun–Saturn card tests
# ---------------------------------------------------------------------------

class TestSunSaturnCard:
    def test_sun_saturn_in_registry(self) -> None:
        from astro_content_agent.services.content.aspect_behavior_cards import SUN_SATURN_CARD
        assert "saturn_sun" in ASPECT_BEHAVIOR_CARD_REGISTRY
        assert ASPECT_BEHAVIOR_CARD_REGISTRY["saturn_sun"].pair_key == "saturn_sun"
        assert "Солнце" in SUN_SATURN_CARD.core_tension

    def test_sun_saturn_pair_key_both_orders(self) -> None:
        # sorted(["sun","saturn"]) = ["saturn","sun"] → saturn_sun
        assert pair_key_from_signal_key("sun-square-saturn") == "saturn_sun"
        assert pair_key_from_signal_key("saturn-square-sun") == "saturn_sun"

    def test_sun_saturn_pair_key_all_aspect_types(self) -> None:
        for asp in ("conjunction", "sextile", "square", "trine", "opposition"):
            assert pair_key_from_signal_key(f"sun-{asp}-saturn") == "saturn_sun"
            assert pair_key_from_signal_key(f"saturn-{asp}-sun") == "saturn_sun"

    def test_context_matches_sun_saturn_signal(self) -> None:
        day = _day(_signal("sun-square-saturn", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert "saturn_sun" in d["matched_pair_keys"]
        m = d["matches"][0]
        assert m["pair_key"] == "saturn_sun"
        assert m["card"]["title"] == "Sun–Saturn Aspect Behavior Card v1"

    def test_context_matches_reverse_order(self) -> None:
        day = _day(_signal("saturn-opposition-sun", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        assert "saturn_sun" in ctx.to_dict()["matched_pair_keys"]

    def test_coexistence_all_five_cards(self) -> None:
        day = _day(
            _signal("sun-square-saturn", polarity="tense"),
            _signal("venus-square-mars", polarity="tense"),
            _signal("moon-square-saturn", polarity="tense"),
            _signal("mars-opposition-saturn", polarity="tense"),
            _signal("venus-conjunction-pluto", polarity="neutral"),
        )
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert len(d["matches"]) == 5
        assert set(d["matched_pair_keys"]) == {
            "saturn_sun", "mars_venus", "moon_saturn", "mars_saturn", "pluto_venus"
        }

    def test_sun_saturn_language_bank(self) -> None:
        assert len(ASPECT_BEHAVIOR_CARD_REGISTRY["saturn_sun"].language_bank) >= 5

    def test_sun_saturn_reel_template_fields(self) -> None:
        rt = ASPECT_BEHAVIOR_CARD_REGISTRY["saturn_sun"].reel_template
        for field in ("hook_0_3s", "spoken_hook", "recognition_beat", "compensation_beat", "cta"):
            assert field in rt

    def test_sun_saturn_compensation_is_rich(self) -> None:
        card = ASPECT_BEHAVIOR_CARD_REGISTRY["saturn_sun"]
        assert len(card.compensation) >= 5
        comp_text = " ".join(card.compensation)
        assert "режим" in comp_text or "структур" in comp_text

    def test_sun_saturn_reel_compensation_beat_is_actionable(self) -> None:
        beat = ASPECT_BEHAVIOR_CARD_REGISTRY["saturn_sun"].reel_template["compensation_beat"]
        assert "режим" in beat or "структур" in beat or "обещани" in beat

    def test_sun_saturn_to_dict_has_all_fields(self) -> None:
        card_dict = ASPECT_BEHAVIOR_CARD_REGISTRY["saturn_sun"].to_dict()
        for f in (
            "pair_key", "title", "core_tension", "lived_pattern",
            "distortions", "emotional_signature", "money_work_expression",
            "secondary_benefit", "compensation", "supergift",
            "language_bank", "planet_cats_translation",
            "post_template", "reel_template",
            "failure_modes_planet1_dominates", "failure_modes_planet2_dominates",
        ):
            assert f in card_dict, f"Missing: {f}"
# ---------------------------------------------------------------------------
# Venus–Mars card tests
# ---------------------------------------------------------------------------

class TestVenusMarsCard:
    def test_venus_mars_in_registry(self) -> None:
        from astro_content_agent.services.content.aspect_behavior_cards import VENUS_MARS_CARD
        assert "mars_venus" in ASPECT_BEHAVIOR_CARD_REGISTRY
        assert ASPECT_BEHAVIOR_CARD_REGISTRY["mars_venus"].pair_key == "mars_venus"
        assert "Венера" in VENUS_MARS_CARD.core_tension

    def test_venus_mars_pair_key_both_orders(self) -> None:
        # sorted(["venus","mars"]) = ["mars","venus"] → mars_venus
        assert pair_key_from_signal_key("venus-square-mars") == "mars_venus"
        assert pair_key_from_signal_key("mars-square-venus") == "mars_venus"

    def test_venus_mars_pair_key_all_aspect_types(self) -> None:
        for asp in ("conjunction", "sextile", "square", "trine", "opposition"):
            assert pair_key_from_signal_key(f"venus-{asp}-mars") == "mars_venus"
            assert pair_key_from_signal_key(f"mars-{asp}-venus") == "mars_venus"

    def test_context_matches_venus_mars_signal(self) -> None:
        day = _day(_signal("venus-square-mars", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert "mars_venus" in d["matched_pair_keys"]
        m = d["matches"][0]
        assert m["pair_key"] == "mars_venus"
        assert m["card"]["title"] == "Venus–Mars Aspect Behavior Card v1"

    def test_context_matches_reverse_order(self) -> None:
        day = _day(_signal("mars-opposition-venus", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        assert "mars_venus" in ctx.to_dict()["matched_pair_keys"]

    def test_coexistence_all_four_cards(self) -> None:
        day = _day(
            _signal("venus-square-mars", polarity="tense"),
            _signal("moon-square-saturn", polarity="tense"),
            _signal("mars-opposition-saturn", polarity="tense"),
            _signal("venus-conjunction-pluto", polarity="neutral"),
        )
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert len(d["matches"]) == 4
        assert set(d["matched_pair_keys"]) == {"mars_venus", "moon_saturn", "mars_saturn", "pluto_venus"}

    def test_venus_mars_language_bank(self) -> None:
        assert len(ASPECT_BEHAVIOR_CARD_REGISTRY["mars_venus"].language_bank) >= 5

    def test_venus_mars_reel_template_fields(self) -> None:
        rt = ASPECT_BEHAVIOR_CARD_REGISTRY["mars_venus"].reel_template
        for field in ("hook_0_3s", "spoken_hook", "recognition_beat", "compensation_beat", "cta"):
            assert field in rt

    def test_venus_mars_to_dict_has_all_fields(self) -> None:
        card_dict = ASPECT_BEHAVIOR_CARD_REGISTRY["mars_venus"].to_dict()
        for field in (
            "pair_key", "title", "core_tension", "lived_pattern",
            "distortions", "emotional_signature", "money_work_expression",
            "secondary_benefit", "compensation", "supergift",
            "language_bank", "planet_cats_translation",
            "post_template", "reel_template",
            "failure_modes_planet1_dominates", "failure_modes_planet2_dominates",
        ):
            assert field in card_dict, f"Missing: {field}"


# ---------------------------------------------------------------------------
# Jupiter–Saturn card tests
# ---------------------------------------------------------------------------

class TestJupiterSaturnCard:
    def test_jupiter_saturn_in_registry(self) -> None:
        from astro_content_agent.services.content.aspect_behavior_cards import JUPITER_SATURN_CARD
        assert "jupiter_saturn" in ASPECT_BEHAVIOR_CARD_REGISTRY
        assert ASPECT_BEHAVIOR_CARD_REGISTRY["jupiter_saturn"].pair_key == "jupiter_saturn"
        assert "Юпитер" in JUPITER_SATURN_CARD.core_tension

    def test_jupiter_saturn_pair_key_both_orders(self) -> None:
        # sorted(["jupiter", "saturn"]) = ["jupiter", "saturn"] → jupiter_saturn
        assert pair_key_from_signal_key("jupiter-square-saturn") == "jupiter_saturn"
        assert pair_key_from_signal_key("saturn-square-jupiter") == "jupiter_saturn"

    def test_jupiter_saturn_pair_key_all_aspect_types(self) -> None:
        for asp in ("conjunction", "sextile", "square", "trine", "opposition"):
            assert pair_key_from_signal_key(f"jupiter-{asp}-saturn") == "jupiter_saturn"
            assert pair_key_from_signal_key(f"saturn-{asp}-jupiter") == "jupiter_saturn"

    def test_context_matches_jupiter_saturn_signal(self) -> None:
        day = _day(_signal("jupiter-square-saturn", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert "jupiter_saturn" in d["matched_pair_keys"]
        m = d["matches"][0]
        assert m["pair_key"] == "jupiter_saturn"
        assert m["card"]["title"] == "Jupiter–Saturn Aspect Behavior Card v1"

    def test_context_matches_reverse_order(self) -> None:
        day = _day(_signal("saturn-opposition-jupiter", polarity="tense"))
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        assert "jupiter_saturn" in ctx.to_dict()["matched_pair_keys"]

    def test_coexistence_all_six_cards(self) -> None:
        day = _day(
            _signal("jupiter-square-saturn", polarity="tense"),
            _signal("sun-square-saturn", polarity="tense"),
            _signal("venus-square-mars", polarity="tense"),
            _signal("moon-square-saturn", polarity="tense"),
            _signal("mars-opposition-saturn", polarity="tense"),
            _signal("venus-conjunction-pluto", polarity="neutral"),
        )
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        d = ctx.to_dict()
        assert d["has_behavior_cards"] is True
        assert len(d["matches"]) == 6
        assert set(d["matched_pair_keys"]) == {
            "jupiter_saturn", "saturn_sun", "mars_venus",
            "moon_saturn", "mars_saturn", "pluto_venus",
        }

    def test_jupiter_saturn_language_bank(self) -> None:
        assert len(ASPECT_BEHAVIOR_CARD_REGISTRY["jupiter_saturn"].language_bank) >= 5

    def test_jupiter_saturn_reel_template_fields(self) -> None:
        rt = ASPECT_BEHAVIOR_CARD_REGISTRY["jupiter_saturn"].reel_template
        for field in ("hook_0_3s", "spoken_hook", "recognition_beat", "compensation_beat", "cta"):
            assert field in rt

    def test_jupiter_saturn_compensation_is_rich(self) -> None:
        card = ASPECT_BEHAVIOR_CARD_REGISTRY["jupiter_saturn"]
        assert len(card.compensation) >= 5
        comp_text = " ".join(card.compensation)
        assert "рост" in comp_text or "риск" in comp_text or "горизонт" in comp_text

    def test_jupiter_saturn_body_symbolic_compensations_present(self) -> None:
        card = ASPECT_BEHAVIOR_CARD_REGISTRY["jupiter_saturn"]
        assert len(card.body_symbolic_compensations) >= 5
        bsc_text = " ".join(card.body_symbolic_compensations)
        assert "карт" in bsc_text or "дашборд" in bsc_text or "архитектур" in bsc_text

    def test_jupiter_saturn_reel_compensation_beat_is_actionable(self) -> None:
        beat = ASPECT_BEHAVIOR_CARD_REGISTRY["jupiter_saturn"].reel_template["compensation_beat"]
        assert "рост" in beat or "горизонт" in beat or "метрик" in beat

    def test_jupiter_saturn_to_dict_has_all_fields(self) -> None:
        card_dict = ASPECT_BEHAVIOR_CARD_REGISTRY["jupiter_saturn"].to_dict()
        for f in (
            "pair_key", "title", "core_tension", "lived_pattern",
            "distortions", "emotional_signature", "money_work_expression",
            "secondary_benefit", "compensation", "body_symbolic_compensations",
            "supergift", "language_bank", "planet_cats_translation",
            "post_template", "reel_template",
            "failure_modes_planet1_dominates", "failure_modes_planet2_dominates",
        ):
            assert f in card_dict, f"Missing: {f}"

    def test_jupiter_saturn_deduplicates_same_pair(self) -> None:
        day = _day(
            _signal("jupiter-square-saturn"),
            _signal("saturn-trine-jupiter"),
        )
        ctx = AspectBehaviorCardsContext.from_astro_day(day)
        assert len(ctx.matches) == 1
        assert ctx.matches[0]["pair_key"] == "jupiter_saturn"
