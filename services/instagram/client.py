from __future__ import annotations

from typing import Protocol

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


class MetaInstagramClient:
    """Real Meta Graph API client.

    Requires a valid short- or long-lived access token with
    `instagram_basic`, `instagram_content_publish` permissions.
    """

    _BASE = "https://graph.facebook.com/v19.0"

    def __init__(self, access_token: str) -> None:
        self._token = access_token

    def create_image_container(
        self,
        *,
        ig_user_id: str,
        image_url: str,
        caption: str,
    ) -> str:
        resp = httpx.post(
            f"{self._BASE}/{ig_user_id}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": self._token,
            },
            timeout=30,
        )
        resp.raise_for_status()
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
            f"{self._BASE}/{ig_user_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self._token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "id" not in data:
            raise ValueError(f"Unexpected IG response: {data}")
        return data["id"]
