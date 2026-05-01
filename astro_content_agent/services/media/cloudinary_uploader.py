"""Upload local images to Cloudinary (signed upload). No Instagram credentials required."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from astro_content_agent.core.config import Settings


@dataclass(frozen=True)
class CloudinaryUploadResult:
    secure_url: str
    public_id: str
    local_path: Path
    format: str | None = None
    bytes: int | None = None


def _cloudinary_signature(params: dict[str, str], api_secret: str) -> str:
    """SHA1 signature for Cloudinary API (sorted key=value, then secret)."""
    to_sign = "&".join(f"{k}={params[k]}" for k in sorted(params))
    return hashlib.sha1((to_sign + api_secret).encode("utf-8")).hexdigest()


def validate_cloudinary_config(settings: Settings) -> tuple[str, str, str, str]:
    """Return (cloud_name, api_key, api_secret, folder) or raise ValueError."""
    cloud = (settings.cloudinary_cloud_name or "").strip()
    key = (settings.cloudinary_api_key or "").strip()
    secret = (settings.cloudinary_api_secret or "").strip()
    folder = (settings.cloudinary_folder or "").strip() or "astro-content-agent"
    missing = [n for n, v in (("CLOUDINARY_CLOUD_NAME", cloud), ("CLOUDINARY_API_KEY", key), ("CLOUDINARY_API_SECRET", secret)) if not v]
    if missing:
        raise ValueError(
            "Cloudinary is not configured. Set in environment or .env: "
            + ", ".join(missing)
            + ". Optional: CLOUDINARY_FOLDER (default astro-content-agent)."
        )
    return cloud, key, secret, folder


def upload_local_image(
    settings: Settings,
    local_path: Path | str,
    *,
    public_id: str | None = None,
    folder: str | None = None,
    timeout_seconds: float = 120.0,
) -> CloudinaryUploadResult:
    """Upload a local image file to Cloudinary and return ``secure_url``."""
    cloud, api_key, api_secret, default_folder = validate_cloudinary_config(settings)
    path = Path(local_path).expanduser()
    if not path.is_file():
        raise ValueError(f"Image file not found: {path}")

    folder_final = (folder.strip() if folder else None) or default_folder
    timestamp = str(int(time.time()))

    sign_params: dict[str, str] = {"timestamp": timestamp}
    if folder_final:
        sign_params["folder"] = folder_final
    if public_id and public_id.strip():
        sign_params["public_id"] = public_id.strip()

    signature = _cloudinary_signature(sign_params, api_secret)

    url = f"https://api.cloudinary.com/v1_1/{cloud}/image/upload"
    data: dict[str, str] = {
        "api_key": api_key,
        "timestamp": timestamp,
        "signature": signature,
    }
    if folder_final:
        data["folder"] = folder_final
    if public_id and public_id.strip():
        data["public_id"] = public_id.strip()

    file_bytes = path.read_bytes()
    files = {"file": (path.name, file_bytes, "application/octet-stream")}

    resp = httpx.post(url, data=data, files=files, timeout=timeout_seconds)
    if resp.status_code >= 400:
        raise RuntimeError(f"Cloudinary upload failed HTTP {resp.status_code}: {resp.text[:2000]}")

    body: dict[str, Any] = resp.json()
    secure = body.get("secure_url")
    pid = body.get("public_id")
    if not secure or not isinstance(secure, str):
        raise RuntimeError(f"Cloudinary response missing secure_url: {body!r}")
    if not pid or not isinstance(pid, str):
        pid = ""

    fmt = body.get("format")
    fmt_s = str(fmt) if fmt is not None else None

    return CloudinaryUploadResult(
        secure_url=secure,
        public_id=pid,
        local_path=path.resolve(),
        format=fmt_s,
        bytes=len(file_bytes),
    )


__all__ = [
    "CloudinaryUploadResult",
    "upload_local_image",
    "validate_cloudinary_config",
]
