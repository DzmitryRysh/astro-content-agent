"""Tests for the Venus Aspect Overlay layer.

Covers:
- _involves_venus helper
- _overlay_mode / _hook_priority / _compensation_priority helpers
- _get_combined_pattern: curated lookup and generic fallback
- _get_hook_suggestion: curated and fallback
- VenusAspectOverlay.no_overlay sentinel
- VenusAspectOverlayContext.from_contexts:
    * no climate → no overlay
    * climate but no Venus aspect → no overlay
    * climate + Venus aspect (tense) → friction overlay
    * climate + Venus aspect (harmonious) → opportunity overlay
    * non-Venus aspect does NOT activate overlay
- to_dict contract
- Service injection: caption, reel, planner all inject venus_aspect_overlay_context
"""
from __future__ import annotations

import types
import uuid
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.content.aspect_behavior_cards import AspectBehaviorCardsContext
from astro_content_agent.services.content.venus_aspect_overlay import (
    VenusAspectOverlay,
    VenusAspectOverlayContext,
    _compensation_priority,
    _get_combined_pattern,
    _get_hook_suggestion,
    _hook_priority,
    _involves_venus,
    _overlay_mode,
)
from astro_content_agent.services.content.venus_sign_climate import VenusSignClimateContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _signal(key: str, *, polarity: str = "tense") -> TransitSignal:
    return TransitSignal(
        key=key,
        headline=key,
        summary="test signal",
        intensity=0.8,
        aspect_polarity=polarity,  # type: ignore[arg-type]
        orb=1.5,
        signal_class="foreground",
    )


def _astro_day(signals: list[TransitSignal]) -> AstroDayPayload:
    return AstroDayPayload(
        day=date(2026, 4, 10),
        engine_version="v1.real",
        generated_at=datetime(2026, 4, 10, 12, 0, 0),
        signals=signals,
    )


def _climate_ctx(sign: str) -> VenusSignClimateContext:
    return VenusSignClimateContext.from_sign(sign)


def _cards_ctx(signals: list[TransitSignal]) -> AspectBehaviorCardsContext:
    return AspectBehaviorCardsContext.from_astro_day(_astro_day(signals))


# ---------------------------------------------------------------------------
# Unit: internal helpers
# ---------------------------------------------------------------------------

class TestInvolvesVenus:
    def test_mars_venus_involves_venus(self) -> None:
        assert _involves_venus("mars_venus") is True

    def test_pluto_venus_involves_venus(self) -> None:
        assert _involves_venus("pluto_venus") is True

    def test_mars_saturn_does_not_involve_venus(self) -> None:
        assert _involves_venus("mars_saturn") is False

    def test_jupiter_saturn_does_not_involve_venus(self) -> None:
        assert _involves_venus("jupiter_saturn") is False

    def test_moon_saturn_does_not_involve_venus(self) -> None:
        assert _involves_venus("moon_saturn") is False


class TestOverlayMode:
    def test_tense_gives_friction(self) -> None:
        assert _overlay_mode("tense") == "friction"

    def test_harmonious_gives_opportunity(self) -> None:
        assert _overlay_mode("harmonious") == "opportunity"

    def test_none_defaults_to_friction(self) -> None:
        assert _overlay_mode(None) == "friction"

    def test_unknown_defaults_to_friction(self) -> None:
        assert _overlay_mode("neutral") == "friction"


class TestHookPriority:
    def test_friction_gives_aspect_first(self) -> None:
        assert _hook_priority("friction") == "aspect_first"

    def test_opportunity_gives_climate_first(self) -> None:
        assert _hook_priority("opportunity") == "climate_first"


class TestCompensationPriority:
    def test_friction_gives_both_layers(self) -> None:
        assert _compensation_priority("friction") == "both_layers"

    def test_opportunity_gives_aspect_card(self) -> None:
        assert _compensation_priority("opportunity") == "aspect_card"


class TestGetCombinedPattern:
    def test_curated_taurus_pluto(self) -> None:
        pattern = _get_combined_pattern("Taurus", "pluto_venus")
        assert len(pattern) >= 3
        combined = " ".join(pattern).lower()
        assert "удержание" in combined or "накопл" in combined

    def test_curated_gemini_mars(self) -> None:
        pattern = _get_combined_pattern("Gemini", "mars_venus")
        assert len(pattern) >= 3
        combined = " ".join(pattern).lower()
        assert "рассеив" in combined or "гибкост" in combined or "вариант" in combined

    def test_curated_libra_pluto(self) -> None:
        pattern = _get_combined_pattern("Libra", "pluto_venus")
        assert len(pattern) >= 3

    def test_curated_capricorn_pluto(self) -> None:
        pattern = _get_combined_pattern("Capricorn", "pluto_venus")
        assert len(pattern) >= 3
        combined = " ".join(pattern).lower()
        assert "страх" in combined or "компульс" in combined or "труд" in combined

    def test_generic_fallback_for_unknown_combination(self) -> None:
        pattern = _get_combined_pattern("Aries", "moon_saturn")  # moon_saturn is not a Venus aspect
        assert len(pattern) >= 2

    def test_all_curated_patterns_have_3_or_more_bullets(self) -> None:
        from astro_content_agent.services.content.venus_aspect_overlay import _CURATED_PATTERNS
        for (sign, key), pattern in _CURATED_PATTERNS.items():
            assert len(pattern) >= 3, f"({sign}, {key}) pattern has fewer than 3 bullets"


