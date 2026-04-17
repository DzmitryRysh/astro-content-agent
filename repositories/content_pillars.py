from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import ContentPillar


class ContentPillarRepository:
    def list_for_brand(self, db: Session, brand_profile_id: str) -> list[ContentPillar]:
        stmt = (
            select(ContentPillar)
            .where(ContentPillar.brand_profile_id == brand_profile_id)
            .order_by(ContentPillar.created_at.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def create(
        self,
        db: Session,
        *,
        brand_profile_id: str,
        name: str,
        description: str | None = None,
    ) -> ContentPillar:
        cp = ContentPillar(
            brand_profile_id=brand_profile_id,
            name=name,
            description=description,
        )
        db.add(cp)
        return cp

    def delete_for_brand(self, db: Session, brand_profile_id: str) -> int:
        """Delete all pillars for a brand. Returns the count deleted."""
        stmt = delete(ContentPillar).where(ContentPillar.brand_profile_id == brand_profile_id)
        result = db.execute(stmt)
        return result.rowcount
