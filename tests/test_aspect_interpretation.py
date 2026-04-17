"""Tests for harmonious vs tense aspect interpretation.

Covers:
- ASPECT_POLARITY_MAP: correct polarity for each aspect type
- aspect_polarity_from_key: extraction from signal key strings
- AstroEngineV0: aspect_polarity is set on generated TransitSignals
- ASPECT_POLARITY_FRAMING: all three polarities defined with required keys
- MoneyAstrologyContext.from_astro_day: aspect_polarities collected from signals
- MoneyAstrologyContext.to_dict: aspect_polarities and aspect_framing_hints present
- Harmonious aspect framing: uses opening/support/opportunity words
- Tense aspect framing: uses friction/tension/conflict words
"""

from __future__ import annotations

import types
from datetime import UTC, date, datetime

import pytest

from astro_content_agent.astro.engine import AstroEngineV0, EngineInput
from astro_content_agent.schemas.astro import (
    ASPECT_POLARITY_MAP,
    TransitSignal,
    aspect_polarity_from_key,
)
from astro_content_agent.services.content.money_astrology import (
    ASPECT_POLARITY_FRAMING,
    MoneyAstrologyContext,
)


# ---------------------------------------------------------------------------
# ASPECT_POLARITY_MAP
# ---------------------------------------------------------------------------

class TestAspectPolarityMap:
    def test_sextile_harmonious(self) -> None:
        assert ASPECT_POLARITY_MAP["sextile"] == "harmonious"

    def test_trine_harmonious(self) -> None:
        assert ASPECT_POLARITY_MAP["trine"] == "harmonious"

    def test_square_tense(self) -> None:
        assert ASPECT_POLARITY_MAP["square"] == "tense"

    def test_opposition_tense(self) -> None:
        assert ASPECT_POLARITY_MAP["opposition"] == "tense"

    def test_conjunct_neutral(self) -> None:
        assert ASPECT_POLARITY_MAP["conjunct"] == "neutral"

    def test_conjunction_neutral(self) -> None:
        assert ASPECT_POLARITY_MAP["conjunction"] == "neutral"


# ---------------------------------------------------------------------------
# aspect_polarity_from_key
# ---------------------------------------------------------------------------

class TestAspectPolarityFromKey:
    def test_sextile_in_key(self) -> None:
        assert aspect_polarity_from_key("venus-sextile-mercury") == "harmonious"

    def test_trine_in_key(self) -> None:
        assert aspect_polarity_from_key("moon-trine-jupiter") == "harmonious"

    def test_square_in_key(self) -> None:
        assert aspect_polarity_from_key("venus-square-saturn") == "tense"

    def test_opposition_in_key(self) -> None:
        assert aspect_polarity_from_key("mars-opposition-neptune") == "tense"

    def test_conjunct_in_key(self) -> None:
        assert aspect_polarity_from_key("sun-conjunct-mercury") == "neutral"

    def test_unknown_key_returns_none(self) -> None:
        assert aspect_polarity_from_key("moon-retrograde") is None

    def test_empty_key_returns_none(self) -> None:
        assert aspect_polarity_from_key("") is None


# ---------------------------------------------------------------------------
# TransitSignal — aspect_polarity field
# ---------------------------------------------------------------------------

class TestTransitSignalPolarityField:
    def _signal(self, polarity: str | None) -> TransitSignal:
        return TransitSignal(
            key="test-key",
            headline="Test signal",
            summary="Test summary",
            intensity=0.5,
            aspect_polarity=polarity,
        )

    def test_harmonious_stored(self) -> None:
        s = self._signal("harmonious")
        assert s.aspect_polarity == "harmonious"

    def test_tense_stored(self) -> None:
        s = self._signal("tense")
        assert s.aspect_polarity == "tense"

    def test_neutral_stored(self) -> None:
        s = self._signal("neutral")
        assert s.aspect_polarity == "neutral"

    def test_none_allowed(self) -> None:
        s = self._signal(None)
        assert s.aspect_polarity is None

    def test_default_is_none(self) -> None:
        s = TransitSignal(key="k", headline="h", summary="s", intensity=0.5)
        assert s.aspect_polarity is None


