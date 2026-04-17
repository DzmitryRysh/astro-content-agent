"""Venus Weekly Agent Orchestrator v1 — Phase 1 lifecycle (file-based state, no publish).

Chains existing components in order:
selector → review artifacts → weekly drafts → editorial checklist → state JSON.

Does not modify AstroEngineV1, climate/overlay/selector internals, drafts, or checklist logic.
"""
from __future__ import annotations

import json
import sys
import traceback
import types
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from astro_content_agent.astro.engine import AstroEngineV1, EngineInput
from astro_content_agent.core.config import get_settings
from astro_content_agent.db.base import Base
from astro_content_agent.services.ai.client import OpenAIClientFactory
from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.services.content.venus_editorial_checklist import write_editorial_checklist
from astro_content_agent.services.content.venus_weekly_drafts import generate_weekly_venus_drafts
from astro_content_agent.services.content.venus_weekly_review import write_weekly_review_artifacts
from astro_content_agent.services.content.venus_weekly_selector import WeeklyVenusPackage, VenusWeeklySelector


@dataclass
class WeeklyAgentResult:
    """Outcome of a full agent cycle."""

    week_start: date
    week_end: date
    out_dir: Path
    state_path: Path
    state: dict[str, Any]
    files_written: list[str] = field(default_factory=list)
    error: str | None = None


def _build_astro_days(week_start: date, brand_id: str):
    engine = AstroEngineV1()
    days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        days.append(engine.generate_day(EngineInput(brand_profile_id=brand_id, day=d)))
    return days


def _climate_block(pkg: WeeklyVenusPackage) -> dict[str, Any]:
    summary = ""
    if pkg.climate_ctx.climate is not None:
        summary = pkg.climate_ctx.climate.money_style.strip()[:400]
    return {
        "venus_sign": pkg.venus_sign,
        "climate_title": pkg.climate_title,
        "climate_summary": summary,
    }


def _write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _draft_brand_stub() -> Any:
    return types.SimpleNamespace(
        id="weekly-venus-drafts",
        name="Weekly Venus Drafts",
        description="Weekly collective Venus Instagram drafts — not a live brand.",
        tone_preset="sharp_witty",
        banned_terms=[],
        default_hashtags=[],
        face_led_preferred=False,
        content_language="ru",
    )


