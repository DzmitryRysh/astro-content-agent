from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import PublishJob


class PublishJobRepository:
    def create(
        self,
        db: Session,
        *,
        instagram_account_id: str,
        draft_id: str,
        scheduled_for: datetime | None = None,
    ) -> PublishJob:
        job = PublishJob(
            instagram_account_id=instagram_account_id,
            draft_id=draft_id,
            status="queued",
            scheduled_for=scheduled_for,
            attempts=0,
        )
        db.add(job)
        return job

    def get_by_id(self, db: Session, job_id: str) -> PublishJob | None:
        return db.get(PublishJob, job_id)

    def list_jobs(
        self,
        db: Session,
        *,
        status: str | None = None,
        instagram_account_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PublishJob]:
        stmt = select(PublishJob)
        if status is not None:
            stmt = stmt.where(PublishJob.status == status)
        if instagram_account_id is not None:
            stmt = stmt.where(PublishJob.instagram_account_id == instagram_account_id)
        stmt = stmt.order_by(PublishJob.created_at.desc()).limit(limit).offset(offset)
        return list(db.execute(stmt).scalars().all())

    def mark_running(self, db: Session, job: PublishJob) -> PublishJob:
        job.status = "running"
        job.attempts += 1
        db.add(job)
        return job

    def mark_succeeded(
        self,
        db: Session,
        job: PublishJob,
        *,
        external_publish_id: str,
    ) -> PublishJob:
        job.status = "succeeded"
        job.external_publish_id = external_publish_id
        job.last_error = None
        db.add(job)
        return job

    def mark_failed(
        self,
        db: Session,
        job: PublishJob,
        *,
        error: str,
        max_attempts: int = 3,
    ) -> PublishJob:
        job.last_error = error
        # Retry if under the attempt ceiling; otherwise permanently fail.
        job.status = "queued" if job.attempts < max_attempts else "failed"
        db.add(job)
        return job

    def list_eligible_for_run(self, db: Session, now: datetime) -> list[PublishJob]:
        """Return queued jobs whose scheduled_for has passed (or was never set)."""
        from sqlalchemy import or_

        stmt = (
            select(PublishJob)
            .where(PublishJob.status == "queued")
            .where(
                or_(
                    PublishJob.scheduled_for.is_(None),
                    PublishJob.scheduled_for <= now,
                )
            )
            .order_by(PublishJob.created_at.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def store_container_id(
        self,
        db: Session,
        job: PublishJob,
        *,
        container_id: str,
    ) -> PublishJob:
        job.external_container_id = container_id
        db.add(job)
        return job
