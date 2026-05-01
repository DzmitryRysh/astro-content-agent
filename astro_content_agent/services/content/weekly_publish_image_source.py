"""CLI helpers: exactly one Venus weekly publish image source (--url | --storage-key | --path)."""
from __future__ import annotations

from pathlib import Path
from typing import Literal


def weekly_publish_image_mode(
    *,
    post_image_url: str | None,
    post_image_storage_key: str | None,
    post_image_path: Path | str | None,
) -> Literal["url", "storage_key", "path"]:
    """Return which image source mode is active; require exactly one."""
    use_u = bool(str(post_image_url or "").strip())
    use_k = bool(str(post_image_storage_key or "").strip())
    use_p = bool(str(post_image_path or "").strip())
    n = use_u + use_k + use_p
    if n == 0:
        raise ValueError(
            "Missing image source: provide exactly one of --post-image-url, "
            "--post-image-storage-key, or --post-image-path."
        )
    if n > 1:
        raise ValueError(
            "Provide exactly one of --post-image-url, --post-image-storage-key, or --post-image-path."
        )
    if use_u:
        return "url"
    if use_k:
        return "storage_key"
    return "path"


__all__ = ["weekly_publish_image_mode"]
