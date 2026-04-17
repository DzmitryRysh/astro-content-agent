from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from astro_content_agent.repositories.publish_jobs import PublishJobRepository
from astro_content_agent.services.instagram.client import InstagramClientProtocol
from astro_content_agent.services.instagram.publisher import PublisherService
from astro_content_agent.services.media.storage import StorageBackend

logger = logging.getLogger(__name__)


def run_publish_queue(
    *,
    db_factory: Callable[[], Session],
    ig_client_factory: Callable[[str], InstagramClientProtocol],
    storage_factory: Callable[[], StorageBackend] | None = None,
    now: datetime | None = None,
) -> dict[str, int]:
    """Process all queued publish jobs that are ready to run.

    Args:
        db_factory: Callable returning a new SQLAlchemy Session.
        ig_client_factory: Given an access_token string, returns an
            InstagramClientProtocol. Allows injection of fakes in tests.
        storage_factory: Optional callable returning a ``StorageBackend``
            instance.  When provided, the publisher uses it to resolve
            asset keys to public URLs.  Defaults to None (identity resolver).
        now: Override current time (for testing); defaults to UTC now.

    Returns:
        Counts dict with keys: processed, succeeded, failed, skipped.
    """
    effective_now = now or datetime.now(UTC)
    counts = {"processed": 0, "succeeded": 0, "failed": 0, "skipped": 0}

    db = db_factory()
    try:
        job_repo = PublishJobRepository()
        eligible = job_repo.list_eligible_for_run(db, effective_now)
        logger.info("publish_queue: %d eligible job(s)", len(eligible))

        for job in eligible:
            account = db.get(__import__("astro_content_agent.db.models", fromlist=["InstagramAccount"]).InstagramAccount, job.instagram_account_id)
            if account is None:
                logger.warning("publish_queue: account not found for job=%s — skipping", job.id)
                counts["skipped"] += 1
                continue

            if not account.access_token:
                logger.warning("publish_queue: no access_token on account=%s — skipping job=%s", account.id, job.id)
                counts["skipped"] += 1
                continue

            ig_client = ig_client_factory(account.access_token)
            storage = storage_factory() if storage_factory is not None else None
            svc = PublisherService(ig_client=ig_client, storage=storage)

            try:
                result = svc.execute_job(db, job_id=job.id)
                counts["processed"] += 1
                if result.succeeded:
                    counts["succeeded"] += 1
                    logger.info("publish_queue: job=%s succeeded ig_media_id=%s", job.id, result.published_post.ig_media_id if result.published_post else None)
                else:
                    counts["failed"] += 1
                    logger.warning("publish_queue: job=%s failed error=%s", job.id, result.error)
            except Exception:
                counts["processed"] += 1
                counts["failed"] += 1
                logger.exception("publish_queue: unhandled error for job=%s", job.id)

    except Exception:
        logger.exception("publish_queue: unhandled top-level error")
    finally:
        db.close()

    logger.info("publish_queue: done counts=%s", counts)
    return counts