# ---------------------------------------------------------------------------
# AstroEngineV0 — sets aspect_polarity on signals
# ---------------------------------------------------------------------------

class TestEngineAspectPolarity:
    def test_engine_sets_aspect_polarity(self) -> None:
        engine = AstroEngineV0()
        payload = engine.generate_day(EngineInput(brand_profile_id="test-brand", day=date(2026, 1, 15)))
        for signal in payload.signals:
            # All signals should have a polarity (since all aspects are in the map)
            assert signal.aspect_polarity in ("harmonious", "tense", "neutral"), (
                f"Signal {signal.key} has unexpected polarity: {signal.aspect_polarity}"
            )

    def test_engine_harmonious_signals_exist(self) -> None:
        """Over multiple days, we should see some harmonious signals."""
        engine = AstroEngineV0()
        harmonious_found = False
        for day_offset in range(30):
            payload = engine.generate_day(
                EngineInput(brand_profile_id="bp", day=date(2026, 1, day_offset + 1))
            )
            for s in payload.signals:
                if s.aspect_polarity == "harmonious":
                    harmonious_found = True
                    break
            if harmonious_found:
                break
        assert harmonious_found, "Expected harmonious signals in 30-day span"

    def test_engine_tense_signals_exist(self) -> None:
        """Over multiple days, we should see some tense signals."""
        engine = AstroEngineV0()
        tense_found = False
        for day_offset in range(30):
            payload = engine.generate_day(
                EngineInput(brand_profile_id="bp", day=date(2026, 1, day_offset + 1))
            )
            for s in payload.signals:
                if s.aspect_polarity == "tense":
                    tense_found = True
                    break
            if tense_found:
                break
        assert tense_found, "Expected tense signals in 30-day span"


# ---------------------------------------------------------------------------
# ASPECT_POLARITY_FRAMING constants
# ---------------------------------------------------------------------------

class TestAspectPolarityFramingConstants:
    _required_keys = [
        "core_nature_ru", "money_framing_ru", "hook_style_ru",
        "framing_words_ru", "avoid_ru",
    ]

    @pytest.mark.parametrize("polarity", ["harmonious", "tense", "neutral"])
    def test_polarity_exists(self, polarity: str) -> None:
        assert polarity in ASPECT_POLARITY_FRAMING

    @pytest.mark.parametrize("polarity", ["harmonious", "tense", "neutral"])
    def test_required_keys_present(self, polarity: str) -> None:
        framing = ASPECT_POLARITY_FRAMING[polarity]
        for key in self._required_keys:
            assert key in framing, f"Missing key '{key}' in ASPECT_POLARITY_FRAMING['{polarity}']"

    def test_harmonious_framing_words_positive(self) -> None:
        words = ASPECT_POLARITY_FRAMING["harmonious"]["framing_words_ru"]
        assert len(words) >= 3
        # Should contain at least one "opening/opportunity" concept
        assert any("окно" in w or "легче" in w or "возможн" in w or "поддержк" in w for w in words)

    def test_tense_framing_words_conflict(self) -> None:
        words = ASPECT_POLARITY_FRAMING["tense"]["framing_words_ru"]
        assert len(words) >= 3
        assert any("напряжен" in w or "конфликт" in w or "давлени" in w for w in words)

    def test_harmonious_avoid_includes_negative_framing(self) -> None:
        avoid = ASPECT_POLARITY_FRAMING["harmonious"]["avoid_ru"]
        assert any("конфликт" in a or "занижаешь" in a or "страх" in a for a in avoid)

    def test_harmonious_has_hook_examples(self) -> None:
        framing = ASPECT_POLARITY_FRAMING["harmonious"]
        examples = framing.get("hook_examples_ru", [])
        assert len(examples) >= 2

    def test_tense_has_hook_examples(self) -> None:
        framing = ASPECT_POLARITY_FRAMING["tense"]
        examples = framing.get("hook_examples_ru", [])
        assert len(examples) >= 2


# ---------------------------------------------------------------------------
# MoneyAstrologyContext — aspect polarity collection
# ---------------------------------------------------------------------------

