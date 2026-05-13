from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from astro_content_agent.db.models import Draft, InstagramAccount, PublishJob, PublishedPost
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.repositories.publish_jobs import PublishJobRepository
from astro_content_agent.repositories.published_posts import PublishedPostRepository
from astro_content_agent.services.instagram.client import InstagramClientProtocol, MetaAPIError
from astro_content_agent.services.instagram.container_builder import ContainerBuilder
from astro_content_agent.services.media.storage import StorageBackend

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

# Instagram returns 400 / code=9007 / subcode=2207027 when media_publish runs before the
# container is ready ("Media ID is not available"). Retry media_publish with bounded backoff.
META_MEDIA_NOT_READY_CODE = 9007
META_MEDIA_NOT_READY_SUBCODE = 2207027
MEDIA_PUBLISH_MAX_ATTEMPTS = 5
MEDIA_PUBLISH_NOT_READY_BACKOFF_SEC = 5.0


def _is_meta_media_not_ready_error(exc: BaseException) -> bool:
    if not isinstance(exc, MetaAPIError):
        return False
    if exc.meta_error_code != META_MEDIA_NOT_READY_CODE:
        return False
    try:
        sub = int(exc.meta_error_subcode) if exc.meta_error_subcode is not None else None
    except (TypeError, ValueError):
        return False
    return sub == META_MEDIA_NOT_READY_SUBCODE


@dataclass(frozen=True)
class PublishResult:
    publish_job: PublishJob
    published_post: PublishedPost | None
    succeeded: bool
    error: str | None = None
    meta_error: dict | None = None
    # How many ``publish_container`` calls were made in this ``execute_job`` (includes retries).
    media_publish_attempts: int | None = None


@dataclass(frozen=True)
class _Deps:
    draft_repo: DraftRepository
    asset_repo: AssetRepository
    job_repo: PublishJobRepository
    post_repo: PublishedPostRepository
    container_builder: ContainerBuilder


