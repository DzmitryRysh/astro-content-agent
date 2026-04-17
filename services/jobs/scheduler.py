from __future__ import annotations

import logging
from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from astro_content_agent.core.config import Settings
from astro_content_agent.services.instagram.client import InstagramClientProtocol
from astro_content_agent.services.instagram.client import MetaInstagramClient

logger = logging.getLogger(__name__)


class SchedulerService:
    """Wraps APScheduler and registers all recurring jobs.

    All job functions are injected with their dependencies at registration
    time so they remain independently testable outside the scheduler.
    """

    def __init__(self, scheduler: BackgroundScheduler) -> None:
        self._scheduler = scheduler

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("scheduler: started")

    def shutdown(self, *, wait: bool = False) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("scheduler: stopped")

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def get_jobs(self) -> list:
        return self._scheduler.get_jobs()


def build_scheduler(
    settings: Settings,
    db_factory: Callable[[], Session],
    ig_client_factory: Callable[[str], InstagramClientProtocol] | None = None,
) -> SchedulerService:
    """Build and register all jobs. Does not start the scheduler."""
    from astro_content_agent.services.jobs.analytics_refresh import run_analytics_refresh
    from astro_content_agent.services.jobs.daily_generation import run_daily_generation
    from astro_content_agent.services.jobs.publish_queue import run_publish_queue

    tz = settings.scheduler_timezone

    # Default IG client factory: create real MetaInstagramClient per access token.
    def _default_ig_factory(access_token: str) -> InstagramClientProtocol:
        return MetaInstagramClient(access_token=access_token)

    resolved_ig_factory = ig_client_factory or _default_ig_factory

    # Storage factory: provides LocalFileStorage for URL resolution during publish.
    def _get_storage():
        from pathlib import Path
        from astro_content_agent.services.media.storage import LocalFileStorage

        return LocalFileStorage(
            assets_dir=Path(settings.assets_dir),
            public_base_url=settings.public_base_url,
        )

    # Lazy runner: created once on first job run to avoid startup errors when
    # OPENAI_API_KEY is not set yet (e.g. local dev without a key).
    _runner_cache: list = []

    def _get_runner():
        if not _runner_cache:
            from astro_content_agent.services.ai.responses_runner import ResponsesRunner

            _runner_cache.append(ResponsesRunner.from_settings())
        return _runner_cache[0]

    scheduler = BackgroundScheduler(timezone=tz)

    # Daily generation: cron at configured hour
    scheduler.add_job(
        lambda: run_daily_generation(db_factory=db_factory, runner=_get_runner()),
        CronTrigger(hour=settings.daily_generation_hour, timezone=tz),
        id="daily_generation",
        replace_existing=True,
        name="Daily content generation",
    )

    # Publish queue: interval every N minutes
    scheduler.add_job(
        lambda: run_publish_queue(
            db_factory=db_factory,
            ig_client_factory=resolved_ig_factory,
            storage_factory=_get_storage,
        ),
        IntervalTrigger(minutes=settings.publish_queue_interval_minutes),
        id="publish_queue",
        replace_existing=True,
        name="Publish queue processor",
    )

    # Analytics refresh: cron at configured hour
    scheduler.add_job(
        lambda: run_analytics_refresh(db_factory=db_factory),
        CronTrigger(hour=settings.analytics_refresh_hour, timezone=tz),
        id="analytics_refresh",
        replace_existing=True,
        name="Analytics refresh",
    )

    return SchedulerService(scheduler)
