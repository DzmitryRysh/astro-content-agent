from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from astro_content_agent.core.config import Settings
from astro_content_agent.schemas.diagnostics import (
    CheckResult,
    DiagnosticsReport,
    PublishReadinessReport,
    PublishSimulationPreview,
)

_VALID_STORAGE_MODES = frozenset({"local"})


def _ok(name: str, message: str) -> CheckResult:
    return CheckResult(name=name, status="ok", message=message)


def _warn(name: str, message: str, hint: str | None = None) -> CheckResult:
    return CheckResult(name=name, status="warning", message=message, hint=hint)


def _err(name: str, message: str, hint: str | None = None) -> CheckResult:
    return CheckResult(name=name, status="error", message=message, hint=hint)


def _overall(checks: list[CheckResult]) -> Literal["ready", "degraded", "not_ready"]:
    statuses = {c.status for c in checks}
    if "error" in statuses:
        return "not_ready"
    if "warning" in statuses:
        return "degraded"
    return "ready"


class DiagnosticsService:
    """Evaluates runtime configuration and data readiness.

    All checks are purely read-only — no writes, no external network calls.
    """

    # ------------------------------------------------------------------
    # Config checks
    # ------------------------------------------------------------------

    def run_config_checks(self, settings: Settings, db: Session) -> DiagnosticsReport:
        """Run all environment / config / DB-state checks and return a report."""
        checks: list[CheckResult] = [
            self._check_openai_key(settings),
            self._check_admin_key(settings),
            self._check_public_base_url(settings),
            self._check_storage_mode(settings),
            self._check_assets_dir(settings),
            self._check_asset_url_generation(settings),
            self._check_instagram_access_token(settings),
            self._check_instagram_ig_user_id_env(settings),
            self._check_instagram_accounts(settings, db),
            self._check_brand_profiles(db),
        ]
        return DiagnosticsReport(
            overall=_overall(checks),
            app_env=settings.app_env,
            checked_at=datetime.now(UTC),
            checks=checks,
        )

    def _check_openai_key(self, settings: Settings) -> CheckResult:
        name = "openai_api_key"
        if settings.openai_api_key:
            return _ok(name, "OPENAI_API_KEY is set.")
        if settings.app_env == "local":
            return _warn(
                name,
                "OPENAI_API_KEY is not set — AI generation will fail.",
                hint="Set OPENAI_API_KEY in your .env file to enable content generation.",
            )
        return _err(
            name,
            "OPENAI_API_KEY is not set.",
            hint="Set OPENAI_API_KEY in your environment before deploying to staging/prod.",
        )

    def _check_admin_key(self, settings: Settings) -> CheckResult:
        name = "admin_api_key"
        if settings.admin_api_key:
            return _ok(name, "ADMIN_API_KEY is set — admin routes are protected.")
        if settings.app_env == "local":
            return _ok(name, "ADMIN_API_KEY not set — guard disabled for local development.")
        return _warn(
            name,
            "ADMIN_API_KEY is not set — admin routes are unprotected.",
            hint="Set ADMIN_API_KEY before staging/prod exposure.",
        )

    def _check_public_base_url(self, settings: Settings) -> CheckResult:
        name = "public_base_url"
        url = settings.public_base_url
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return _err(
                name,
                f"PUBLIC_BASE_URL '{url}' is not a valid URL.",
                hint="Set PUBLIC_BASE_URL to a fully-qualified URL, e.g. https://myserver.example.com",
            )
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0")
        if is_localhost and settings.app_env in ("staging", "prod"):
            return _err(
                name,
                f"PUBLIC_BASE_URL is set to localhost ('{url}') but APP_ENV is '{settings.app_env}'.",
                hint="Set PUBLIC_BASE_URL to a real publicly accessible URL for Instagram to fetch assets.",
            )
        if is_localhost:
            return _warn(
                name,
                f"PUBLIC_BASE_URL is localhost ('{url}'). Instagram cannot fetch assets from localhost.",
                hint="Use a tunnel (e.g. ngrok) and update PUBLIC_BASE_URL before publishing to real Instagram.",
            )
        return _ok(name, f"PUBLIC_BASE_URL is set to '{url}'.")

    def _check_storage_mode(self, settings: Settings) -> CheckResult:
        name = "storage_mode"
        mode = settings.storage_mode
        if mode in _VALID_STORAGE_MODES:
            return _ok(name, f"STORAGE_MODE='{mode}' is valid.")
        return _warn(
            name,
            f"STORAGE_MODE='{mode}' is not a recognised value. Supported: {sorted(_VALID_STORAGE_MODES)}.",
            hint="Use 'local' for development. S3/GCS support is a future extension.",
        )

    def _check_assets_dir(self, settings: Settings) -> CheckResult:
        name = "assets_dir"
        path = Path(settings.assets_dir).expanduser()
        try:
            resolved = path.resolve()
        except OSError as exc:
            return _err(name, f"ASSETS_DIR is not usable: {exc}.", hint="Fix ASSETS_DIR to a valid path.")
        if resolved.is_dir():
            return _ok(name, f"ASSETS_DIR exists: {resolved}")
        if settings.app_env == "local":
            return _warn(
                name,
                f"ASSETS_DIR path '{resolved}' is not a directory yet.",
                hint="The app creates it on startup for local storage, or create it before saving media.",
            )
        return _err(
            name,
            f"ASSETS_DIR '{resolved}' must exist for local storage when APP_ENV='{settings.app_env}'.",
            hint="Create the directory or adjust ASSETS_DIR.",
        )

    def _check_instagram_access_token(self, settings: Settings) -> CheckResult:
        name = "instagram_access_token"
        if settings.instagram_access_token:
            return _ok(name, "INSTAGRAM_ACCESS_TOKEN is set (used for all Graph API publish calls).")
        if settings.app_env == "local":
            return _warn(
                name,
                "INSTAGRAM_ACCESS_TOKEN is not set — real publish endpoints return 503.",
                hint="Use POST /api/v1/publish/{draft_id}/dry-run to validate drafts without Meta. Set token when Meta access is ready.",
            )
        return _err(
            name,
            "INSTAGRAM_ACCESS_TOKEN is not set.",
            hint="Configure a long-lived token from the Meta Developer Console.",
        )

    def _check_instagram_ig_user_id_env(self, settings: Settings) -> CheckResult:
        name = "instagram_ig_user_id"
        if settings.instagram_ig_user_id:
            return _ok(
                name,
                "INSTAGRAM_IG_USER_ID is set in environment (publish jobs still require instagram_accounts.ig_user_id).",
            )
        return _warn(
            name,
            "INSTAGRAM_IG_USER_ID is not set in environment (optional).",
            hint="Each publish job uses instagram_accounts.ig_user_id — set that column from Meta for the connected IG user.",
        )

    def _check_asset_url_generation(self, settings: Settings) -> CheckResult:
        name = "asset_url_generation"
        test_key = "diagnostics/test-key/sample.png"
        try:
            from astro_content_agent.services.media.url_builder import build_asset_url

            url = build_asset_url(test_key, settings)
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return _err(name, f"Generated asset URL is not valid: '{url}'.")
            return _ok(name, f"Asset URL generation works. Sample: '{url}'.")
        except Exception as exc:
            return _err(name, f"Asset URL generation raised an error: {exc}.")

    def _check_instagram_accounts(self, settings: Settings, db: Session) -> CheckResult:
        name = "instagram_accounts"
        try:
            from sqlalchemy import select
            from astro_content_agent.db.models import InstagramAccount

            stmt = select(InstagramAccount).where(
                InstagramAccount.is_active == 1,
                InstagramAccount.access_token.isnot(None),
            )
            active = db.execute(stmt).scalars().all()
            count = len(active)
            if count == 0:
                severity = "warning" if settings.app_env == "local" else "error"
                msg = "No active Instagram accounts with an access_token found."
                hint = "Create an InstagramAccount record with a valid access_token to enable publishing."
                return CheckResult(name=name, status=severity, message=msg, hint=hint)  # type: ignore[arg-type]
            return _ok(name, f"{count} active Instagram account(s) with access_token found.")
        except Exception as exc:
            return _err(name, f"Could not query Instagram accounts: {exc}.")

    def _check_brand_profiles(self, db: Session) -> CheckResult:
        name = "brand_profiles"
        try:
            from astro_content_agent.repositories.brand_profiles import BrandProfileRepository

            profiles = BrandProfileRepository().list_all(db)
            if not profiles:
                return _warn(
                    name,
                    "No brand profiles found.",
                    hint=(
                        "From the repository root: python scripts/aca/seed_brand_profile.py "
                        "(if that script exists in your checkout), or POST /api/v1/admin/brand-profile."
                    ),
                )
            return _ok(name, f"{len(profiles)} brand profile(s) found.")
        except Exception as exc:
            return _err(name, f"Could not query brand profiles: {exc}.")

    # ------------------------------------------------------------------
    # Publish readiness (dry-run)
    # ------------------------------------------------------------------

    def run_publish_readiness(
        self,
        db: Session,
        *,
        draft_id: str,
        settings: Settings,
        instagram_account_id: str | None = None,
        include_simulation: bool = False,
    ) -> PublishReadinessReport:
        """Validate all preconditions for publishing a specific draft.

        Does not perform any external network call or state mutation.
        """
        checks: list[CheckResult] = []
        checks.extend(self._check_draft_for_publish(db, draft_id))
        checks.extend(self._check_publish_config(settings))
        if instagram_account_id is not None:
            checks.extend(self._check_instagram_account_for_publish(db, instagram_account_id))

        simulation: PublishSimulationPreview | None = None
        if include_simulation:
            sim, sim_checks = self._build_publish_simulation(db, draft_id, settings, instagram_account_id)
            checks.extend(sim_checks)
            simulation = sim

        all_ok = all(c.status == "ok" for c in checks)
        return PublishReadinessReport(
            draft_id=draft_id,
            ready=all_ok,
            checks=checks,
            checked_at=datetime.now(UTC),
            instagram_account_id=instagram_account_id,
            simulation=simulation,
        )

    def _check_draft_for_publish(
        self, db: Session, draft_id: str
    ) -> list[CheckResult]:
        results: list[CheckResult] = []
        from astro_content_agent.repositories.assets import AssetRepository
        from astro_content_agent.repositories.drafts import DraftRepository

        # Draft existence
        draft = DraftRepository().get_by_id(db, draft_id)
        if draft is None:
            results.append(
                _err("draft_exists", f"Draft '{draft_id}' not found.", hint="Check the draft_id.")
            )
            return results  # nothing else to check
        results.append(_ok("draft_exists", f"Draft '{draft_id}' found."))

        # Draft status
        if draft.status == "approved":
            results.append(_ok("draft_approved", "Draft is approved."))
        else:
            results.append(
                _err(
                    "draft_approved",
                    f"Draft status is '{draft.status}', must be 'approved' to publish.",
                    hint="Approve the draft via POST /api/v1/drafts/{draft_id}/approve",
                )
            )

        # Draft type publishable
        publishable_types = frozenset({"post"})
        if draft.draft_type in publishable_types:
            results.append(_ok("draft_type_publishable", f"draft_type='{draft.draft_type}' is publishable."))
        else:
            results.append(
                _warn(
                    "draft_type_publishable",
                    f"draft_type='{draft.draft_type}' is not publishable in MVP (only 'post').",
                    hint="Only image posts are publishable. Reels/carousels are draft-only in MVP.",
                )
            )

        # Asset exists
        assets = AssetRepository().list_for_draft(db, draft_id)
        if assets:
            asset = assets[0]
            results.append(_ok("draft_has_asset", f"Draft has {len(assets)} asset(s)."))
            # Asset URL buildable
            if asset.storage_path:
                results.append(_ok("asset_key_present", f"Asset storage key: '{asset.storage_path}'."))
            else:
                results.append(
                    _err("asset_key_present", "Asset has no storage_path.", hint="Regenerate the image.")
                )
        else:
            results.append(
                _err(
                    "draft_has_asset",
                    "No assets found for draft.",
                    hint="Generate an image first via POST /api/v1/drafts/{draft_id}/generate-image",
                )
            )

        return results

    def _check_publish_config(self, settings: Settings) -> list[CheckResult]:
        results: list[CheckResult] = []

        # PUBLIC_BASE_URL (must be non-localhost for real Instagram publishing)
        parsed = urlparse(settings.public_base_url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0")
        if is_localhost:
            results.append(
                _warn(
                    "publish_public_url",
                    f"PUBLIC_BASE_URL='{settings.public_base_url}' is localhost — Instagram cannot fetch assets.",
                    hint="Use a tunnel (ngrok) or real public URL and set PUBLIC_BASE_URL accordingly.",
                )
            )
        else:
            results.append(_ok("publish_public_url", f"PUBLIC_BASE_URL='{settings.public_base_url}' is non-localhost."))

        if settings.instagram_access_token:
            results.append(
                _ok(
                    "publish_instagram_token",
                    "INSTAGRAM_ACCESS_TOKEN is set — real publish API calls can authenticate.",
                )
            )
        elif settings.app_env == "local":
            results.append(
                _warn(
                    "publish_instagram_token",
                    "INSTAGRAM_ACCESS_TOKEN is not set — POST /publish/{id} returns 503.",
                    hint="Use POST /api/v1/publish/{draft_id}/dry-run to validate without Meta. Set token when developer access is ready.",
                )
            )
        else:
            results.append(
                _err(
                    "publish_instagram_token",
                    "INSTAGRAM_ACCESS_TOKEN is not set — publishing cannot run in this environment.",
                    hint="Configure the token from Meta Developer Console.",
                )
            )

        return results

    def _check_instagram_account_for_publish(
        self, db: Session, instagram_account_id: str
    ) -> list[CheckResult]:
        from astro_content_agent.db.models import InstagramAccount

        account = db.get(InstagramAccount, instagram_account_id)
        if account is None:
            return [
                _err(
                    "instagram_account",
                    f"No instagram_accounts row for id='{instagram_account_id}'.",
                    hint="Use an existing instagram_account_id from the DB or admin API.",
                )
            ]
        out: list[CheckResult] = [
            _ok("instagram_account", f"Account '{account.account_name}' found."),
        ]
        if account.is_active != 1:
            out.append(
                _err(
                    "instagram_account_active",
                    "Instagram account is not active (is_active != 1).",
                    hint="Set is_active=1 before scheduling publish.",
                )
            )
        else:
            out.append(_ok("instagram_account_active", "Instagram account is active."))
        if not account.ig_user_id:
            out.append(
                _err(
                    "instagram_account_ig_user_id",
                    "instagram_accounts.ig_user_id is missing.",
                    hint="Set the numeric Instagram user id from Meta (Graph API user id, not @handle).",
                )
            )
        else:
            out.append(_ok("instagram_account_ig_user_id", "instagram_accounts.ig_user_id is set."))
        return out

    def _build_publish_simulation(
        self,
        db: Session,
        draft_id: str,
        settings: Settings,
        instagram_account_id: str | None,
    ) -> tuple[PublishSimulationPreview | None, list[CheckResult]]:
        from astro_content_agent.db.models import InstagramAccount
        from astro_content_agent.repositories.assets import AssetRepository
        from astro_content_agent.repositories.drafts import DraftRepository
        from astro_content_agent.services.instagram.container_builder import ContainerBuilder
        from astro_content_agent.services.media.url_builder import get_local_storage

        draft = DraftRepository().get_by_id(db, draft_id)
        if draft is None:
            return None, []

        assets = AssetRepository().list_for_draft(db, draft_id)
        if not assets:
            return None, []

        ig_user_id: str | None = None
        if instagram_account_id is not None:
            acc = db.get(InstagramAccount, instagram_account_id)
            if acc is not None:
                ig_user_id = acc.ig_user_id

        try:
            storage = get_local_storage(settings)
            cb = ContainerBuilder(url_resolver=storage.url)
            params = cb.build(draft=draft, asset=assets[0])
        except Exception as exc:
            return None, [
                _err(
                    "publish_payload_build",
                    str(exc),
                    hint="Fix draft_type, PostDraftPayload fields, or asset mime_type before publish.",
                )
            ]

        cap = params.caption
        excerpt = cap if len(cap) <= 500 else cap[:497] + "..."
        return (
            PublishSimulationPreview(
                image_url=params.image_url,
                caption_excerpt=excerpt,
                storage_key=assets[0].storage_path,
                ig_user_id=ig_user_id,
            ),
            [],
        )
