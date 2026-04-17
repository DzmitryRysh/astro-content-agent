"""Tests for weekly Venus draft generation (anti-repeat + file IO; LLM mocked)."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.db.base import Base
from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.services.content.venus_weekly_drafts import (
    PreviousWeekSnapshot,
    build_anti_repeat_instruction,
    generate_weekly_venus_drafts,
    load_previous_week_snapshot,
    support_angle_is_meaningful,
)
from astro_content_agent.services.content.venus_weekly_selector import VenusWeeklySelector
from astro_content_agent.tests.fakes.fake_openai import FakeOpenAIClient, default_responder


def _mock_venus(sign: str) -> dict:
    venus = PlanetPosition(
        name="Venus", longitude=0.0, sign=sign, sign_degree=15.0,
        retrograde=False, speed=1.0,
    )
    positions = {n: MagicMock() for n in ["Sun", "Moon", "Mercury", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]}
    positions["Venus"] = venus
    return positions


def _sig() -> TransitSignal:
    return TransitSignal(
        key="sun-square-saturn",
        headline="Sun square Saturn",
        summary="x",
        intensity=0.5,
        aspect_polarity="tense",
        orb=2.0,
        signal_class="foreground",
    )


def _day(d: date) -> AstroDayPayload:
    return AstroDayPayload(
        day=d,
        engine_version="v1.real",
        generated_at=datetime(d.year, d.month, d.day, 12, 0, 0),
        signals=[_sig()],
    )


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def ai_runner() -> ResponsesRunner:
    root = Path(__file__).resolve().parents[1] / "services" / "ai" / "prompts"
    return ResponsesRunner(model="test", client=FakeOpenAIClient(default_responder), prompts_root=root)


class TestSupportMeaningful:
    def test_short_false(self) -> None:
        assert support_angle_is_meaningful("short", min_len=36) is False

    def test_long_true(self) -> None:
        s = "x" * 40
        assert support_angle_is_meaningful(s) is True


class TestLoadPreviousWeekSnapshot:
    def test_missing_folder_returns_none(self, tmp_path: Path) -> None:
        assert load_previous_week_snapshot(tmp_path, date(2026, 4, 20)) is None

    def test_loads_review_and_drafts(self, tmp_path: Path) -> None:
        prev = date(2026, 4, 13)
        folder = tmp_path / prev.isoformat()
        folder.mkdir(parents=True)
        (folder / f"venus_weekly_review_{prev.isoformat()}.md").write_text(
            "## Venus climate of the week\n\n- **Знак:** Taurus\n\n## Main post\n\n"
            "- **Hook family:** `накопление_и_инерция`\n",
            encoding="utf-8",
        )
        (folder / f"venus_weekly_post_{prev.isoformat()}.md").write_text(
            "## Hook\n\nСтарый зачин недели.\n\n## Caption\n\nbody\n",
            encoding="utf-8",
        )
        (folder / f"venus_weekly_reel_{prev.isoformat()}.md").write_text(
            "## hook_0_3s\n\nСтарый рилс.\n",
            encoding="utf-8",
        )
        snap = load_previous_week_snapshot(tmp_path, date(2026, 4, 20))
        assert snap is not None
        assert snap.venus_sign == "Taurus"
        assert snap.hook_family == "накопление_и_инерция"
        assert snap.post_hook == "Старый зачин недели."
        assert snap.reel_hook_0_3s == "Старый рилс."


class TestAntiRepeatInstruction:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_same_sign_family_sets_forced_angle(self, mock_compute, tmp_path: Path) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        astro_days = [_day(date(2026, 4, 14))]
        pkg = VenusWeeklySelector.select_for_week(date(2026, 4, 20), astro_days=astro_days)
        prev = PreviousWeekSnapshot(
            week_folder=tmp_path,
            venus_sign="Taurus",
            hook_family=pkg.hook_family,
            post_hook="Повторяющийся зачин",
            reel_hook_0_3s="Повтор 0-3",
        )
        note, forced, log = build_anti_repeat_instruction(pkg, prev)
        assert forced
        assert "Анти-повтор" in note
        assert any("same_sign_same_hook_family" in entry for entry in log)

    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    def test_no_prev_empty(self, mock_compute) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        pkg = VenusWeeklySelector.select_for_week(date(2026, 4, 13), astro_days=None)
        note, forced, log = build_anti_repeat_instruction(pkg, None)
        assert note == ""
        assert forced is None
        assert log == []


class TestGenerateWeeklyFiles:
    @patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
    @patch("astro_content_agent.services.content.venus_weekly_drafts.AstroEngineV1")
    def test_writes_post_and_reel_markdown(
        self,
        mock_engine_cls,
        mock_compute,
        db_session,
        ai_runner: ResponsesRunner,
        tmp_path: Path,
    ) -> None:
        mock_compute.return_value = _mock_venus("Taurus")
        mock_eng = MagicMock()
        mock_eng.generate_day.return_value = _day(date(2026, 4, 16))
        mock_engine_cls.return_value = mock_eng

        pkg = VenusWeeklySelector.select_for_week(date(2026, 4, 13), astro_days=None)
        out = tmp_path / "out"
        brand = type("B", (), {"id": "t", "name": "T", "description": "", "tone_preset": "sharp_witty", "banned_terms": [], "default_hashtags": [], "face_led_preferred": False, "content_language": "ru"})()

        res = generate_weekly_venus_drafts(
            db=db_session,
            runner=ai_runner,
            brand=brand,
            pkg=pkg,
            output_dir=out,
            brand_id="x",
            weekly_venus_root=tmp_path,
        )
        assert res.post_path.is_file()
        assert res.reel_path.is_file()
        post_txt = res.post_path.read_text(encoding="utf-8")
        assert "## Hook" in post_txt
        assert "Если голова сегодня гудит" in post_txt or "перезапуск" in post_txt
