from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol for pluggable file storage backends.

    ``storage_path`` / key semantics:
    - Always a forward-slash relative path, e.g. ``brand_id/draft_id/placeholder.png``.
    - Never an absolute OS path.
    - Portable: LocalFileStorage maps it to ``assets_dir/key``; an S3 backend
      would map it to a bucket object key.
    """

    def save(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        """Persist *data* at *key* and return the canonical (normalised) key."""
        ...

    def url(self, key: str) -> str:
        """Return a publicly accessible URL for the given storage key."""
        ...

    def absolute_path(self, key: str) -> Path | None:
        """Return the local filesystem path for *key*, or ``None`` for remote backends."""
        ...


class LocalFileStorage:
    """Stores files on the local filesystem and exposes them via a public base URL.

    Designed for local development.  S3/GCS migration: implement
    ``StorageBackend`` and swap the instance — callers are decoupled.

    Args:
        assets_dir: Root directory where files are written.
        public_base_url: Base URL used to build public URLs, e.g.
            ``http://localhost:8000``.  The file at key
            ``brand/draft/image.png`` will be accessible at
            ``{public_base_url}/media/brand/draft/image.png``.
    """

    def __init__(self, *, assets_dir: Path, public_base_url: str) -> None:
        self._assets_dir = assets_dir
        self._public_base_url = public_base_url.rstrip("/")

    def save(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        """Write *data* to ``assets_dir/key`` and return the normalised key."""
        dest = self._assets_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return self._normalise(key)

    def url(self, key: str) -> str:
        """Build ``{public_base_url}/media/{key}``."""
        return f"{self._public_base_url}/media/{self._normalise(key)}"

    def absolute_path(self, key: str) -> Path:
        """Return ``assets_dir/key`` as an absolute path."""
        return self._assets_dir / key

    @staticmethod
    def _normalise(key: str) -> str:
        """Convert backslashes to forward slashes and strip leading slashes."""
        return key.replace("\\", "/").lstrip("/")
