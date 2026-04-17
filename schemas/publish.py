from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PublishRequest(BaseModel):
    instagram_account_id: str


class SchedulePublishRequest(BaseModel):
    instagram_account_id: str
    scheduled_for: datetime


class PublishJobResponse(BaseModel):
    id: str
    instagram_account_id: str
    draft_id: str
    status: str
    attempts: int
    scheduled_for: datetime | None
    external_container_id: str | None
    external_publish_id: str | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, job: Any) -> "PublishJobResponse":
        return cls(
            id=job.id,
            instagram_account_id=job.instagram_account_id,
            draft_id=job.draft_id,
            status=job.status,
            attempts=job.attempts,
            scheduled_for=job.scheduled_for,
            external_container_id=job.external_container_id,
            external_publish_id=job.external_publish_id,
            last_error=job.last_error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


class PublishedPostResponse(BaseModel):
    id: str
    publish_job_id: str
    instagram_account_id: str
    draft_id: str
    ig_media_id: str | None
    ig_permalink: str | None
    published_at: datetime | None
    payload: dict[str, Any] | None

    @classmethod
    def from_orm_model(cls, post: Any) -> "PublishedPostResponse":
        return cls(
            id=post.id,
            publish_job_id=post.publish_job_id,
            instagram_account_id=post.instagram_account_id,
            draft_id=post.draft_id,
            ig_media_id=post.ig_media_id,
            ig_permalink=post.ig_permalink,
            published_at=post.published_at,
            payload=post.payload,
        )


class PublishResponse(BaseModel):
    publish_job: PublishJobResponse
    published_post: PublishedPostResponse | None
    succeeded: bool
    error: str | None = None


class PublishJobListResponse(BaseModel):
    items: list[PublishJobResponse]
    total: int


class PublishedPostListResponse(BaseModel):
    items: list[PublishedPostResponse]
    total: int
