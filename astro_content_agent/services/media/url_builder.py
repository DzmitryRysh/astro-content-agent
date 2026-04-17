from __future__ import annotations

from pathlib import Path

from astro_content_agent.core.config import Settings
from astro_content_agent.services.media.storage import LocalFileStorage


def build_asset_url(storage_key: str, settings: Settings) -> str:
    """Build the public URL for an asset key using app settings.

    Convenience helper for callers that already hold a ``Settings`` instance
    but don't have a ``StorageBackend`` handy (e.g. background jobs).
    """
    base = settings.public_base_url.rstrip("/")
    key = storage_key.replace("\\", "/").lstrip("/")
    return f"{base}/media/{key}"


def get_local_storage(settings: Settings) -> LocalFileStorage:
    """Construct a ``LocalFileStorage`` from app settings."""
    return LocalFileStorage(
        assets_dir=Path(settings.assets_dir),
        public_base_url=settings.public_base_url,
    )
