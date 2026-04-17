"""Tests for venus_editorial_checklist (heuristics + markdown output)."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from astro_content_agent.astro.ephemeris import PlanetPosition
from astro_content_agent.schemas.astro import AstroDayPayload, TransitSignal
from astro_content_agent.services.content.venus_editorial_checklist import (
    render_editorial_checklist_markdown,
    write_editorial_checklist,
)
from astro_content_agent.services.content.venus_weekly_selector import VenusWeeklySelector


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
        headline="x",
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


def _write_minimal_post(path: Path, hook: str, caption: str, cta: str) -> None:
    path.write_text(
        "\n".join(
            [
                "# Venus weekly — post draft",
                "## Hook",
                hook,
                "## Caption",
                caption,
                "## CTA",
                cta,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_minimal_reel(path: Path, h0: str, script: str, cta: str) -> None:
    path.write_text(
        "\n".join(
            [
                "# Venus weekly — reel draft",
                "## hook_0_3s",
                h0,
                "## Spoken hook",
                h0 + " extended",
                "## Script",
                script,
                "## CTA",
                cta,
                "",
            ]
        ),
        encoding="utf-8",
    )


@patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
def test_checklist_contains_sections(mock_compute, tmp_path: Path) -> None:
    mock_compute.return_value = _mock_venus("Taurus")
    pkg = VenusWeeklySelector.select_for_week(date(2026, 4, 20), astro_days=[_day(date(2026, 4, 14))])
    ws = pkg.week_start.isoformat()
    week_dir = tmp_path / ws
    week_dir.mkdir()
    cap = "Параграф.\n\nЧто помогает:\n- один\n- два\n- три\n"
    _write_minimal_post(
        week_dir / f"venus_weekly_post_{ws}.md",
        hook="Достаточно длинная зацепка для теста климата",
        caption=cap,
        cta="Сохрани, если узнал себя.",
    )
    scr = "word " * 50 + "\n\nКомпенсация: что помогает\n- a\n- b\n"
    _write_minimal_reel(
        week_dir / f"venus_weekly_reel_{ws}.md",
        h0="Короткий рилс-хук",
        script=scr,
        cta="Напиши в комментах.",
    )

    md = render_editorial_checklist_markdown(pkg=pkg, week_dir=week_dir, weekly_venus_root=tmp_path)
    assert "# Venus editorial checklist" in md
    assert "## Post check" in md
    assert "## Reel check" in md
    assert "## Final weekly recommendation" in md
    assert "publish_now" in md or "publish_with_light_edits" in md


@patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions")
def test_write_editorial_checklist_file(mock_compute, tmp_path: Path) -> None:
    mock_compute.return_value = _mock_venus("Taurus")
    pkg = VenusWeeklySelector.select_for_week(date(2026, 4, 13), astro_days=None)
    ws = pkg.week_start.isoformat()
    week_dir = tmp_path / ws
    week_dir.mkdir()
    _write_minimal_post(
        week_dir / f"venus_weekly_post_{ws}.md",
        hook="Нормальная длина зацепки для поста",
        caption="Текст\n\n- пункт\n- пункт\n",
        cta="Сохрани.",
    )
    _write_minimal_reel(
        week_dir / f"venus_weekly_reel_{ws}.md",
        h0="Рилс хук тут",
        script="script " * 30 + "\nчто помогает:\n- x\n- y\n",
        cta="Подпишись.",
    )
    out = write_editorial_checklist(pkg, week_dir, weekly_venus_root=tmp_path)
    assert out.name == f"venus_editorial_checklist_{ws}.md"
    assert out.is_file()


def test_missing_post_raises(tmp_path: Path) -> None:
    with patch("astro_content_agent.services.content.venus_weekly_selector.compute_positions") as m:
        m.return_value = _mock_venus("Gemini")
        pkg = VenusWeeklySelector.select_for_week(date(2026, 4, 27), astro_days=[_day(date(2026, 4, 28))])
    week_dir = tmp_path / "empty"
    week_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        render_editorial_checklist_markdown(pkg=pkg, week_dir=week_dir)
