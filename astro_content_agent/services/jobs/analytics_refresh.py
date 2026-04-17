from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from astro_content_agent.repositories.published_posts import PublishedPostRepository

logger = logging.getLogger(__name__)


def run_analytics_refresh(
    *,
    db_factory: Callable[[], Session],
    lookback_days: int = 7,
) -> None:
    """Refresh analytics for recently published posts.

    Phase 6 stub — iterates over recent posts and logs what would be fetched.
    Replace the inner loop body with a real Meta Insights API call in Phase 7+.
    """
    db = db_factory()
    try:
        repo = PublishedPostRepository()
        posts = repo.list_posts(db, limit=200)

        cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
        eligible = [p for p in posts if p.published_at and p.published_at >= cutoff]

        logger.info("analytics_refresh: found %d post(s) in last %d day(s)", len(eligible), lookback_days)

        for post in eligible:
            # Extension point: call Meta Insights API here in a future phase.
            logger.debug("analytics_refresh: would refresh ig_media_id=%s post_id=%s", post.ig_media_id, post.id)

        logger.info("analytics_refresh: complete")
    except Exception:
        logger.exception("analytics_refresh: unhandled error")
    finally:
        db.close()
