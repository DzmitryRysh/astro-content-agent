from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import Draft


class DraftRepository:
    def create(
        self,
        db: Session,
        *,
        brand_profile_id: str,
        content_plan_id: str | None,
        draft_type: str,
        text: str | None,
        payload: dict | None,
    ) -> Draft:
        rec = Draft(
            brand_profile_id=brand_profile_id,
            content_plan_id=content_plan_id,
            draft_type=draft_type,
            status="draft",
            text=text,
            payload=payload,
        )
        db.add(rec)
        return rec

    def get_by_id(self, db: Session, draft_id: str) -> Draft | None:
        return db.get(Draft, draft_id)

    def list_drafts(
        self,
        db: Session,
        *,
        brand_profile_id: str | None = None,
        status: str | None = None,
        draft_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Draft]:
        stmt = select(Draft)
        if brand_profile_id is not None:
            stmt = stmt.where(Draft.brand_profile_id == brand_profile_id)
        if status is not None:
            stmt = stmt.where(Draft.status == status)
        if draft_type is not None:
            stmt = stmt.where(Draft.draft_type == draft_type)
        stmt = stmt.order_by(Draft.created_at.desc()).limit(limit).offset(offset)
        return list(db.execute(stmt).scalars().all())

    def approve(self, db: Session, draft: Draft) -> Draft:
        draft.status = "approved"
        draft.approved_at = datetime.now(UTC)
        db.add(draft)
        return draft

    def list_for_content_plan(self, db: Session, content_plan_id: str) -> list[Draft]:
        stmt = select(Draft).where(Draft.content_plan_id == content_plan_id)
        return list(db.execute(stmt).scalars().all())

    def reject(self, db: Session, draft: Draft, *, reason: str) -> Draft:
        draft.status = "rejected"
        draft.rejected_at = datetime.now(UTC)
        draft.rejection_reason = reason
        db.add(draft)
        return draft
