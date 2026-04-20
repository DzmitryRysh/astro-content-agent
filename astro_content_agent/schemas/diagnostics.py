from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CheckResult(BaseModel):
    """Result of a single diagnostic check."""

    name: str
    status: Literal["ok", "warning", "error"]
    message: str
    hint: str | None = None


class DiagnosticsReport(BaseModel):
    """Full runtime diagnostics report."""

    overall: Literal["ready", "degraded", "not_ready"]
    app_env: str
    checked_at: datetime
    checks: list[CheckResult]


class PublishSimulationPreview(BaseModel):
    """What would be sent to Instagram container creation (no network)."""

    image_url: str
    caption_excerpt: str
    storage_key: str
    ig_user_id: str | None = None


class PublishReadinessReport(BaseModel):
    """Dry-run publish readiness report for a specific draft."""

    draft_id: str
    ready: bool
    checks: list[CheckResult]
    checked_at: datetime
    instagram_account_id: str | None = None
    simulation: PublishSimulationPreview | None = None
