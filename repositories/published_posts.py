from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import PublishedPost


class PublishedPostRepository:
    def create(
        self,
        db: Session,
        *,
        publish_job_id: str,
        instagram_account_id: str,
        draft_id: str,
        ig_media_id: str,
        ig_permalink: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> PublishedPost:
        post = PublishedPost(
            publish_job_id=publish_job_id,
            instagram_account_id=instagram_account_id,
            draft_id=draft_id,
            ig_media_id=ig_media_id,
            ig_permalink=ig_permalink,
            published_at=datetime.now(UTC),
            payload=payload or {},
        )
        db.add(post)
        return post

    def list_posts(
        self,
        db: Session,
        *,
        instagram_account_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PublishedPost]:
        stmt = select(PublishedPost)
        if instagram_account_id is not None:
            stmt = stmt.where(PublishedPost.instagram_account_id == instagram_account_id)
        stmt = stmt.order_by(PublishedPost.published_at.desc()).limit(limit).offset(offset)
        return list(db.execute(stmt).scalars().all())
