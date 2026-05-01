"""Tests for Cloudinary signed upload helper (no real network)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import httpx
import pytest

from astro_content_agent.core.config import Settings
from astro_content_agent.services.media.cloudinary_uploader import (
    upload_local_image,
    validate_cloudinary_config,
)


def _settings_with_cloudinary(tmp_path: Path) -> Settings:
    img = tmp_path / "x.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    return Settings(
        _env_file=None,
        CLOUDINARY_CLOUD_NAME="demo",
        CLOUDINARY_API_KEY="key123",
        CLOUDINARY_API_SECRET="secret456",
        CLOUDINARY_FOLDER="astro-content-agent",
        ASSETS_DIR=str(tmp_path),
    )


def test_validate_cloudinary_config_missing_raises() -> None:
    s = Settings(_env_file=None, CLOUDINARY_CLOUD_NAME="", CLOUDINARY_API_KEY="", CLOUDINARY_API_SECRET="")
    with pytest.raises(ValueError, match="CLOUDINARY"):
        validate_cloudinary_config(s)


def test_upload_local_image_missing_file_raises(tmp_path: Path) -> None:
    s = _settings_with_cloudinary(tmp_path)
    with pytest.raises(ValueError, match="not found"):
        upload_local_image(s, tmp_path / "nope.png")


def test_upload_local_image_success_mocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    s = _settings_with_cloudinary(tmp_path)
    img = tmp_path / "up.jpg"
    img.write_bytes(b"\xff\xd8\xff")

    def _fake_post(url: str, *, data: dict, files: dict, timeout: float):  # type: ignore[no-untyped-def]
        assert "api.cloudinary.com" in url
        assert data.get("api_key") == "key123"
        assert "signature" in data
        assert "file" in files
        req = httpx.Request("POST", url)
        return httpx.Response(
            200,
            request=req,
            json={
                "secure_url": "https://res.cloudinary.com/demo/image/upload/v1/x.jpg",
                "public_id": "astro-content-agent/manual/up",
                "format": "jpg",
            },
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    out = upload_local_image(s, img, public_id="manual/up")
    assert out.secure_url.startswith("https://")
    assert "manual/up" in out.public_id or out.public_id
    assert out.local_path == img.resolve()
    assert out.format == "jpg"


def test_upload_cloudinary_cli_main_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from astro_content_agent.services.media.cloudinary_uploader import CloudinaryUploadResult

    repo = Path(__file__).resolve().parents[2]
    aca_dir = str(repo / "scripts" / "aca")
    if aca_dir not in sys.path:
        sys.path.insert(0, aca_dir)
    cli_path = repo / "scripts" / "aca" / "upload_cloudinary_image.py"
    spec = importlib.util.spec_from_file_location("_upload_cloudinary_cli", cli_path)
    assert spec and spec.loader
    uci = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(uci)

    img = tmp_path / "cli.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")

    fake = Settings(
        _env_file=None,
        CLOUDINARY_CLOUD_NAME="demo",
        CLOUDINARY_API_KEY="k",
        CLOUDINARY_API_SECRET="s",
        CLOUDINARY_FOLDER="f",
        ASSETS_DIR=str(tmp_path),
    )

    monkeypatch.setattr(uci, "get_settings", lambda: fake)

    def _fake_upload(settings, local_path, *, public_id=None, folder=None):  # type: ignore[no-untyped-def]
        assert settings is fake
        return CloudinaryUploadResult(
            secure_url="https://res.cloudinary.com/demo/x",
            public_id="pid",
            local_path=Path(local_path).resolve(),
            format="png",
            bytes=12,
        )

    monkeypatch.setattr(uci, "upload_local_image", _fake_upload)
    monkeypatch.setattr(sys, "argv", ["upload_cloudinary_image.py", "--image-path", str(img)])
    assert uci.main() == 0
