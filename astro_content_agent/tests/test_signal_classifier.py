"""Tests for the transit signal classifier and its integration with AstroEngineV1."""
from __future__ import annotations

from datetime import date

import pytest

from astro_content_agent.astro.classifier import (
    OUTER_SLOW_PLANETS,
    TIGHT_ORB_OVERRIDE,
    classify_transit,
)
from astro_content_agent.astro.engine import AstroEngineV1, EngineInput
from astro_content_agent.schemas.astro import AstroDayPayload


# ---------------------------------------------------------------------------
# classify_transit unit tests
# ---------------------------------------------------------------------------

class TestClassifyTransit:
    # ------ inner-planet involvement -> always foreground ------------------

    def test_sun_trine_moon_foreground(self):
        assert classify_transit("Sun", "Moon", 0.4) == "foreground"

    def test_mercury_square_mars_foreground(self):
        assert classify_transit("Mercury", "Mars", 2.5) == "foreground"

    def test_venus_opposition_jupiter_foreground(self):
        # Jupiter is NOT in OUTER_SLOW -> foreground
        assert classify_transit("Venus", "Jupiter", 3.0) == "foreground"

    def test_moon_conjunction_pluto_foreground(self):
        # Moon is inner/fast -> foreground regardless of Pluto
        assert classify_transit("Moon", "Pluto", 1.5) == "foreground"

    def test_sun_sextile_saturn_foreground(self):
        assert classify_transit("Sun", "Saturn", 2.0) == "foreground"

    def test_mars_conjunction_neptune_foreground(self):
        assert classify_transit("Mars", "Neptune", 0.5) == "foreground"

    # ------ Jupiter is foreground-eligible ---------------------------------

    def test_jupiter_saturn_foreground(self):
        # Jupiter excluded from OUTER_SLOW -> foreground
        assert classify_transit("Jupiter", "Saturn", 4.0) == "foreground"

    def test_jupiter_pluto_foreground(self):
        assert classify_transit("Jupiter", "Pluto", 2.0) == "foreground"

    def test_jupiter_neptune_foreground(self):
        assert classify_transit("Jupiter", "Neptune", 3.5) == "foreground"

    # ------ slow outer-outer pairs -> background by default ---------------

    def test_saturn_pluto_sextile_background(self):
        assert classify_transit("Saturn", "Pluto", 1.5) == "background"

    def test_neptune_pluto_sextile_background(self):
        assert classify_transit("Neptune", "Pluto", 2.7) == "background"

    def test_saturn_uranus_background(self):
        assert classify_transit("Saturn", "Uranus", 3.0) == "background"

    def test_uranus_neptune_background(self):
        assert classify_transit("Uranus", "Neptune", 2.0) == "background"

    def test_saturn_neptune_background(self):
        assert classify_transit("Saturn", "Neptune", 4.0) == "background"

    # ------ tight-orb override for slow-outer pairs -----------------------

    def test_saturn_pluto_tight_elevated_to_foreground(self):
        # orb < TIGHT_ORB_OVERRIDE (1.0) -> foreground even if both outer-slow
        assert classify_transit("Saturn", "Pluto", 0.9) == "foreground"

    def test_saturn_pluto_exactly_at_threshold_is_background(self):
        # orb == TIGHT_ORB_OVERRIDE -> NOT elevated (threshold is strict <)
        assert classify_transit("Saturn", "Pluto", TIGHT_ORB_OVERRIDE) == "background"

    def test_neptune_pluto_very_tight_foreground(self):
        assert classify_transit("Neptune", "Pluto", 0.1) == "foreground"

    def test_uranus_neptune_just_under_threshold_foreground(self):
        assert classify_transit("Uranus", "Neptune", 0.99) == "foreground"

    # ------ None orb handling ---------------------------------------------

    def test_none_orb_inner_planet_still_foreground(self):
        assert classify_transit("Sun", "Moon", None) == "foreground"

    def test_none_orb_outer_pair_no_override_background(self):
        # Can't apply tight-orb override when orb is unknown -> background
        assert classify_transit("Saturn", "Pluto", None) == "background"

    # ------ order of arguments should not matter --------------------------

    def test_argument_order_symmetric_foreground(self):
        assert classify_transit("Sun", "Saturn", 2.0) == classify_transit("Saturn", "Sun", 2.0)

    def test_argument_order_symmetric_background(self):
        assert classify_transit("Saturn", "Pluto", 2.0) == classify_transit("Pluto", "Saturn", 2.0)

    # ------ OUTER_SLOW_PLANETS set is exactly the four slow planets -------

    def test_outer_slow_set_contents(self):
        assert OUTER_SLOW_PLANETS == {"Saturn", "Uranus", "Neptune", "Pluto"}

    def test_jupiter_not_in_outer_slow(self):
        assert "Jupiter" not in OUTER_SLOW_PLANETS

    def test_mars_not_in_outer_slow(self):
        assert "Mars" not in OUTER_SLOW_PLANETS


