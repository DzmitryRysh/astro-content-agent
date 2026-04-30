from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qsl, quote_plus, urlsplit, urlunsplit

import httpx


class InstagramClientProtocol(Protocol):
    """Abstract interface for the Meta Instagram Graph API.

    Concrete implementations: MetaInstagramClient (real), FakeInstagramClient (tests).
    """

    def create_image_container(
        self,
        *,
        ig_user_id: str,
        image_url: str,
        caption: str,
    ) -> str:
        """Upload image metadata and return the IG container_id.

        Note: `image_url` must be a publicly accessible URL in production.
        For placeholder/test assets the fake client accepts any string.
        """

    def publish_container(
        self,
        *,
        ig_user_id: str,
        container_id: str,
    ) -> str:
        """Publish an existing container and return the ig_media_id."""


@dataclass(frozen=True)
class MetaAPIError(Exception):
    status_code: int
    url: str
    response_text: str
    response_json: dict | list | None = None
    meta_error_code: int | None = None
    meta_error_subcode: int | None = None
    meta_error_type: str | None = None
    meta_error_message: str | None = None

    def __str__(self) -> str:
        msg = self.meta_error_message or f"Meta Graph API HTTP {self.status_code}"
        parts = [msg, f"status={self.status_code}"]
        if self.meta_error_code is not None:
            parts.append(f"code={self.meta_error_code}")
        if self.meta_error_subcode is not None:
            parts.append(f"subcode={self.meta_error_subcode}")
        return " | ".join(parts)


def redact_access_token_from_url(url: str) -> str:
    try:
        split = urlsplit(url)
        redacted_parts: list[str] = []
        for k, v in parse_qsl(split.query, keep_blank_values=True):
            if k.lower() == "access_token":
                redacted_parts.append(f"{quote_plus(k)}=<REDACTED>")
            else:
                redacted_parts.append(f"{quote_plus(k)}={quote_plus(v)}")
        return urlunsplit((split.scheme, split.netloc, split.path, "&".join(redacted_parts), split.fragment))
    except Exception:
        return url.replace("access_token=", "access_token=<REDACTED>")


def _to_meta_error(resp: httpx.Response) -> MetaAPIError:
    redacted_url = redact_access_token_from_url(str(resp.request.url))
    txt = resp.text
    body_json: dict | list | None = None
    try:
        body_json = resp.json()
    except (ValueError, json.JSONDecodeError):
        body_json = None
    err_obj = body_json.get("error") if isinstance(body_json, dict) and isinstance(body_json.get("error"), dict) else {}
    return MetaAPIError(
        status_code=resp.status_code,
        url=redacted_url,
        response_text=txt,
        response_json=body_json,
        meta_error_code=err_obj.get("code"),
        meta_error_subcode=err_obj.get("error_subcode"),
        meta_error_type=err_obj.get("type"),
        meta_error_message=err_obj.get("message"),
    )


def _raise_for_status_with_meta_details(resp: httpx.Response) -> None:
    if 200 <= resp.status_code < 300:
        return
    raise _to_meta_error(resp)


class MetaInstagramClient:
    """Real Meta Graph API client.

    Requires a valid short- or long-lived access token with
    `instagram_basic`, `instagram_content_publish` permissions.
    """

    _BASE_DEFAULT_IGA = "https://graph.instagram.com"
    _BASE_DEFAULT_FB = "https://graph.facebook.com/v19.0"

    def __init__(self, access_token: str, *, base_url: str | None = None) -> None:
        self._token = access_token
        self._base_url = self._resolve_base_url(access_token=access_token, configured_base_url=base_url)

    @classmethod
    def _resolve_base_url(cls, *, access_token: str, configured_base_url: str | None) -> str:
        if configured_base_url and configured_base_url.strip():
            return configured_base_url.strip().rstrip("/")
        if access_token.startswith("IGA"):
            return cls._BASE_DEFAULT_IGA
        return cls._BASE_DEFAULT_FB

    def create_image_container(
        self,
        *,
        ig_user_id: str,
        image_url: str,
        caption: str,
    ) -> str:
        resp = httpx.post(
            f"{self._base_url}/{ig_user_id}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": self._token,
            },
            timeout=30,
        )
        _raise_for_status_with_meta_details(resp)
        data = resp.json()
        if "id" not in data:
            raise ValueError(f"Unexpected IG response: {data}")
        return data["id"]

    def publish_container(
        self,
        *,
        ig_user_id: str,
        container_id: str,
    ) -> str:
        resp = httpx.post(
            f"{self._base_url}/{ig_user_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self._token,
            },
            timeout=30,
        )
        _raise_for_status_with_meta_details(resp)
        data = resp.json()
        if "id" not in data:
            raise ValueError(f"Unexpected IG response: {data}")
        return data["id"]
