from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from astro_content_agent.db.models import Draft
from astro_content_agent.repositories.drafts import DraftRepository


@dataclass(frozen=True)
class _Deps:
    drafts_repo: DraftRepository


class DraftApprovalService:
    """Manages approval/rejection state transitions for drafts.

    Valid transitions:
    - draft  -> approved
    - draft  -> rejected
    Approved and rejected drafts are immutable; regenerate to create a new draft.
    """

    class DraftNotFoundError(ValueError):
        pass

    class InvalidStatusTransitionError(ValueError):
        pass

    def __init__(self, deps: _Deps | None = None) -> None:
        self._deps = deps or _Deps(drafts_repo=DraftRepository())

    def get_or_404(self, db: Session, draft_id: str) -> Draft:
        draft = self._deps.drafts_repo.get_by_id(db, draft_id)
        if draft is None:
            raise self.DraftNotFoundError(f"draft not found: {draft_id}")
        return draft

    def approve(self, db: Session, draft_id: str) -> Draft:
        draft = self.get_or_404(db, draft_id)
        if draft.status != "draft":
            raise self.InvalidStatusTransitionError(
                f"cannot approve draft with status '{draft.status}'"
            )
        self._deps.drafts_repo.approve(db, draft)
        db.commit()
        db.refresh(draft)
        return draft

    def reject(self, db: Session, draft_id: str, *, reason: str) -> Draft:
        draft = self.get_or_404(db, draft_id)
        if draft.status != "draft":
            raise self.InvalidStatusTransitionError(
                f"cannot reject draft with status '{draft.status}'"
            )
        self._deps.drafts_repo.reject(db, draft, reason=reason)
        db.commit()
        db.refresh(draft)
        return draft
