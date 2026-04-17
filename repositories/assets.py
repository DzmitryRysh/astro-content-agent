from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import Asset


class AssetRepository:
    def create(
        self,
        db: Session,
        *,
        brand_profile_id: str,
        draft_id: str | None,
        asset_type: str,
        storage_path: str,
        mime_type: str | None = None,
        width: int | None = None,
        height: int | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Asset:
        rec = Asset(
            brand_profile_id=brand_profile_id,
            draft_id=draft_id,
            asset_type=asset_type,
            storage_path=storage_path,
            mime_type=mime_type,
            width=width,
            height=height,
            meta=meta,
        )
        db.add(rec)
        return rec

    def list_for_draft(self, db: Session, draft_id: str) -> list[Asset]:
        stmt = select(Asset).where(Asset.draft_id == draft_id).order_by(Asset.created_at.desc())
        return list(db.execute(stmt).scalars().all())
