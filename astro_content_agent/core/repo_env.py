"""Repo-root ``.env`` loading for CLIs (values never logged from this module)."""
from __future__ import annotations

import os
from pathlib import Path


def load_repo_dotenv_if_present(repo_root: Path, *, override: bool = False) -> bool:
    """Populate ``os.environ`` from ``repo_root / ".env"`` if that file exists.

    *override* is passed to python-dotenv: when ``False`` (default), variables
    already set in the environment are not replaced (so explicit exports and
    subprocess env win over ``.env``).

    Returns ``True`` if a ``.env`` file was found and processed, else ``False``.
    Does not print secret values.
    """
    dotenv_path = Path(repo_root).expanduser().resolve() / ".env"
    if not dotenv_path.is_file():
        return False
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False
    load_dotenv(dotenv_path, override=override)
    return True


def resolve_publish_target_ids(
    *,
    cli_brand_profile_id: str | None,
    cli_instagram_account_id: str | None,
) -> tuple[str | None, str | None]:
    """Resolve brand / Instagram account ids: CLI args override ``ACA_*`` env."""
    bp = (cli_brand_profile_id or os.environ.get("ACA_BRAND_PROFILE_ID") or "").strip() or None
    ia = (cli_instagram_account_id or os.environ.get("ACA_INSTAGRAM_ACCOUNT_ID") or "").strip() or None
    return bp, ia
