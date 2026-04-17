"""Tests for Venus Weekly Review Artifact (markdown + JSON + file writer)."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

import pytest

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.content.venus_weekly_review import (
    render_weekly_review_markdown,
    weekly_review_json_dict,
    write_weekly_review_artifacts,
)
from astro_content_agent.services.content.venus_weekly_selector import VenusWeeklySelector

WEEK_START = date(2026, 4, 13)


def _pos(sign: str, retrograde: bool = False) -> dict:
    venus = PlanetPosition(
        name="Venus", longitude=0.0, sign=sign, sign_degree=15.0,
        retrograde=retrograde, speed=1.0 if not retrograde else -0.5,
    )
    positions = {n: MagicMock() for n in ["Sun", "Moon", "Mercury", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]}
    positions["Venus"] = venus
    return positions


def _sig(key: str, *, polarity: str = "tense", intensity: float = 0.8, orb: float = 1.2) -> TransitSignal:
    return TransitSignal(
        key=key, headline=key, summary="t",
        intensity=intensity, aspect_polarity=polarity,  # type: ignore[arg-type]
        orb=orb, signal_class="foreground",
    )


def _day(signals: list[TransitSignal], d: date) -> AstroDayPayload:
    return AstroDayPayload(
        day=d, engine_version="v1.real",
        generated_at=datetime(d.year, d.month, d.day, 12, 0, 0),
        signals=signals,
    )


@patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
def _pkg_overlay(mock_compute) -> object:
    mock_compute.return_value = _pos("Taurus")
    return VenusWeeklySelector.select_for_week(
        start_date=WEEK_START,
        astro_days=[_day([_sig("venus_square_pluto")], d=date(2026, 4, 15))],
    )


@patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
def _pkg_climate_only(mock_compute) -> object:
    mock_compute.return_value = _pos("Gemini")
    return VenusWeeklySelector.select_for_week(start_date=WEEK_START)


class TestMarkdownSections:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_contains_all_major_headings(self, mock_compute) -> None:
        mock_compute.return_value = _pos("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=WEEK_START)
        md = render_weekly_review_markdown(pkg)
        for h in (
            "# Venus weekly review",
            "## Week",
            "## Venus climate of the week",
            "## Main overlay",
            "## Main post",
            "## Main reel",
            "## Support angle",
            "## Why this won",
            "## Editorial notes",
            "## Scored overlays",
        ):
            assert h in md, f"missing heading: {h}"

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_overlay_week_includes_alternative_when_two_candidates(self, mock_compute) -> None:
        mock_compute.return_value = _pos("Taurus")
        astro_days = [
            _day([_sig("mars_conjunct_venus", orb=3.5)], d=date(2026, 4, 13)),
            _day([_sig("venus_square_pluto", orb=1.0)], d=date(2026, 4, 16)),
        ]
        pkg = VenusWeeklySelector.select_for_week(start_date=WEEK_START, astro_days=astro_days)
        md = render_weekly_review_markdown(pkg)
        assert "**Альтернатива:**" in md
        assert "mars_venus" in md


class TestJsonDict:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_json_has_expected_keys(self, mock_compute) -> None:
        mock_compute.return_value = _pos("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=WEEK_START)
        d = weekly_review_json_dict(pkg)
        assert d["artifact"] == "venus_weekly_review_v1"
        assert "week_start" in d
        assert "overlay" in d
        assert "main_post" in d
        assert "main_reel" in d
        assert "why_won" in d
        assert isinstance(d["likely_leak"], list)

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_json_roundtrip(self, mock_compute) -> None:
        mock_compute.return_value = _pos("Taurus")
        pkg = VenusWeeklySelector.select_for_week(
            start_date=WEEK_START,
            astro_days=[_day([_sig("venus_square_pluto")], d=date(2026, 4, 15))],
        )
        d = weekly_review_json_dict(pkg)
        s = json.dumps(d, ensure_ascii=False)
        loaded = json.loads(s)
        assert loaded["overlay"]["pair"] == "pluto_venus"


class TestWriteArtifacts:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_writes_md_and_json(self, mock_compute) -> None:
        mock_compute.return_value = _pos("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=WEEK_START)
        with TemporaryDirectory() as td:
            paths = write_weekly_review_artifacts(pkg, Path(td), write_json=True)
            assert paths.markdown.exists()
            assert paths.json_path is not None
            assert paths.json_path.exists()
            assert "venus_weekly_review_2026-04-13" in paths.markdown.name

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_md_only_when_json_disabled(self, mock_compute) -> None:
        mock_compute.return_value = _pos("Taurus")
        pkg = VenusWeeklySelector.select_for_week(start_date=WEEK_START)
        with TemporaryDirectory() as td:
            paths = write_weekly_review_artifacts(pkg, Path(td), write_json=False)
            assert paths.json_path is None
            assert paths.markdown.exists()