class TestGetHookSuggestion:
    def test_curated_taurus_pluto_suggestion(self) -> None:
        hint = _get_hook_suggestion("Taurus", "pluto_venus")
        assert len(hint) > 10
        h = hint.lower()
        assert "накопл" in h or "запас" in h or "копейк" in h or "деньг" in h

    def test_curated_gemini_mars_suggestion(self) -> None:
        hint = _get_hook_suggestion("Gemini", "mars_venus")
        assert len(hint) > 10

    def test_fallback_for_unknown_combination(self) -> None:
        hint = _get_hook_suggestion("Aries", "moon_saturn")
        assert len(hint) > 10  # fallback is always populated


# ---------------------------------------------------------------------------
# VenusAspectOverlay.no_overlay sentinel
# ---------------------------------------------------------------------------

class TestNoOverlaySentinel:
    def test_active_is_false(self) -> None:
        o = VenusAspectOverlay.no_overlay()
        assert o.active is False

    def test_mode_is_no_overlay(self) -> None:
        assert VenusAspectOverlay.no_overlay().overlay_mode == "no_overlay"

    def test_all_optional_fields_are_empty(self) -> None:
        o = VenusAspectOverlay.no_overlay()
        assert o.venus_sign is None
        assert o.aspect_key is None
        assert o.combined_pattern == ()
        assert o.instagram_hook_suggestion == ""

    def test_to_dict_is_serialisable(self) -> None:
        d = VenusAspectOverlay.no_overlay().to_dict()
        assert d["active"] is False
        assert d["overlay_mode"] == "no_overlay"


# ---------------------------------------------------------------------------
# VenusAspectOverlayContext.from_contexts
# ---------------------------------------------------------------------------

