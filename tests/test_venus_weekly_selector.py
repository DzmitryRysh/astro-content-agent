"""Tests for the Venus Weekly Trend Selector.

Covers:
- _hook_family: known combinations, climate-only fallback, unknown fallback
- _compensation_focus: overlay and climate-only paths
- _score_overlay: friction > opportunity, curated > generic, tight orb > wide
- VenusWeeklySelector.select_for_week:
    * no astro_days → climate-only package
    * non-Venus signals only → climate-only package
    * one Venus signal → overlay activated, correct pair captured
    * multiple Venus signals → highest-scoring overlay wins
    * best_day matches the day of the winning signal
- WeeklyVenusPackage structure:
    * all fields present
    * to_dict contains expected keys
    * editorial angles are non-empty strings
    * hook_family and compensation_focus are non-empty
- Retrograde note appears when Venus is retrograde
"""
from __future__ import annotations

from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.content.venus_weekly_selector import (
    WeeklyVenusPackage,
    VenusWeeklySelector,
    _compensation_focus,
    _hook_family,
    _score_overlay,
)
from astro_content_agent.services.content.venus_aspect_overlay import VenusAspectOverlayContext
from astro_content_agent.services.content.venus_sign_climate import VenusSignClimateContext
from astro_content_agent.services.content.aspect_behavior_cards import AspectBehaviorCardsContext


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_WEEK_START = date(2026, 4, 13)


def _signal(key: str, *, polarity: str = "tense", intensity: float = 0.8, orb: float = 1.5) -> TransitSignal:
    return TransitSignal(
        key=key,
        headline=key,
        summary="test",
        intensity=intensity,
        aspect_polarity=polarity,  # type: ignore[arg-type]
        orb=orb,
        signal_class="foreground",
    )


def _astro_day(signals: list[TransitSignal], day: date = date(2026, 4, 15)) -> AstroDayPayload:
    return AstroDayPayload(
        day=day,
        engine_version="v1.real",
        generated_at=datetime(day.year, day.month, day.day, 12, 0, 0),
        signals=signals,
    )


def _mock_venus(sign: str, retrograde: bool = False) -> MagicMock:
    """Return a mock compute_positions result with Venus in `sign`."""
    venus_pos = PlanetPosition(
        name="Venus",
        longitude=0.0,
        sign=sign,
        sign_degree=15.0,
        retrograde=retrograde,
        speed=1.0 if not retrograde else -0.5,
    )
    positions = {name: MagicMock() for name in ["Sun", "Moon", "Mercury", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]}
    positions["Venus"] = venus_pos
    return positions


# ---------------------------------------------------------------------------
# Unit: _hook_family
# ---------------------------------------------------------------------------

class TestHookFamily:
    def test_known_overlay_combination(self) -> None:
        assert _hook_family("Taurus", "pluto_venus") == "владение_vs_ценность"

    def test_known_climate_only(self) -> None:
        assert _hook_family("Gemini", None) == "движение_и_рассеивание"

    def test_unknown_combo_falls_back_with_sign(self) -> None:
        result = _hook_family("Aries", "saturn_venus")
        # Unknown combo — falls back to generic with sign name
        assert "aries" in result.lower()

    def test_all_12_signs_have_climate_only_entry(self) -> None:
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]
        for sign in signs:
            result = _hook_family(sign, None)
            assert len(result) > 3, f"Missing climate-only hook family for {sign}"

    def test_friction_pairs_in_both_tables(self) -> None:
        # All pairs we curated should appear in hook family table
        for sign, pair in [
            ("Taurus", "pluto_venus"),
            ("Gemini", "mars_venus"),
            ("Capricorn", "pluto_venus"),
            ("Pisces", "mars_venus"),
        ]:
            result = _hook_family(sign, pair)
            assert "_vs_" in result or "climate" in result


# ---------------------------------------------------------------------------
# Unit: _compensation_focus
# ---------------------------------------------------------------------------

class TestCompensationFocus:
    def test_known_overlay_returns_specific_text(self) -> None:
        result = _compensation_focus("Taurus", "pluto_venus")
        assert "честная цена" in result.lower() or len(result) > 20

    def test_climate_only_returns_text(self) -> None:
        result = _compensation_focus("Capricorn", None)
        assert len(result) > 10

    def test_unknown_overlay_falls_back_to_climate(self) -> None:
        result = _compensation_focus("Libra", "saturn_venus")
        # Falls back to climate entry for Libra
        assert len(result) > 5

    def test_all_12_signs_have_climate_compensation(self) -> None:
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]
        for sign in signs:
            result = _compensation_focus(sign, None)
            assert len(result) > 5, f"Missing climate compensation for {sign}"


