from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from astro_content_agent.core.config import Settings
from astro_content_agent.db.models import InstagramAccount
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.repositories.publish_jobs import PublishJobRepository
from astro_content_agent.services.ai.responses_runner import ResponsesRunner
from astro_content_agent.services.instagram.publisher import PublisherService
from astro_content_agent.services.jobs.analytics_refresh import run_analytics_refresh
from astro_content_agent.services.jobs.daily_generation import run_daily_generation
from astro_content_agent.services.jobs.publish_queue import run_publish_queue
from astro_content_agent.services.jobs.scheduler import SchedulerService, build_scheduler
from astro_content_agent.tests.fakes.fake_instagram import FakeInstagramClient
from astro_content_agent.tests.fakes.fake_openai import FakeOpenAIClient, default_responder

from datetime import date


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _ai_runner() -> ResponsesRunner:
    prompts_root = Path(__file__).resolve().parents[1] / "services" / "ai" / "prompts"
    return ResponsesRunner(model="test", client=FakeOpenAIClient(default_responder), prompts_root=prompts_root)


def _make_account(db: Session) -> InstagramAccount:
    acc = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="Scheduler Test Account",
        ig_user_id="ig-sched-123",
        access_token="fake-token",
        is_active=1,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


def _make_approved_draft(db: Session, brand_profile_id: str) -> object:
    from astro_content_agent.tests.test_phase5_publish import _make_approved_draft as _apd
    return _apd(db, brand_profile_id)


def _make_asset(db: Session, draft) -> object:
    from astro_content_agent.tests.test_phase5_publish import _make_asset as _ma
    return _ma(db, draft)


# ---------------------------------------------------------------------------
# Scheduler registration
# ---------------------------------------------------------------------------


def test_build_scheduler_registers_three_jobs(db_session: Session) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        SCHEDULER_ENABLED=False,
        DATABASE_URL="sqlite:///:memory:",
    )
    svc = build_scheduler(settings=settings, db_factory=lambda: db_session)
    jobs = svc.get_jobs()
    job_ids = {j.id for j in jobs}
    assert "daily_generation" in job_ids
    assert "publish_queue" in job_ids
    assert "analytics_refresh" in job_ids


def test_scheduler_service_not_running_before_start(db_session: Session) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        SCHEDULER_ENABLED=False,
        DATABASE_URL="sqlite:///:memory:",
    )
    svc = build_scheduler(settings=settings, db_factory=lambda: db_session)
    assert svc.running is False


# ---------------------------------------------------------------------------
# Daily generation job
# ---------------------------------------------------------------------------


def test_daily_generation_creates_plan_and_drafts(db_session: Session, brand_profile) -> None:
    runner = _ai_runner()
    counts = run_daily_generation(
        db_factory=lambda: db_session,
        runner=runner,
        day=date(2026, 4, 3),
    )
    assert counts["brands_processed"] == 1
    assert counts["plans_created"] == 1
    assert counts["drafts_created"] >= 1
    assert counts["errors"] == 0


def test_daily_generation_is_idempotent(db_session: Session, brand_profile) -> None:
    runner = _ai_runner()
    day = date(2026, 4, 3)

    # First run
    counts1 = run_daily_generation(db_factory=lambda: db_session, runner=runner, day=day)
    # Second run (same day, same brand)
    counts2 = run_daily_generation(db_factory=lambda: db_session, runner=runner, day=day)

    assert counts1["plans_created"] == 1
    assert counts2["plans_created"] == 0
    assert counts2["plans_skipped"] == 1
    assert counts2["drafts_created"] == 0


def test_daily_generation_no_brands_is_harmless(db_session: Session) -> None:
    runner = _ai_runner()
    counts = run_daily_generation(
        db_factory=lambda: db_session,
        runner=runner,
        day=date(2026, 4, 3),
    )
    assert counts["brands_processed"] == 0
    assert counts["plans_created"] == 0
    assert counts["errors"] == 0


# ---------------------------------------------------------------------------
# Publish queue job
# ---------------------------------------------------------------------------


def test_publish_queue_processes_eligible_job(db_session: Session, brand_profile) -> None:
    ig_client = FakeInstagramClient()
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    svc = PublisherService(ig_client=ig_client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)

    counts = run_publish_queue(
        db_factory=lambda: db_session,
        ig_client_factory=lambda token: ig_client,
    )
    assert counts["processed"] == 1
    assert counts["succeeded"] == 1


def test_publish_queue_skips_future_scheduled_jobs(db_session: Session, brand_profile) -> None:
    ig_client = FakeInstagramClient()
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)

    svc = PublisherService(ig_client=ig_client)
    future = datetime.now(UTC) + timedelta(hours=2)
    svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id, scheduled_for=future)

    # Run queue with "now" set to before the scheduled time
    counts = run_publish_queue(
        db_factory=lambda: db_session,
        ig_client_factory=lambda token: ig_client,
        now=datetime.now(UTC),  # current time is before the scheduled future time
    )
    assert counts["processed"] == 0


def test_publish_queue_handles_failed_job_gracefully(db_session: Session, brand_profile) -> None:
    failing_client = FakeInstagramClient(fail_on_publish=True)
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    svc = PublisherService(ig_client=failing_client)
    svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)

    counts = run_publish_queue(
        db_factory=lambda: db_session,
        ig_client_factory=lambda token: failing_client,
    )
    assert counts["processed"] == 1
    assert counts["failed"] == 1
    assert counts["succeeded"] == 0


def test_publish_queue_skips_account_without_token(db_session: Session, brand_profile) -> None:
    ig_client = FakeInstagramClient()
    draft = _make_approved_draft(db_session, brand_profile.id)

    # Account with no token
    account = InstagramAccount(
        id=str(uuid.uuid4()),
        account_name="No Token Account",
        ig_user_id="ig-no-token",
        access_token=None,
        is_active=1,
    )
    db_session.add(account)
    db_session.commit()

    svc = PublisherService(ig_client=ig_client)
    svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)

    counts = run_publish_queue(
        db_factory=lambda: db_session,
        ig_client_factory=lambda token: ig_client,
    )
    assert counts["skipped"] == 1
    assert counts["processed"] == 0


# ---------------------------------------------------------------------------
# Analytics refresh job
# ---------------------------------------------------------------------------


def test_analytics_refresh_runs_without_error(db_session: Session) -> None:
    # No published posts — should complete silently
    run_analytics_refresh(db_factory=lambda: db_session, lookback_days=7)


def test_analytics_refresh_with_published_posts(db_session: Session, brand_profile) -> None:
    ig_client = FakeInstagramClient()
    draft = _make_approved_draft(db_session, brand_profile.id)
    account = _make_account(db_session)
    _make_asset(db_session, draft)

    svc = PublisherService(ig_client=ig_client)
    job = svc.create_job(db_session, draft_id=draft.id, instagram_account_id=account.id)
    svc.execute_job(db_session, job_id=job.id)

    # Should iterate over the published post without raising
    run_analytics_refresh(db_factory=lambda: db_session, lookback_days=7)