# ---------------------------------------------------------------------------
# AstroDayPayload.foreground_signals / background_signals properties
# ---------------------------------------------------------------------------

class TestAstroDayPayloadHelpers:
    def _result(self, day: date = date(2026, 4, 7)) -> AstroDayPayload:
        return AstroEngineV1().generate_day(EngineInput("test", day))

    def test_foreground_plus_background_equals_all_signals(self):
        payload = self._result()
        combined = payload.foreground_signals + payload.background_signals
        assert sorted(s.key for s in combined) == sorted(s.key for s in payload.signals)

    def test_foreground_signals_all_classified_correctly(self):
        for s in self._result().foreground_signals:
            assert s.signal_class == "foreground"

    def test_background_signals_all_classified_correctly(self):
        for s in self._result().background_signals:
            assert s.signal_class == "background"

    def test_foreground_signals_not_empty_on_typical_day(self):
        # There is always at least one inner-planet transit in the top-5
        assert len(self._result().foreground_signals) >= 1

    def test_background_signals_include_saturn_pluto_when_not_tight(self):
        # Saturn sextile Pluto on Apr 7 has orb ~1.04 -> background
        payload = self._result(date(2026, 4, 7))
        bg_keys = {s.key for s in payload.background_signals}
        assert "saturn-sextile-pluto" in bg_keys, (
            f"Expected saturn-sextile-pluto in background; got: {bg_keys}"
        )

    def test_properties_are_views_not_copies(self):
        # Modifying the returned list does not affect payload.signals
        payload = self._result()
        original_len = len(payload.signals)
        payload.foreground_signals.clear()  # modifying the returned list
        assert len(payload.signals) == original_len


# ---------------------------------------------------------------------------
# Integration: signal_class field set correctly in V1 output
# ---------------------------------------------------------------------------

class TestSignalClassIntegration:
    def test_signal_class_field_present_on_all_v1_signals(self):
        result = AstroEngineV1().generate_day(EngineInput("test", date(2026, 4, 7)))
        for s in result.signals:
            assert s.signal_class in ("foreground", "background"), (
                f"Unexpected class on {s.key}: {s.signal_class}"
            )

    def test_sun_trine_moon_is_foreground(self):
        # April 7: Sun trine Moon is the tightest signal
        result = AstroEngineV1().generate_day(EngineInput("test", date(2026, 4, 7)))
        top = result.signals[0]
        assert "sun" in top.key and "trine" in top.key and "moon" in top.key
        assert top.signal_class == "foreground"

    def test_v0_signals_default_to_foreground(self):
        from astro_content_agent.astro.engine import AstroEngineV0
        result = AstroEngineV0().generate_day(EngineInput("brand-x", date(2026, 4, 7)))
        for s in result.signals:
            assert s.signal_class == "foreground"

    def test_signal_class_survives_round_trip_serialisation(self):
        result = AstroEngineV1().generate_day(EngineInput("test", date(2026, 4, 7)))
        dumped = result.model_dump(mode="json")
        reloaded = AstroDayPayload.model_validate(dumped)
        original_classes = [s.signal_class for s in result.signals]
        reloaded_classes = [s.signal_class for s in reloaded.signals]
        assert original_classes == reloaded_classes

    def test_classification_is_deterministic(self):
        r1 = AstroEngineV1().generate_day(EngineInput("test", date(2026, 4, 7)))
        r2 = AstroEngineV1().generate_day(EngineInput("test", date(2026, 4, 7)))
        assert [s.signal_class for s in r1.signals] == [s.signal_class for s in r2.signals]