def _make_astro_day(signals_data: list[dict]) -> object:
    """Build a minimal AstroDayPayload-like object for testing."""
    from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal

    signals = [TransitSignal(**d) for d in signals_data]
    return AstroDayPayload(
        day=date(2026, 1, 15),
        engine_version="v0.test",
        generated_at=datetime.now(UTC),
        signals=signals,
    )


class TestMoneyAstrologyContextAspectPolarity:
    def test_harmonious_polarity_collected(self) -> None:
        astro_day = _make_astro_day([{
            "key": "venus-sextile-mercury",
            "headline": "Venus sextile Mercury",
            "summary": "opportunity",
            "intensity": 0.5,
            "aspect_polarity": "harmonious",
        }])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert "venus-sextile-mercury" in ctx.aspect_polarities
        assert ctx.aspect_polarities["venus-sextile-mercury"] == "harmonious"

    def test_tense_polarity_collected(self) -> None:
        astro_day = _make_astro_day([{
            "key": "venus-square-saturn",
            "headline": "Venus square Saturn",
            "summary": "friction",
            "intensity": 0.7,
            "aspect_polarity": "tense",
        }])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert ctx.aspect_polarities["venus-square-saturn"] == "tense"

    def test_none_polarity_not_in_dict(self) -> None:
        astro_day = _make_astro_day([{
            "key": "moon-retrograde",
            "headline": "Moon retrograde",
            "summary": "shift",
            "intensity": 0.4,
            "aspect_polarity": None,
        }])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert "moon-retrograde" not in ctx.aspect_polarities

    def test_multiple_polarities_collected(self) -> None:
        astro_day = _make_astro_day([
            {"key": "venus-sextile-mercury", "headline": "h", "summary": "s",
             "intensity": 0.5, "aspect_polarity": "harmonious"},
            {"key": "mars-square-saturn", "headline": "h", "summary": "s",
             "intensity": 0.7, "aspect_polarity": "tense"},
            {"key": "sun-conjunct-moon", "headline": "h", "summary": "s",
             "intensity": 0.6, "aspect_polarity": "neutral"},
        ])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        assert ctx.aspect_polarities["venus-sextile-mercury"] == "harmonious"
        assert ctx.aspect_polarities["mars-square-saturn"] == "tense"
        assert ctx.aspect_polarities["sun-conjunct-moon"] == "neutral"


class TestMoneyAstrologyContextToDict:
    def test_to_dict_has_aspect_polarities(self) -> None:
        astro_day = _make_astro_day([{
            "key": "moon-trine-venus",
            "headline": "Moon trine Venus",
            "summary": "flow",
            "intensity": 0.6,
            "aspect_polarity": "harmonious",
        }])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        d = ctx.to_dict()
        assert "aspect_polarities" in d
        assert d["aspect_polarities"]["moon-trine-venus"] == "harmonious"

    def test_to_dict_has_aspect_framing_hints(self) -> None:
        astro_day = _make_astro_day([{
            "key": "venus-square-saturn",
            "headline": "Venus square Saturn",
            "summary": "friction",
            "intensity": 0.7,
            "aspect_polarity": "tense",
        }])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        d = ctx.to_dict()
        assert "aspect_framing_hints" in d
        hint = d["aspect_framing_hints"]["venus-square-saturn"]
        assert hint["polarity"] == "tense"
        assert "money_framing_ru" in hint
        assert len(hint["avoid_ru"]) > 0

    def test_harmonious_hint_has_correct_tone(self) -> None:
        astro_day = _make_astro_day([{
            "key": "venus-trine-jupiter",
            "headline": "Venus trine Jupiter",
            "summary": "flow",
            "intensity": 0.8,
            "aspect_polarity": "harmonious",
        }])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        hint = ctx.to_dict()["aspect_framing_hints"]["venus-trine-jupiter"]
        # Harmonious tone should reference opportunity/opening, not conflict
        money_framing = hint["money_framing_ru"].lower()
        assert any(word in money_framing for word in ["момент", "легче", "окно", "шаг"])

    def test_no_signals_no_framing_hints(self) -> None:
        astro_day = _make_astro_day([])
        ctx = MoneyAstrologyContext.from_astro_day(astro_day)
        d = ctx.to_dict()
        assert d["aspect_framing_hints"] == {}
        assert d["aspect_polarities"] == {}
