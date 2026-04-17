"""Tests for the Venus Sign Climate layer.

Covers:
- registry content and structure for all 12 signs
- VenusSignClimateContext.from_sign (unit, no ephemeris)
- VenusSignClimateContext.from_astro_day (integration, uses real ephemeris for known dates)
- to_dict contract
- no-match / unknown sign handling
- payload injection: planner, caption_service, reel_script_service each include the key
- funnel separation: no natal-house language, organic CTA only
"""
from __future__ import annotations

import types
import uuid
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.content.venus_sign_climate import (
    VENUS_ARIES_CLIMATE,
    VENUS_CANCER_CLIMATE,
    VENUS_CAPRICORN_CLIMATE,
    VENUS_AQUARIUS_CLIMATE,
    VENUS_GEMINI_CLIMATE,
    VENUS_LEO_CLIMATE,
    VENUS_LIBRA_CLIMATE,
    VENUS_PISCES_CLIMATE,
    VENUS_SAGITTARIUS_CLIMATE,
    VENUS_SCORPIO_CLIMATE,
    VENUS_SIGN_CLIMATE_REGISTRY,
    VENUS_TAURUS_CLIMATE,
    VENUS_VIRGO_CLIMATE,
    VenusSignClimate,
    VenusSignClimateContext,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _day(sign_day: date | None = None) -> AstroDayPayload:
    return AstroDayPayload(
        day=sign_day or date(2026, 4, 16),
        engine_version="v1.real",
        generated_at=datetime(2026, 4, 16, 12, 0, 0),
        signals=[],
    )


def _signal(key: str, *, polarity: str | None = "tense") -> TransitSignal:
    return TransitSignal(
        key=key,
        headline=key.replace("-", " "),
        summary="test",
        intensity=0.8,
        aspect_polarity=polarity,
        orb=1.0,
        signal_class="foreground",
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_taurus_registered(self) -> None:
        assert "Taurus" in VENUS_SIGN_CLIMATE_REGISTRY
        assert VENUS_SIGN_CLIMATE_REGISTRY["Taurus"] is VENUS_TAURUS_CLIMATE

    def test_gemini_registered(self) -> None:
        assert "Gemini" in VENUS_SIGN_CLIMATE_REGISTRY
        assert VENUS_SIGN_CLIMATE_REGISTRY["Gemini"] is VENUS_GEMINI_CLIMATE

    def test_registry_has_all_twelve_signs(self) -> None:
        assert len(VENUS_SIGN_CLIMATE_REGISTRY) == 12
        expected = {
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        }
        assert set(VENUS_SIGN_CLIMATE_REGISTRY.keys()) == expected

    def test_signs_are_correct_instances(self) -> None:
        for sign, climate in VENUS_SIGN_CLIMATE_REGISTRY.items():
            assert isinstance(climate, VenusSignClimate)
            assert climate.sign == sign


# ---------------------------------------------------------------------------
# VenusSignClimate dataclass content
# ---------------------------------------------------------------------------

class TestTaurusClimate:
    def test_title_is_set(self) -> None:
        assert "Тельц" in VENUS_TAURUS_CLIMATE.climate_title

    def test_money_style_mentions_accumulation(self) -> None:
        text = VENUS_TAURUS_CLIMATE.money_style.lower()
        assert "накопл" in text or "стабил" in text

    def test_likely_leak_has_items(self) -> None:
        assert len(VENUS_TAURUS_CLIMATE.likely_leak) >= 3

    def test_likely_strength_has_items(self) -> None:
        assert len(VENUS_TAURUS_CLIMATE.likely_strength) >= 3

    def test_instagram_hook_angles_has_items(self) -> None:
        assert len(VENUS_TAURUS_CLIMATE.instagram_hook_angles) >= 3

    def test_instagram_cta_hint_has_items(self) -> None:
        assert len(VENUS_TAURUS_CLIMATE.instagram_cta_hint) >= 3

    def test_instagram_cta_hint_no_app_mention(self) -> None:
        combined = " ".join(VENUS_TAURUS_CLIMATE.instagram_cta_hint).lower()
        assert "money compass" not in combined
        assert "2-й дом" not in combined
        assert "10-й дом" not in combined

    def test_instagram_cta_hint_has_organic_patterns(self) -> None:
        combined = " ".join(VENUS_TAURUS_CLIMATE.instagram_cta_hint).lower()
        assert "сохрани" in combined or "директ" in combined or "подпис" in combined

    def test_to_dict_contains_all_fields(self) -> None:
        d = VENUS_TAURUS_CLIMATE.to_dict()
        for f in (
            "sign", "climate_title", "money_style", "comfort_style",
            "unconscious_pull", "likely_leak", "likely_strength",
            "instagram_hook_angles", "instagram_cta_hint", "money_poles",
        ):
            assert f in d, f"Missing field: {f}"


class TestGeminiClimate:
    def test_title_is_set(self) -> None:
        assert "Близнец" in VENUS_GEMINI_CLIMATE.climate_title

    def test_money_style_mentions_movement(self) -> None:
        text = VENUS_GEMINI_CLIMATE.money_style.lower()
        assert "движ" in text or "обмен" in text or "гибк" in text

    def test_likely_leak_has_items(self) -> None:
        assert len(VENUS_GEMINI_CLIMATE.likely_leak) >= 3

    def test_likely_strength_has_items(self) -> None:
        assert len(VENUS_GEMINI_CLIMATE.likely_strength) >= 3

    def test_instagram_hook_angles_has_items(self) -> None:
        assert len(VENUS_GEMINI_CLIMATE.instagram_hook_angles) >= 3

    def test_instagram_cta_hint_has_items(self) -> None:
        assert len(VENUS_GEMINI_CLIMATE.instagram_cta_hint) >= 3

    def test_instagram_cta_hint_no_app_mention(self) -> None:
        combined = " ".join(VENUS_GEMINI_CLIMATE.instagram_cta_hint).lower()
        assert "money compass" not in combined
        assert "2-й дом" not in combined
        assert "10-й дом" not in combined

    def test_instagram_cta_hint_has_organic_patterns(self) -> None:
        combined = " ".join(VENUS_GEMINI_CLIMATE.instagram_cta_hint).lower()
        assert "сохрани" in combined or "директ" in combined or "подпис" in combined

    def test_to_dict_contains_all_fields(self) -> None:
        d = VENUS_GEMINI_CLIMATE.to_dict()
        for f in (
            "sign", "climate_title", "money_style", "comfort_style",
            "unconscious_pull", "likely_leak", "likely_strength",
            "instagram_hook_angles", "instagram_cta_hint", "money_poles",
        ):
            assert f in d, f"Missing field: {f}"


# ---------------------------------------------------------------------------
# VenusSignClimateContext — from_sign
# ---------------------------------------------------------------------------

class TestContextFromSign:
    def test_taurus_match(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Taurus")
        assert ctx.has_climate is True
        assert ctx.sign == "Taurus"
        assert ctx.climate is VENUS_TAURUS_CLIMATE
        assert ctx.retrograde is False

    def test_gemini_match(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Gemini")
        assert ctx.has_climate is True
        assert ctx.sign == "Gemini"
        assert ctx.climate is VENUS_GEMINI_CLIMATE

    def test_aries_match(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Aries")
        assert ctx.has_climate is True
        assert ctx.sign == "Aries"
        assert ctx.climate is VENUS_ARIES_CLIMATE

    def test_scorpio_match(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Scorpio")
        assert ctx.has_climate is True
        assert ctx.sign == "Scorpio"
        assert ctx.climate is VENUS_SCORPIO_CLIMATE

    def test_capricorn_match(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Capricorn")
        assert ctx.has_climate is True
        assert ctx.sign == "Capricorn"
        assert ctx.climate is VENUS_CAPRICORN_CLIMATE

    def test_pisces_match(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Pisces")
        assert ctx.has_climate is True
        assert ctx.sign == "Pisces"
        assert ctx.climate is VENUS_PISCES_CLIMATE

    def test_retrograde_flag_preserved(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Taurus", retrograde=True)
        assert ctx.retrograde is True

    def test_unknown_sign_no_match(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Ophiuchus")
        assert ctx.has_climate is False
        assert ctx.sign == "Ophiuchus"
        assert ctx.climate is None

    def test_no_match_sentinel(self) -> None:
        ctx = VenusSignClimateContext.no_match()
        assert ctx.has_climate is False
        assert ctx.sign is None
        assert ctx.climate is None


# ---------------------------------------------------------------------------
# VenusSignClimateContext — to_dict
# ---------------------------------------------------------------------------

class TestContextToDict:
    def test_match_dict_shape(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Taurus")
        d = ctx.to_dict()
        assert d["has_climate"] is True
        assert d["sign"] == "Taurus"
        assert d["retrograde"] is False
        assert isinstance(d["climate"], dict)
        assert d["climate"]["sign"] == "Taurus"

    def test_no_match_dict_shape(self) -> None:
        ctx = VenusSignClimateContext.no_match()
        d = ctx.to_dict()
        assert d["has_climate"] is False
        assert d["sign"] is None
        assert d["climate"] is None

    def test_unknown_sign_dict_shape(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Ophiuchus")
        d = ctx.to_dict()
        assert d["has_climate"] is False
        assert d["sign"] == "Ophiuchus"
        assert d["climate"] is None

    def test_climate_dict_has_hook_angles(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Gemini")
        d = ctx.to_dict()
        assert len(d["climate"]["instagram_hook_angles"]) >= 3

    def test_climate_dict_cta_hint_is_organic(self) -> None:
        ctx = VenusSignClimateContext.from_sign("Taurus")
        d = ctx.to_dict()
        combined = " ".join(d["climate"]["instagram_cta_hint"]).lower()
        assert "сохрани" in combined or "директ" in combined or "подпис" in combined
        assert "money compass" not in combined


# ---------------------------------------------------------------------------
# VenusSignClimateContext — from_astro_day (real ephemeris)
# ---------------------------------------------------------------------------

class TestContextFromAstroDay:
    # Venus entered Taurus ≈ 2026-03-27 and stays until ≈ 2026-04-20.
    # Pick a date firmly in Taurus.
    TAURUS_DATE = date(2026, 4, 10)

    # Venus entered Gemini ≈ 2026-04-20.  Use a date safely in Gemini.
    GEMINI_DATE = date(2026, 5, 15)

    def test_taurus_date_resolves_to_taurus(self) -> None:
        astro_day = _day(self.TAURUS_DATE)
        ctx = VenusSignClimateContext.from_astro_day(astro_day)
        assert ctx.has_climate is True
        assert ctx.sign == "Taurus"

    def test_gemini_date_resolves_to_gemini(self) -> None:
        astro_day = _day(self.GEMINI_DATE)
        ctx = VenusSignClimateContext.from_astro_day(astro_day)
        assert ctx.has_climate is True
        assert ctx.sign == "Gemini"

    def test_result_is_consistent_for_same_date(self) -> None:
        astro_day = _day(self.TAURUS_DATE)
        ctx1 = VenusSignClimateContext.from_astro_day(astro_day)
        ctx2 = VenusSignClimateContext.from_astro_day(astro_day)
        assert ctx1.sign == ctx2.sign
        assert ctx1.has_climate == ctx2.has_climate

    def test_to_dict_serialises_after_from_astro_day(self) -> None:
        astro_day = _day(self.TAURUS_DATE)
        ctx = VenusSignClimateContext.from_astro_day(astro_day)
        d = ctx.to_dict()
        assert "has_climate" in d
        assert "sign" in d


# ---------------------------------------------------------------------------
# Payload injection: planner, caption, reel each pass the key
# ---------------------------------------------------------------------------

def _brand(
    *,
    content_language: str = "ru",
    tone_preset: str = "sharp_witty",
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        id=str(uuid.uuid4()),
        name="Test",
        description="d",
        tone_preset=tone_preset,
        banned_terms=[],
        default_hashtags=[],
        face_led_preferred=0,
        content_language=content_language,
    )


def _astro_signal_record(day: date) -> MagicMock:
    astro_day = AstroDayPayload(
        day=day,
        engine_version="v1.real",
        generated_at=datetime(day.year, day.month, day.day, 12, 0, 0),
        signals=[],
    )
    rec = MagicMock()
    rec.id = str(uuid.uuid4())
    rec.payload = astro_day.model_dump(mode="json")
    return rec


class TestPlannerInjectsClimateContext:
    def test_planner_payload_contains_venus_sign_climate_context(self) -> None:
        from astro_content_agent.services.strategy.planner import StrategyPlannerService

        captured: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured.update(input_payload)
            from astro_content_agent.schemas.strategy import DayPlanItem, DayPlanPayload

            return DayPlanPayload(
                day=date(2026, 4, 10),
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

        brand = _brand()
        mock_deps = MagicMock()
        mock_deps.brand_repo.get.return_value = brand
        mock_deps.pillar_repo.list_for_brand.return_value = []
        mock_deps.pillar_balancer.get_recent_pillar_usage.return_value = {}
        mock_deps.pillar_balancer.to_prompt_hint.return_value = ""
        mock_deps.plan_repo.upsert.return_value = MagicMock(
            id=str(uuid.uuid4()),
            payload={"day": "2026-04-10", "items": [], "notes": []},
        )
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = _astro_signal_record(
            date(2026, 4, 10)
        )

        svc = StrategyPlannerService(runner=mock_runner, deps=mock_deps)
        svc.generate_day_plan(
            db=MagicMock(),
            brand_profile_id=brand.id,
            day=date(2026, 4, 10),
            generate_astro_if_missing=False,
        )

        assert "venus_sign_climate_context" in captured
        vsc = captured["venus_sign_climate_context"]
        assert "has_climate" in vsc
        assert "sign" in vsc


class TestCaptionServiceInjectsClimateContext:
    def test_caption_payload_contains_venus_sign_climate_context(self) -> None:
        from astro_content_agent.services.content.caption_service import CaptionService
        from astro_content_agent.schemas.drafts import PostDraftPayload

        captured: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured.update(input_payload)
            return PostDraftPayload(
                title="t",
                hook="h",
                caption="c",
                cta="cta",
                hashtags=[],
                voice_note="v",
                metadata={},
            )

        mock_runner = MagicMock()
        mock_runner.run_json.side_effect = fake_run_json

        brand = _brand()
        mock_deps = MagicMock()
        mock_deps.brand_repo.get.return_value = brand
        mock_deps.draft_repo.create.return_value = MagicMock(
            id=str(uuid.uuid4()),
            payload={"title": "t", "hook": "h", "caption": "c", "cta": "cta",
                     "hashtags": [], "voice_note": "v", "metadata": {}},
        )
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = _astro_signal_record(
            date(2026, 4, 10)
        )
        mock_deps.plan_repo.get_by_brand_and_day.return_value = None
        mock_deps.pillar_balancer.get_recent_pillar_usage.return_value = {}
        mock_deps.pillar_balancer.to_prompt_hint.return_value = ""

        svc = CaptionService(runner=mock_runner, deps=mock_deps)
        svc.generate_post_draft(
            db=MagicMock(),
            brand_profile_id=brand.id,
            day=date(2026, 4, 10),
            content_plan=None,
            plan_slot=None,
        )

        assert "venus_sign_climate_context" in captured
        vsc = captured["venus_sign_climate_context"]
        assert "has_climate" in vsc


class TestReelServiceInjectsClimateContext:
    def test_reel_payload_contains_venus_sign_climate_context(self) -> None:
        from astro_content_agent.services.content.reel_script_service import ReelScriptService
        from astro_content_agent.schemas.drafts import ReelDraftPayload

        captured: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured.update(input_payload)
            return ReelDraftPayload(
                hook_0_3s="h",
                hook="H",
                reel_type="talking_head",
                script="s",
                cta="c",
                metadata={},
            )

        mock_runner = MagicMock()
        mock_runner.run_json.side_effect = fake_run_json

        brand = _brand()
        mock_deps = MagicMock()
        mock_deps.brand_repo.get.return_value = brand
        mock_deps.draft_repo.create.return_value = MagicMock(
            id=str(uuid.uuid4()),
            payload={"hook_0_3s": "h", "hook": "H", "script": "s", "cta": "c",
                     "hashtags": [], "voice_note": "v", "metadata": {}},
        )
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = _astro_signal_record(
            date(2026, 4, 10)
        )
        mock_deps.plan_repo.get_by_brand_and_day.return_value = None
        mock_deps.pillar_balancer.get_recent_pillar_usage.return_value = {}
        mock_deps.pillar_balancer.to_prompt_hint.return_value = ""

        svc = ReelScriptService(runner=mock_runner, deps=mock_deps)
        svc.generate_reel_draft(
            db=MagicMock(),
            brand_profile_id=brand.id,
            day=date(2026, 4, 10),
            content_plan=None,
            plan_slot=None,
        )

        assert "venus_sign_climate_context" in captured
        vsc = captured["venus_sign_climate_context"]
        assert "has_climate" in vsc


# ---------------------------------------------------------------------------
# All 12 signs structural checks (parametrized across the full registry)
# ---------------------------------------------------------------------------

ALL_SIGNS = [
    ("Aries", VENUS_ARIES_CLIMATE, "импульс", "имп"),
    ("Taurus", VENUS_TAURUS_CLIMATE, "накопл", "стабил"),
    ("Gemini", VENUS_GEMINI_CLIMATE, "движ", "обмен"),
    ("Cancer", VENUS_CANCER_CLIMATE, "безопасн", "тревог"),
    ("Leo", VENUS_LEO_CLIMATE, "статус", "роскош"),
    ("Virgo", VENUS_VIRGO_CLIMATE, "контрол", "экономн"),
    ("Libra", VENUS_LIBRA_CLIMATE, "гармон", "красот"),
    ("Scorpio", VENUS_SCORPIO_CLIMATE, "контрол", "обладан"),
    ("Sagittarius", VENUS_SAGITTARIUS_CLIMATE, "свобод", "масштаб"),
    ("Capricorn", VENUS_CAPRICORN_CLIMATE, "труд", "страх"),
    ("Aquarius", VENUS_AQUARIUS_CLIMATE, "идей", "независим"),
    ("Pisces", VENUS_PISCES_CLIMATE, "ощущен", "чуйк"),
]


class TestAllTwelveSignsStructure:
    """Structural invariants that must hold for every sign in the registry."""

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_sign_field_matches_key(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        assert climate.sign == sign

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_climate_title_is_nonempty(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        assert len(climate.climate_title) > 10

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_money_style_is_nonempty(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        assert len(climate.money_style) > 20

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_money_style_contains_keyword(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        text = (climate.money_style + " " + climate.unconscious_pull).lower()
        assert kw1 in text or kw2 in text, (
            f"{sign}: expected '{kw1}' or '{kw2}' in money_style+unconscious_pull"
        )

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_likely_leak_has_at_least_three(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        assert len(climate.likely_leak) >= 3, f"{sign}: likely_leak too short"

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_likely_strength_has_at_least_three(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        assert len(climate.likely_strength) >= 3, f"{sign}: likely_strength too short"

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_hook_angles_has_at_least_four(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        assert len(climate.instagram_hook_angles) >= 4, f"{sign}: instagram_hook_angles too short"

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_cta_hint_has_at_least_three(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        assert len(climate.instagram_cta_hint) >= 3, f"{sign}: instagram_cta_hint too short"

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_cta_no_app_mention(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        combined = " ".join(climate.instagram_cta_hint).lower()
        assert "money compass" not in combined, f"{sign} CTA must not mention Money Compass"
        assert "2-й дом" not in combined, f"{sign} CTA must not mention 2nd house"
        assert "10-й дом" not in combined, f"{sign} CTA must not mention 10th house"

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_cta_has_organic_action(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        combined = " ".join(climate.instagram_cta_hint).lower()
        has_organic = any(kw in combined for kw in ("сохрани", "директ", "подпис", "комментари", "напиши"))
        assert has_organic, f"{sign}: CTA must contain at least one organic Instagram action"

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_to_dict_has_all_fields(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        d = climate.to_dict()
        for f in (
            "sign", "climate_title", "money_style", "comfort_style",
            "unconscious_pull", "likely_leak", "likely_strength",
            "instagram_hook_angles", "instagram_cta_hint", "money_poles",
        ):
            assert f in d, f"{sign}: missing field '{f}' in to_dict()"

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_from_sign_resolves_to_climate(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        ctx = VenusSignClimateContext.from_sign(sign)
        assert ctx.has_climate is True
        assert ctx.climate is climate


# ---------------------------------------------------------------------------
# Funnel separation: no natal house language in climate objects
# ---------------------------------------------------------------------------

class TestFunnelSeparation:
    """Ensure climate descriptions contain no natal-house or personal-chart language
    that would blur the Instagram / app boundary."""

    _FORBIDDEN_PHRASES = [
        "натальный дом",
        "natal house",
        "ваш асцендент",
        "ваш 2 дом",
        "ваш 10 дом",
        "по вашему гороскопу",
    ]

    def _all_climate_text(self, climate: VenusSignClimate) -> str:
        parts = [
            climate.climate_title,
            climate.money_style,
            climate.comfort_style,
            climate.unconscious_pull,
            " ".join(climate.likely_leak),
            " ".join(climate.likely_strength),
            " ".join(climate.instagram_hook_angles),
            " ".join(climate.money_poles),
            # CTA also checked: must be app-free
            " ".join(climate.instagram_cta_hint),
        ]
        return " ".join(parts).lower()

    @pytest.mark.parametrize("sign,climate,kw1,kw2", ALL_SIGNS)
    def test_no_natal_house_language(self, sign: str, climate: VenusSignClimate, kw1: str, kw2: str) -> None:
        text = self._all_climate_text(climate)
        for phrase in self._FORBIDDEN_PHRASES:
            assert phrase.lower() not in text, f"{sign}: Found forbidden phrase: {phrase}"

    def test_cta_hint_no_app_mention(self) -> None:
        """Instagram CTA must not reference Money Compass or personal chart features."""
        for sign, climate in VENUS_SIGN_CLIMATE_REGISTRY.items():
            combined = " ".join(climate.instagram_cta_hint).lower()
            assert "money compass" not in combined, (
                f"{sign} instagram_cta_hint must NOT reference Money Compass"
            )
            assert "2-й дом" not in combined, f"{sign} CTA must not mention 2nd house"
            assert "10-й дом" not in combined, f"{sign} CTA must not mention 10th house"

    def test_cta_hint_has_organic_instagram_patterns(self) -> None:
        """CTA must contain recognizable organic Instagram actions."""
        for sign, climate in VENUS_SIGN_CLIMATE_REGISTRY.items():
            combined = " ".join(climate.instagram_cta_hint).lower()
            has_organic = any(
                kw in combined for kw in ("сохрани", "директ", "подпис", "комментари", "напиши")
            )
            assert has_organic, f"{sign} CTA hint must contain organic Instagram action"