class PublisherService:
    """Orchestrates the full Instagram publish flow.

    Design:
    - Only approved image-post drafts may be published.
    - The external_container_id is persisted after step 1 so that a retry
      can skip container creation and go straight to publish.
    - Draft status is never modified by this service; only publish_job
      and published_post records change.
    - On failure: job is marked queued (retryable) until MAX_ATTEMPTS,
      then permanently failed.
    """

    class DraftNotApprovedError(ValueError):
        pass

    class DraftNotFoundError(ValueError):
        pass

    class AccountNotFoundError(ValueError):
        pass

    class UnsupportedDraftTypeError(ValueError):
        pass

    def __init__(
        self,
        *,
        ig_client: InstagramClientProtocol,
        storage: StorageBackend | None = None,
        deps: _Deps | None = None,
    ) -> None:
        self._client = ig_client
        # Build url_resolver from storage if provided; otherwise identity (key passes through).
        url_resolver = storage.url if storage is not None else None
        self._deps = deps or _Deps(
            draft_repo=DraftRepository(),
            asset_repo=AssetRepository(),
            job_repo=PublishJobRepository(),
            post_repo=PublishedPostRepository(),
            container_builder=ContainerBuilder(url_resolver=url_resolver),
        )

    def _publish_container_with_not_ready_retries(
        self,
        *,
        ig_user_id: str,
        container_id: str,
    ) -> tuple[str, int]:
        """Call ``publish_container``; retry on Meta *container not ready* (9007 / 2207027)."""
        last_exc: MetaAPIError | None = None
        for attempt in range(1, MEDIA_PUBLISH_MAX_ATTEMPTS + 1):
            try:
                ig_media_id = self._client.publish_container(
                    ig_user_id=ig_user_id,
                    container_id=container_id,
                )
                return ig_media_id, attempt
            except MetaAPIError as e:
                last_exc = e
                if _is_meta_media_not_ready_error(e) and attempt < MEDIA_PUBLISH_MAX_ATTEMPTS:
                    logger.warning(
                        "IG media_publish not ready (code=%s subcode=%s); sleeping %.1fs before retry %s/%s",
                        e.meta_error_code,
                        e.meta_error_subcode,
                        MEDIA_PUBLISH_NOT_READY_BACKOFF_SEC,
                        attempt + 1,
                        MEDIA_PUBLISH_MAX_ATTEMPTS,
                    )
                    time.sleep(MEDIA_PUBLISH_NOT_READY_BACKOFF_SEC)
                    continue
                raise
        raise AssertionError("unreachable") from last_exc

    def create_job(
        self,
        db: Session,
        *,
        draft_id: str,
        instagram_account_id: str,
        scheduled_for: datetime | None = None,
    ) -> PublishJob:
        """Validate draft eligibility and create a publish job."""
        draft = self._deps.draft_repo.get_by_id(db, draft_id)
        if draft is None:
            raise self.DraftNotFoundError(f"draft not found: {draft_id}")
        if draft.status != "approved":
            raise self.DraftNotApprovedError(
                f"draft must be approved before publishing (current status: '{draft.status}')"
            )
        account = db.get(InstagramAccount, instagram_account_id)
        if account is None:
            raise self.AccountNotFoundError(f"instagram_account not found: {instagram_account_id}")

        job = self._deps.job_repo.create(
            db,
            instagram_account_id=instagram_account_id,
            draft_id=draft_id,
            scheduled_for=scheduled_for,
        )
        db.commit()
        db.refresh(job)
        return job

    def execute_job(self, db: Session, *, job_id: str) -> PublishResult:
        """Run a queued publish job synchronously.

        Retry-safe: if a container_id was already stored from a prior
        attempt, the container creation step is skipped.
        """
        job = self._deps.job_repo.get_by_id(db, job_id)
        if job is None:
            raise ValueError(f"publish_job not found: {job_id}")

        account = db.get(InstagramAccount, job.instagram_account_id)

        self._deps.job_repo.mark_running(db, job)
        db.commit()

        try:
            if account is None:
                raise ValueError(f"instagram account not found: {job.instagram_account_id}")
            if not account.ig_user_id:
                raise ValueError(
                    "Instagram account has no ig_user_id — Meta Graph API cannot create media. "
                    "Set instagram_accounts.ig_user_id (numeric id from Meta). "
                    "Dry-run: POST /api/v1/publish/<draft_id>/dry-run or GET /api/v1/admin/publish-readiness/<draft_id>."
                )

            draft = self._deps.draft_repo.get_by_id(db, job.draft_id)
            # Step 1: create media container (skip if already done on a prior attempt)
            container_id = job.external_container_id
            if container_id is None:
                assets = self._deps.asset_repo.list_for_draft(db, job.draft_id)
                if not assets:
                    raise ValueError("no assets found for draft; generate an image first")
                asset = assets[0]
                params = self._deps.container_builder.build(draft=draft, asset=asset)
                container_id = self._client.create_image_container(
                    ig_user_id=account.ig_user_id,
                    image_url=params.image_url,
                    caption=params.caption,
                )
                self._deps.job_repo.store_container_id(db, job, container_id=container_id)
                db.commit()

            # Step 2: publish the container (retry if Meta reports container not ready yet)
            ig_media_id, media_publish_attempts = self._publish_container_with_not_ready_retries(
                ig_user_id=account.ig_user_id,
                container_id=container_id,
            )

            # Step 3: record the published post
            published_post = self._deps.post_repo.create(
                db,
                publish_job_id=job.id,
                instagram_account_id=job.instagram_account_id,
                draft_id=job.draft_id,
                ig_media_id=ig_media_id,
                payload={"container_id": container_id},
            )
            self._deps.job_repo.mark_succeeded(db, job, external_publish_id=ig_media_id)
            db.commit()
            db.refresh(job)
            db.refresh(published_post)
            logger.info("Published draft=%s ig_media_id=%s", job.draft_id, ig_media_id)
            return PublishResult(
                publish_job=job,
                published_post=published_post,
                succeeded=True,
                media_publish_attempts=media_publish_attempts,
            )

        except Exception as exc:
            error_msg = str(exc)
            logger.error("Publish failed job=%s attempt=%s error=%s", job.id, job.attempts, error_msg)
            self._deps.job_repo.mark_failed(db, job, error=error_msg, max_attempts=MAX_ATTEMPTS)
            db.commit()
            db.refresh(job)
            meta_payload = None
            media_publish_attempts: int | None = None
            if isinstance(exc, MetaAPIError):
                meta_payload = {
                    "meta_status_code": exc.status_code,
                    "meta_error_body": exc.response_text,
                    "meta_error_json": exc.response_json,
                    "meta_error_code": exc.meta_error_code,
                    "meta_error_subcode": exc.meta_error_subcode,
                    "meta_error_type": exc.meta_error_type,
                    "meta_error_message": exc.meta_error_message,
                    "meta_url": exc.url,
                }
                if _is_meta_media_not_ready_error(exc):
                    media_publish_attempts = MEDIA_PUBLISH_MAX_ATTEMPTS
            return PublishResult(
                publish_job=job,
                published_post=None,
                succeeded=False,
                error=error_msg,
                meta_error=meta_payload,
                media_publish_attempts=media_publish_attempts,
            )
