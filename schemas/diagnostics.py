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


class PublishReadinessReport(BaseModel):
    """Dry-run publish readiness report for a specific draft."""

    draft_id: str
    ready: bool
    checks: list[CheckResult]
    checked_at: datetime
