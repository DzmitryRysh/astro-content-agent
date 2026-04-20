from __future__ import annotations

from sqlalchemy.orm import Session

from astro_content_agent.core.config import Settings
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.schemas.drafts import (
    DraftOperatorReview,
    OperatorReviewActionLinks,
    PostDraftPayload,
    ReelDraftPayload,
)
from astro_content_agent.services.diagnostics.checker import DiagnosticsService
from astro_content_agent.services.media.url_builder import get_local_storage


def build_draft_operator_review(
    db: Session,
    *,
    draft_id: str,
    settings: Settings,
    instagram_account_id: str | None = None,
) -> DraftOperatorReview | None:
    """Assemble operator-facing review payload with publish readiness and dry-run preview."""
    repo = DraftRepository()
    draft = repo.get_by_id(db, draft_id)
    if draft is None:
        return None

    title = hook = caption = cta = None
    hashtags: list[str] = []
    if draft.draft_type == "post":
        try:
            p = PostDraftPayload.model_validate(draft.payload or {})
            title = p.title
            hook = p.hook
            caption = p.caption
            cta = p.cta
            hashtags = list(p.hashtags[:16])
        except Exception:
            pass
    elif draft.draft_type == "reel":
        try:
            r = ReelDraftPayload.model_validate(draft.payload or {})
            hook = r.hook or r.hook_0_3s
            script = r.script or ""
            caption = script if len(script) <= 2000 else script[:1997] + "..."
            cta = r.cta
        except Exception:
            pass

    assets = AssetRepository().list_for_draft(db, draft_id)
    storage = get_local_storage(settings)
    primary_key = assets[0].storage_path if assets else None
    primary_url = storage.url(primary_key) if primary_key else None

    diag = DiagnosticsService()
    readiness = diag.run_publish_readiness(
        db,
        draft_id=draft_id,
        settings=settings,
        instagram_account_id=instagram_account_id,
        include_simulation=True,
    )

    actions = OperatorReviewActionLinks(
        approve=f"/api/v1/drafts/{draft_id}/approve",
        reject=f"/api/v1/drafts/{draft_id}/reject",
        publish_dry_run=f"/api/v1/publish/{draft_id}/dry-run",
        admin_publish_readiness=f"/api/v1/admin/publish-readiness/{draft_id}",
    )

    return DraftOperatorReview(
        draft_id=draft.id,
        brand_profile_id=draft.brand_profile_id,
        draft_type=draft.draft_type,
        status=draft.status,
        title=title,
        hook=hook,
        caption=caption,
        cta=cta,
        hashtags_preview=hashtags,
        text_fallback=draft.text,
        primary_asset_storage_key=primary_key,
        primary_image_public_url=primary_url,
        approved_at=draft.approved_at,
        rejected_at=draft.rejected_at,
        rejection_reason=draft.rejection_reason,
        publish_readiness_ready=readiness.ready,
        publish_readiness_checks=list(readiness.checks),
        dry_run=readiness.simulation,
        actions=actions,
    )
