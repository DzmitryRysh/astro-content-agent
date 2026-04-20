from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from astro_content_agent.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    """Timezone-aware UTC for ORM defaults (replaces deprecated datetime.utcnow)."""
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )


class InstagramAccount(Base, TimestampMixin):
    __tablename__ = "instagram_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ig_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    facebook_page_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class BrandProfile(Base, TimestampMixin):
    __tablename__ = "brand_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone_preset: Mapped[str | None] = mapped_column(String(200), nullable=True)
    banned_terms: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    default_hashtags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    face_led_preferred: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    content_language: Mapped[str] = mapped_column(String(10), nullable=False, default="ru")


class ContentPillar(Base, TimestampMixin):
    __tablename__ = "content_pillars"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand_profile_id: Mapped[str] = mapped_column(ForeignKey("brand_profiles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class AstroSignal(Base, TimestampMixin):
    __tablename__ = "astro_signals"
    __table_args__ = (UniqueConstraint("signal_date", "brand_profile_id", name="uq_astro_signals_day_brand"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand_profile_id: Mapped[str] = mapped_column(ForeignKey("brand_profiles.id"), nullable=False)
    signal_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v0")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class ContentPlan(Base, TimestampMixin):
    __tablename__ = "content_plans"
    __table_args__ = (UniqueConstraint("plan_date", "brand_profile_id", name="uq_content_plans_day_brand"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand_profile_id: Mapped[str] = mapped_column(ForeignKey("brand_profiles.id"), nullable=False)
    plan_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    astro_signal_id: Mapped[str | None] = mapped_column(ForeignKey("astro_signals.id"), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class Draft(Base, TimestampMixin):
    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand_profile_id: Mapped[str] = mapped_column(ForeignKey("brand_profiles.id"), nullable=False)
    content_plan_id: Mapped[str | None] = mapped_column(ForeignKey("content_plans.id"), nullable=True)
    draft_type: Mapped[str] = mapped_column(String(50), nullable=False)  # post|carousel|reel
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")  # draft|approved|rejected
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand_profile_id: Mapped[str] = mapped_column(ForeignKey("brand_profiles.id"), nullable=False)
    draft_id: Mapped[str | None] = mapped_column(ForeignKey("drafts.id"), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, default="image")
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class PublishJob(Base, TimestampMixin):
    __tablename__ = "publish_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instagram_account_id: Mapped[str] = mapped_column(ForeignKey("instagram_accounts.id"), nullable=False)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")  # queued|running|succeeded|failed
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_container_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_publish_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class PublishedPost(Base, TimestampMixin):
    __tablename__ = "published_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    publish_job_id: Mapped[str] = mapped_column(ForeignKey("publish_jobs.id"), nullable=False)
    instagram_account_id: Mapped[str] = mapped_column(ForeignKey("instagram_accounts.id"), nullable=False)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.id"), nullable=False)
    ig_media_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ig_permalink: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class AnalyticsSnapshot(Base, TimestampMixin):
    __tablename__ = "analytics_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    published_post_id: Mapped[str] = mapped_column(ForeignKey("published_posts.id"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class PromptVersion(Base, TimestampMixin):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_prompt_versions_name_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class ModelRun(Base, TimestampMixin):
    __tablename__ = "model_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    prompt_version_id: Mapped[str | None] = mapped_column(ForeignKey("prompt_versions.id"), nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="succeeded")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class ErrorLog(Base, TimestampMixin):
    __tablename__ = "error_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scope: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