def run_venus_weekly_agent_cycle(
    week_start: date,
    *,
    out_dir: Path,
    brand_id: str = "weekly-workflow",
    climate_only: bool = False,
    weekly_venus_root: Path,
) -> WeeklyAgentResult:
    """Run the full weekly pack pipeline and write ``venus_weekly_state_<week_start>.json``.

    On success, ``status`` is ``awaiting_approval`` (Phase 1). On any exception,
    ``status`` is ``failed`` and ``notes`` contains a short error summary.
    """
    week_end = week_start + timedelta(days=6)
    state_name = f"venus_weekly_state_{week_start.isoformat()}.json"
    state_path = out_dir / state_name
    out_dir.mkdir(parents=True, exist_ok=True)

    def _fail_state(exc: BaseException) -> WeeklyAgentResult:
        err = f"{type(exc).__name__}: {exc}"
        payload = {
            "version": 1,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "status": "failed",
            "climate": None,
            "overlay_active": None,
            "overlay_pair": None,
            "review_ready": False,
            "drafts_ready": False,
            "checklist_ready": False,
            "approval_status": "pending",
            "publish_status": "not_started",
            "notes": err + "\n" + traceback.format_exc()[-4000:],
            "outputs": {},
        }
        _write_state(state_path, payload)
        return WeeklyAgentResult(
            week_start=week_start,
            week_end=week_end,
            out_dir=out_dir,
            state_path=state_path,
            state=payload,
            files_written=[state_name],
            error=err,
        )

    try:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for the weekly agent (draft generation step). "
                "Set it in the environment or .env before running."
            )

        if climate_only:
            days = []
        else:
            days = _build_astro_days(week_start, brand_id)

        selector = VenusWeeklySelector()
        pkg = selector.select_for_week(week_start, days)

        review_paths = write_weekly_review_artifacts(pkg, out_dir)
        review_md = review_paths.markdown.name
        review_json = review_paths.json_path.name if review_paths.json_path else None

        sql_engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=sql_engine)
        Session = sessionmaker(bind=sql_engine)
        db = Session()
        runner = ResponsesRunner(
            model=settings.openai_model,
            client=OpenAIClientFactory(api_key=settings.openai_api_key).create(),
        )
        draft_result = generate_weekly_venus_drafts(
            db=db,
            runner=runner,
            brand=_draft_brand_stub(),
            pkg=pkg,
            output_dir=out_dir,
            brand_id=brand_id,
            weekly_venus_root=weekly_venus_root,
        )
        post_name = draft_result.post_path.name
        reel_name = draft_result.reel_path.name
        support_name = draft_result.support_path.name if draft_result.support_path else None

        checklist_path = write_editorial_checklist(
            pkg,
            out_dir,
            weekly_venus_root=weekly_venus_root,
        )
        checklist_name = checklist_path.name

        outputs: dict[str, str] = {
            "review_md": review_md,
            "post_draft": post_name,
            "reel_draft": reel_name,
            "editorial_checklist": checklist_name,
        }
        if review_json:
            outputs["review_json"] = review_json
        if support_name:
            outputs["support_draft"] = support_name

        payload = {
            "version": 1,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "status": "awaiting_approval",
            "climate": _climate_block(pkg),
            "overlay_active": bool(pkg.overlay_active),
            "overlay_pair": pkg.overlay_pair,
            "review_ready": True,
            "drafts_ready": True,
            "checklist_ready": True,
            "approval_status": "pending",
            "publish_status": "not_started",
            "notes": "",
            "outputs": outputs,
            "package": pkg.to_dict(),
        }
        _write_state(state_path, payload)

        files_written = [
            review_md,
            post_name,
            reel_name,
            checklist_name,
            state_name,
        ]
        if review_json:
            files_written.insert(1, review_json)
        if support_name:
            files_written.insert(-2, support_name)

        return WeeklyAgentResult(
            week_start=week_start,
            week_end=week_end,
            out_dir=out_dir,
            state_path=state_path,
            state=payload,
            files_written=files_written,
            error=None,
        )
    except Exception as exc:  # noqa: BLE001 — agent boundary records failure to state
        return _fail_state(exc)


def _console_safe_line(text: str) -> str:
    """Avoid ``UnicodeEncodeError`` on Windows cp1252 consoles when titles contain Cyrillic."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(enc, errors="replace").decode(enc, errors="replace")


def print_agent_summary(result: WeeklyAgentResult) -> None:
    """Print a single clean terminal block for operators."""
    st = result.state
    climate = st.get("climate") or {}
    sign = climate.get("venus_sign", "—")
    title = (climate.get("climate_title") or "")[:72]
    overlay_on = st.get("overlay_active")
    pair = st.get("overlay_pair") or "—"
    print()
    print("=" * 60)
    print("VENUS WEEKLY AGENT — run summary")
    print("=" * 60)
    print(_console_safe_line(f"  Week:        {result.week_start} -> {result.week_end}"))
    print(_console_safe_line(f"  Climate:     {sign} — {title}"))
    print(_console_safe_line(f"  Overlay:     active={overlay_on}  pair={pair}"))
    print(_console_safe_line(f"  Output dir:  {result.out_dir}"))
    print(_console_safe_line(f"  State file:  {result.state_path.name}"))
    print(_console_safe_line(f"  Final state: {st.get('status')}"))
    if result.error:
        print(_console_safe_line(f"  Error:       {result.error}"))
    print("  Files created:")
    for name in result.files_written:
        print(_console_safe_line(f"    - {name}"))
    print("=" * 60)
    print()