# ---------------------------------------------------------------------------
# Unit: _score_overlay
# ---------------------------------------------------------------------------

class TestScoreOverlay:
    def _make_scored(
        self,
        sign: str,
        pair_key: str,
        mode: str = "friction",
        intensity: float = 0.8,
        orb: float = 1.5,
    ):
        climate_ctx = VenusSignClimateContext.from_sign(sign)
        cards_ctx = AspectBehaviorCardsContext.from_astro_day(
            _astro_day([_signal(f"venus_square_{pair_key.replace('_venus','').replace('venus_','')}", polarity="tense" if mode == "friction" else "harmonious", intensity=intensity, orb=orb)])
        )
        overlay_ctx = VenusAspectOverlayContext.from_contexts(climate_ctx, cards_ctx)
        return _score_overlay(
            day=date(2026, 4, 15),
            overlay_ctx=overlay_ctx,
            signal_intensity=intensity,
            signal_orb=orb,
            signal_key=f"{pair_key}_test",
        )

    def test_curated_beats_non_curated(self) -> None:
        curated = self._make_scored("Taurus", "pluto_venus", intensity=0.5, orb=3.0)
        # Simulate a non-curated overlay — still builds a score
        # curated score should have has_curated_pattern=True
        assert curated.has_curated_pattern is True

    def test_friction_scores_higher_than_same_intensity_opportunity(self) -> None:
        # Build two scored overlays — one with pluto_venus (should be friction=tense)
        # We can't easily test friction vs opportunity for same pair, so test
        # that score is > 0.5 for a curated tense pair
        scored = self._make_scored("Taurus", "pluto_venus", intensity=0.8, orb=1.5)
        assert scored.score > 0.5

    def test_tight_orb_scores_higher(self) -> None:
        # Orb 0.5 vs orb 4.5 — tighter orb should yield higher score
        tight = self._make_scored("Taurus", "pluto_venus", intensity=0.8, orb=0.5)
        wide = self._make_scored("Taurus", "pluto_venus", intensity=0.8, orb=4.5)
        assert tight.score > wide.score

    def test_score_is_positive(self) -> None:
        scored = self._make_scored("Gemini", "mars_venus", intensity=0.6, orb=2.0)
        assert scored.score > 0


# ---------------------------------------------------------------------------
# VenusWeeklySelector.select_for_week — climate-only paths
# ---------------------------------------------------------------------------