class TestFromContextsNoOverlay:
    def test_no_climate_no_overlay(self) -> None:
        climate = VenusSignClimateContext.from_sign("Ophiuchus")  # not registered
        cards = _cards_ctx([_signal("venus-square-pluto")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.active is False

    def test_no_venus_aspect_no_overlay(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("mars-square-saturn")])  # Mars-Saturn: no Venus
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.active is False

    def test_no_signals_no_overlay(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.active is False

    def test_jupiter_saturn_signal_no_overlay(self) -> None:
        """Jupiter-Saturn card does not involve Venus."""
        climate = _climate_ctx("Capricorn")
        cards = _cards_ctx([_signal("jupiter-square-saturn")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.active is False


class TestFromContextsFriction:
    def test_taurus_venus_pluto_tense_activates_overlay(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.active is True

    def test_overlay_mode_is_friction(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.overlay_mode == "friction"

    def test_hook_priority_is_aspect_first(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.hook_priority == "aspect_first"

    def test_compensation_priority_is_both_layers(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.compensation_priority == "both_layers"

    def test_sign_is_correctly_set(self) -> None:
        climate = _climate_ctx("Gemini")
        cards = _cards_ctx([_signal("mars-opposition-venus", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.venus_sign == "Gemini"

    def test_aspect_key_is_set(self) -> None:
        climate = _climate_ctx("Gemini")
        cards = _cards_ctx([_signal("mars-opposition-venus", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.aspect_key == "mars_venus"

    def test_combined_pattern_is_populated(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert len(ctx.overlay.combined_pattern) >= 3

    def test_climate_background_is_nonempty(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert len(ctx.overlay.climate_background) > 10

    def test_aspect_trigger_is_nonempty(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert len(ctx.overlay.aspect_trigger) > 5

    def test_instagram_hook_suggestion_is_nonempty(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert len(ctx.overlay.instagram_hook_suggestion) > 10

    def test_libra_venus_pluto_activates_overlay(self) -> None:
        climate = _climate_ctx("Libra")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.active is True
        assert ctx.overlay.venus_sign == "Libra"
        assert ctx.overlay.overlay_mode == "friction"

    def test_capricorn_venus_pluto_activates_overlay(self) -> None:
        climate = _climate_ctx("Capricorn")
        cards = _cards_ctx([_signal("venus-square-pluto", polarity="tense")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.active is True
        assert ctx.overlay.venus_sign == "Capricorn"
        combined = " ".join(ctx.overlay.combined_pattern).lower()
        assert "страх" in combined or "компульс" in combined or "труд" in combined


class TestFromContextsOpportunity:
    def test_harmonious_venus_aspect_gives_opportunity(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-trine-pluto", polarity="harmonious")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.active is True
        assert ctx.overlay.overlay_mode == "opportunity"

    def test_opportunity_hook_priority_is_climate_first(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-trine-pluto", polarity="harmonious")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.hook_priority == "climate_first"

    def test_opportunity_compensation_is_aspect_card(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-trine-pluto", polarity="harmonious")])
        ctx = VenusAspectOverlayContext.from_contexts(climate, cards)
        assert ctx.overlay.compensation_priority == "aspect_card"


class TestToDict:
    def test_to_dict_has_overlay_key(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto")])
        d = VenusAspectOverlayContext.from_contexts(climate, cards).to_dict()
        assert "overlay" in d

    def test_to_dict_overlay_has_all_expected_fields(self) -> None:
        climate = _climate_ctx("Taurus")
        cards = _cards_ctx([_signal("venus-square-pluto")])
        d = VenusAspectOverlayContext.from_contexts(climate, cards).to_dict()["overlay"]
        for field in (
            "active", "overlay_mode", "venus_sign", "aspect_key", "aspect_polarity",
            "climate_background", "aspect_trigger", "combined_pattern",
            "hook_priority", "compensation_priority", "instagram_hook_suggestion",
        ):
            assert field in d, f"Missing field: {field}"

    def test_no_overlay_to_dict_shape(self) -> None:
        climate = VenusSignClimateContext.from_sign("Ophiuchus")
        cards = _cards_ctx([])
        d = VenusAspectOverlayContext.from_contexts(climate, cards).to_dict()
        assert d["overlay"]["active"] is False


# ---------------------------------------------------------------------------
# Service injection tests (mirror pattern from test_venus_sign_climate.py)
# ---------------------------------------------------------------------------

def _brand(*, content_language: str = "ru", tone_preset: str = "sharp_witty") -> types.SimpleNamespace:
    return types.SimpleNamespace(
        id=str(uuid.uuid4()), name="Test", description="d",
        tone_preset=tone_preset, banned_terms=[], default_hashtags=[],
        face_led_preferred=0, content_language=content_language,
    )


def _astro_signal_record_with_venus(day: date) -> MagicMock:
    astro_day = AstroDayPayload(
        day=day,
        engine_version="v1.real",
        generated_at=datetime(day.year, day.month, day.day, 12, 0, 0),
        signals=[_signal("venus-square-pluto", polarity="tense")],
    )
    rec = MagicMock()
    rec.id = str(uuid.uuid4())
    rec.payload = astro_day.model_dump(mode="json")
    return rec


class TestCaptionServiceInjectsOverlayContext:
    def test_caption_payload_contains_venus_aspect_overlay_context(self) -> None:
        from astro_content_agent.schemas.drafts import PostDraftPayload
        from astro_content_agent.services.content.caption_service import CaptionService

        captured: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured.update(input_payload)
            return PostDraftPayload(
                title="t", hook="h", caption="c", cta="cta", hashtags=[], voice_note="v", metadata={}
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
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = (
            _astro_signal_record_with_venus(date(2026, 4, 10))
        )
        mock_deps.plan_repo.get_by_brand_and_day.return_value = None
        mock_deps.pillar_balancer.get_recent_pillar_usage.return_value = {}
        mock_deps.pillar_balancer.to_prompt_hint.return_value = ""

        svc = CaptionService(runner=mock_runner, deps=mock_deps)
        svc.generate_post_draft(
            db=MagicMock(), brand_profile_id=brand.id,
            day=date(2026, 4, 10), content_plan=None, plan_slot=None,
        )
        assert "venus_aspect_overlay_context" in captured
        ov = captured["venus_aspect_overlay_context"]
        assert "overlay" in ov
        assert "active" in ov["overlay"]


class TestReelServiceInjectsOverlayContext:
    def test_reel_payload_contains_venus_aspect_overlay_context(self) -> None:
        from astro_content_agent.schemas.drafts import ReelDraftPayload
        from astro_content_agent.services.content.reel_script_service import ReelScriptService

        captured: dict = {}

        def fake_run_json(db, prompt_ref, schema, input_payload, metadata):  # noqa: ANN001
            captured.update(input_payload)
            return ReelDraftPayload(
                hook_0_3s="h", hook="H", reel_type="talking_head", script="s", cta="c", metadata={}
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
        mock_deps.astro_signal_service.get_or_calculate_today.return_value = (
            _astro_signal_record_with_venus(date(2026, 4, 10))
        )
        mock_deps.plan_repo.get_by_brand_and_day.return_value = None
        mock_deps.pillar_balancer.get_recent_pillar_usage.return_value = {}
        mock_deps.pillar_balancer.to_prompt_hint.return_value = ""

        svc = ReelScriptService(runner=mock_runner, deps=mock_deps)
        svc.generate_reel_draft(
            db=MagicMock(), brand_profile_id=brand.id,
            day=date(2026, 4, 10), content_plan=None, plan_slot=None,
        )
        assert "venus_aspect_overlay_context" in captured
        ov = captured["venus_aspect_overlay_context"]
        assert "overlay" in ov
