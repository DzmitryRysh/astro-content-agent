from __future__ import annotations

import uuid

from astro_content_agent.services.instagram.client import MetaAPIError


class FakeInstagramClient:
    """Fake Meta client for tests.

    Pass ``fail_on_container=True`` to simulate a failure during container creation.
    Pass ``fail_on_publish=True`` to simulate a failure during media publish
    (non-Meta ``RuntimeError``).
    Pass ``publish_not_ready_failures=N`` to raise Meta ``9007``/``2207027`` on the first
    ``N`` ``publish_container`` calls, then succeed (for readiness retry tests).
    Tracks all calls so tests can assert on them.
    """

    def __init__(
        self,
        *,
        fail_on_container: bool = False,
        fail_on_publish: bool = False,
        container_id_override: str | None = None,
        media_id_override: str | None = None,
        publish_not_ready_failures: int = 0,
    ) -> None:
        self.fail_on_container = fail_on_container
        self.fail_on_publish = fail_on_publish
        self.container_id_override = container_id_override
        self.media_id_override = media_id_override
        self._publish_not_ready_failures = publish_not_ready_failures
        self.container_calls: list[dict] = []
        self.publish_calls: list[dict] = []

    def create_image_container(
        self,
        *,
        ig_user_id: str,
        image_url: str,
        caption: str,
    ) -> str:
        self.container_calls.append({"ig_user_id": ig_user_id, "image_url": image_url, "caption": caption})
        if self.fail_on_container:
            raise RuntimeError("Simulated container creation failure")
        return self.container_id_override or f"fake-container-{uuid.uuid4().hex[:8]}"

    def publish_container(
        self,
        *,
        ig_user_id: str,
        container_id: str,
    ) -> str:
        self.publish_calls.append({"ig_user_id": ig_user_id, "container_id": container_id})
        if self.fail_on_publish:
            raise RuntimeError("Simulated publish failure")
        if self._publish_not_ready_failures > 0:
            self._publish_not_ready_failures -= 1
            raise MetaAPIError(
                status_code=400,
                url="https://graph.instagram.com/0/media_publish?access_token=<REDACTED>",
                response_text="{}",
                response_json={
                    "error": {
                        "message": "Media ID is not available",
                        "type": "OAuthException",
                        "code": 9007,
                        "error_subcode": 2207027,
                    }
                },
                meta_error_code=9007,
                meta_error_subcode=2207027,
                meta_error_type="OAuthException",
                meta_error_message="Media ID is not available",
            )
        return self.media_id_override or f"fake-media-{uuid.uuid4().hex[:8]}"