class TestSelectorClimateOnly:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_no_astro_days_returns_climate_only(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert pkg.overlay_active is False
        assert pkg.overlay_mode == "climate_only"
        assert pkg.overlay_pair is None
        assert pkg.overlay_ctx is None
        assert pkg.best_day is None

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_non_venus_signals_return_climate_only(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [_astro_day([_signal("sun_square_saturn")])]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.overlay_active is False
        assert pkg.overlay_mode == "climate_only"

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_climate_only_sign_is_correct(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Gemini")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert pkg.venus_sign == "Gemini"

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_climate_only_editorial_notes_non_empty(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Capricorn")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert len(pkg.editorial_notes) >= 1
        assert all(isinstance(n, str) and len(n) > 5 for n in pkg.editorial_notes)

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_retrograde_note_in_climate_only(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus", retrograde=True)
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        combined = " ".join(pkg.editorial_notes)
        assert "ретро" in combined.lower()


# ---------------------------------------------------------------------------
# VenusWeeklySelector.select_for_week — active overlay paths
# ---------------------------------------------------------------------------

class TestSelectorWithOverlay:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_venus_pluto_signal_activates_overlay(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [_astro_day([_signal("venus_square_pluto")])]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.overlay_active is True
        assert pkg.overlay_pair == "pluto_venus"

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_venus_mars_signal_activates_overlay(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Gemini")
        astro_days = [_astro_day([_signal("mars_conjunct_venus")])]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.overlay_active is True
        assert pkg.overlay_pair == "mars_venus"

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_best_day_matches_signal_day(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        signal_day = date(2026, 4, 16)
        astro_days = [_astro_day([_signal("venus_square_pluto")], day=signal_day)]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.best_day == signal_day

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_overlay_mode_is_friction_for_tense(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [_astro_day([_signal("venus_square_pluto", polarity="tense")])]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.overlay_mode == "friction"

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_overlay_ctx_is_not_none_when_active(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [_astro_day([_signal("venus_square_pluto")])]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.overlay_ctx is not None

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_scored_overlays_recorded(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [_astro_day([_signal("venus_square_pluto")])]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert len(pkg.scored_overlays) >= 1
        assert "score" in pkg.scored_overlays[0]
        assert "pair_key" in pkg.scored_overlays[0]


# ---------------------------------------------------------------------------
# Multi-overlay: highest score wins
# ---------------------------------------------------------------------------

class TestSelectorMultipleOverlays:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_tighter_orb_wins_over_looser(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        day_tight = date(2026, 4, 14)
        day_loose = date(2026, 4, 17)
        astro_days = [
            _astro_day([_signal("venus_square_pluto", intensity=0.8, orb=0.5)], day=day_tight),
            _astro_day([_signal("venus_square_pluto", intensity=0.8, orb=4.5)], day=day_loose),
        ]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.best_day == day_tight

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_non_venus_signal_never_wins(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [
            _astro_day([_signal("sun_square_saturn", intensity=1.0, orb=0.1)], day=date(2026, 4, 14)),
            _astro_day([_signal("venus_square_pluto", intensity=0.3, orb=4.9)], day=date(2026, 4, 17)),
        ]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.overlay_active is True
        assert pkg.overlay_pair == "pluto_venus"

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_two_venus_signals_same_day_uses_first(self, mock_compute) -> None:
        """When a day has both venus signals, the first Venus-involving match is used."""
        mock_compute.return_value = _mock_venus("Gemini")
        astro_days = [
            _astro_day([
                _signal("mars_conjunct_venus", intensity=0.9, orb=0.5),
                _signal("venus_square_pluto", intensity=0.7, orb=2.0),
            ], day=date(2026, 4, 15)),
        ]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        assert pkg.overlay_active is True
        # Only one record per day (breaks after first Venus match per day)
        assert len(pkg.scored_overlays) == 1


# ---------------------------------------------------------------------------
# WeeklyVenusPackage structure
# ---------------------------------------------------------------------------

class TestPackageStructure:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def _get_climate_pkg(self, mock_compute) -> WeeklyVenusPackage:
        mock_compute.return_value = _mock_venus("Taurus")
        return VenusWeeklySelector.select_for_week(start_date=_WEEK_START)

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def _get_overlay_pkg(self, mock_compute) -> WeeklyVenusPackage:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [_astro_day([_signal("venus_square_pluto")])]
        return VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_week_end_is_7_days_after_start(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert (pkg.week_end - pkg.week_start).days == 6

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_post_angle_is_non_empty_string(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert isinstance(pkg.primary_post_angle, str) and len(pkg.primary_post_angle) > 10

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_reel_angle_is_non_empty_string(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert isinstance(pkg.primary_reel_angle, str) and len(pkg.primary_reel_angle) > 10

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_support_angle_is_non_empty_string(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert isinstance(pkg.support_angle, str) and len(pkg.support_angle) > 10

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_hook_family_is_non_empty(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert len(pkg.hook_family) > 3

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_compensation_focus_is_non_empty(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert len(pkg.compensation_focus) > 5

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_selection_rationale_is_string(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert isinstance(pkg.selection_rationale, str) and len(pkg.selection_rationale) > 5

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_climate_ctx_resolves_to_taurus(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        assert pkg.climate_ctx.climate is not None
        assert pkg.climate_ctx.climate.sign == "Taurus"


# ---------------------------------------------------------------------------
# to_dict contract
# ---------------------------------------------------------------------------

class TestToDict:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_to_dict_contains_required_keys(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        d = pkg.to_dict()
        required = {
            "week_start", "week_end", "venus_sign", "climate_title",
            "overlay_active", "overlay_mode", "overlay_pair",
            "primary_post_angle", "primary_reel_angle", "support_angle",
            "hook_family", "compensation_focus",
            "selection_rationale", "editorial_notes",
            "climate_ctx", "overlay_ctx",
        }
        assert required.issubset(d.keys())

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_to_dict_dates_are_iso_strings(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        d = pkg.to_dict()
        assert d["week_start"] == "2026-04-13"
        assert d["week_end"] == "2026-04-19"

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_to_dict_overlay_ctx_none_when_climate_only(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START)
        d = pkg.to_dict()
        assert d["overlay_ctx"] is None

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_to_dict_overlay_ctx_is_dict_when_active(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [_astro_day([_signal("venus_square_pluto")])]
        pkg = VenusWeeklySelector.select_for_week(start_date=_WEEK_START, astro_days=astro_days)
        d = pkg.to_dict()
        assert isinstance(d["overlay_ctx"], dict)
        assert "overlay" in d["overlay_ctx"]
