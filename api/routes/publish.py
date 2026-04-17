from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from astro_content_agent.db.session import get_db
from astro_content_agent.repositories.publish_jobs import PublishJobRepository
from astro_content_agent.repositories.published_posts import PublishedPostRepository
from astro_content_agent.schemas.publish import (
    PublishJobListResponse,
    PublishJobResponse,
    PublishRequest,
    PublishResponse,
    PublishedPostListResponse,
    PublishedPostResponse,
    SchedulePublishRequest,
)
from astro_content_agent.services.instagram.client import InstagramClientProtocol
from astro_content_agent.services.instagram.publisher import PublisherService
from astro_content_agent.services.media.storage import LocalFileStorage
from astro_content_agent.services.media.url_builder import get_local_storage
from astro_content_agent.core.config import Settings, get_settings

router = APIRouter()


def get_ig_client(
    settings: Settings = Depends(get_settings),
) -> InstagramClientProtocol:
    """Return a configured Instagram client.

    Wired from ``INSTAGRAM_ACCESS_TOKEN`` in .env for real publishing.
    Override via ``app.dependency_overrides[get_ig_client]`` in tests.

    Raises 503 with an actionable message when the token is not configured,
    rather than a raw 500, so the error is easy to diagnose locally.
    """
    from astro_content_agent.services.instagram.client import MetaInstagramClient

    token = settings.instagram_access_token
    if not token:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=(
                "Instagram publishing is not configured. "
                "Set INSTAGRAM_ACCESS_TOKEN in .env and restart the server."
            ),
        )
    return MetaInstagramClient(access_token=token)


def get_storage() -> LocalFileStorage:
    """FastAPI dependency: returns a LocalFileStorage configured from app settings."""
    return get_local_storage(get_settings())


@router.post("/{draft_id}", response_model=PublishResponse)
def publish_now(
    draft_id: str,
    body: PublishRequest,
    db: Session = Depends(get_db),
    ig_client: InstagramClientProtocol = Depends(get_ig_client),
    storage: LocalFileStorage = Depends(get_storage),
) -> PublishResponse:
    """Create a publish job and execute it immediately (synchronous in Phase 5/8)."""
    svc = PublisherService(ig_client=ig_client, storage=storage)
    try:
        job = svc.create_job(
            db,
            draft_id=draft_id,
            instagram_account_id=body.instagram_account_id,
        )
    except PublisherService.DraftNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PublisherService.AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PublisherService.DraftNotApprovedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    result = svc.execute_job(db, job_id=job.id)
    published_post_resp: PublishedPostResponse | None = None
    if result.published_post is not None:
        published_post_resp = PublishedPostResponse.from_orm_model(result.published_post)

    return PublishResponse(
        publish_job=PublishJobResponse.from_orm_model(result.publish_job),
        published_post=published_post_resp,
        succeeded=result.succeeded,
        error=result.error,
    )


@router.post("/{draft_id}/schedule", response_model=PublishJobResponse)
def schedule_publish(
    draft_id: str,
    body: SchedulePublishRequest,
    db: Session = Depends(get_db),
    ig_client: InstagramClientProtocol = Depends(get_ig_client),
    storage: LocalFileStorage = Depends(get_storage),
) -> PublishJobResponse:
    """Create a queued publish job to be executed later by the scheduler."""
    svc = PublisherService(ig_client=ig_client, storage=storage)
    try:
        job = svc.create_job(
            db,
            draft_id=draft_id,
            instagram_account_id=body.instagram_account_id,
            scheduled_for=body.scheduled_for,
        )
    except PublisherService.DraftNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PublisherService.AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PublisherService.DraftNotApprovedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    return PublishJobResponse.from_orm_model(job)


@router.get("/jobs", response_model=PublishJobListResponse)
def list_jobs(
    status: str | None = Query(default=None),
    instagram_account_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PublishJobListResponse:
    repo = PublishJobRepository()
    jobs = repo.list_jobs(
        db,
        status=status,
        instagram_account_id=instagram_account_id,
        limit=limit,
        offset=offset,
    )
    return PublishJobListResponse(
        items=[PublishJobResponse.from_orm_model(j) for j in jobs],
        total=len(jobs),
    )


@router.get("/history", response_model=PublishedPostListResponse)
def publish_history(
    instagram_account_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PublishedPostListResponse:
    repo = PublishedPostRepository()
    posts = repo.list_posts(db, instagram_account_id=instagram_account_id, limit=limit, offset=offset)
    return PublishedPostListResponse(
        items=[PublishedPostResponse.from_orm_model(p) for p in posts],
        total=len(posts),
    )
