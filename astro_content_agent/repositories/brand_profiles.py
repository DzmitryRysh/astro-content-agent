from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import BrandProfile


class BrandProfileRepository:
    def get(self, db: Session, brand_profile_id: str) -> BrandProfile | None:
        return db.get(BrandProfile, brand_profile_id)

    def list_all(self, db: Session) -> list[BrandProfile]:
        stmt = select(BrandProfile).order_by(BrandProfile.created_at.asc())
        return list(db.execute(stmt).scalars().all())

    def create(
        self,
        db: Session,
        *,
        name: str,
        description: str | None = None,
        tone_preset: str | None = None,
        banned_terms: list[str] | None = None,
        default_hashtags: list[str] | None = None,
        face_led_preferred: bool = False,
        content_language: str = "ru",
    ) -> BrandProfile:
        bp = BrandProfile(
            name=name,
            description=description,
            tone_preset=tone_preset,
            banned_terms=banned_terms or [],
            default_hashtags=default_hashtags or [],
            face_led_preferred=int(face_led_preferred),
            content_language=content_language,
        )
        db.add(bp)
        return bp
