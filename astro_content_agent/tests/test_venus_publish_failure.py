"""Classification for Venus weekly real-publish failures."""
from __future__ import annotations

import httpx
import pytest

from astro_content_agent.services.content.venus_publish_failure import (
    classify_exception,
    classify_message,
    next_publish_attempt_count,
)
from astro_content_agent.services.instagram.client import MetaAPIError, MetaInstagramClient, redact_access_token_from_url
from astro_content_agent.services.instagram.publisher import PublisherService


def _http_error(code: int) -> httpx.HTTPStatusError:
    req = httpx.Request("GET", "https://graph.facebook.com/x")
    resp = httpx.Response(code, request=req)
    return httpx.HTTPStatusError("fail", request=req, response=resp)


def test_classify_503_retryable() -> None:
    c = classify_exception(_http_error(503))
    assert c.error_type == "meta_http_transient"
    assert c.publish_retryable is True


def test_classify_400_not_retryable() -> None:
    c = classify_exception(_http_error(400))
    assert c.error_type == "meta_http_client_error"
    assert c.publish_retryable is False


def test_classify_meta_api_error_400_not_retryable() -> None:
    c = classify_exception(
        MetaAPIError(
            status_code=400,
            url="https://graph.facebook.com/v19.0/1/media?access_token=<REDACTED>",
            response_text='{"error":{"message":"Invalid image URL","type":"OAuthException","code":190}}',
            response_json={"error": {"message": "Invalid image URL", "type": "OAuthException", "code": 190}},
            meta_error_code=190,
            meta_error_subcode=None,
            meta_error_type="OAuthException",
            meta_error_message="Invalid image URL",
        )
    )
    assert c.error_type == "meta_http_client_error"
    assert c.publish_retryable is False


def test_iga_token_uses_graph_instagram_media_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def _fake_post(url: str, *, params: dict, timeout: int):  # type: ignore[no-untyped-def]
        seen["url"] = url
        seen["params"] = params
        req = httpx.Request("POST", url, params=params)
        return httpx.Response(200, request=req, json={"id": "cont-1"})

    monkeypatch.setattr(httpx, "post", _fake_post)
    c = MetaInstagramClient(access_token="IGA" + "x" * 20)
    out = c.create_image_container(ig_user_id="17841400000000000", image_url="https://example.com/x.png", caption="Hi")
    assert out == "cont-1"
    assert str(seen["url"]).startswith("https://graph.instagram.com/")
    assert str(seen["url"]).endswith("/17841400000000000/media")


def test_redact_access_token_from_url() -> None:
    raw = "https://graph.instagram.com/1/media?caption=x&access_token=IGAabcdef123&x=1"
    redacted = redact_access_token_from_url(raw)
    assert "access_token=<REDACTED>" in redacted
    assert "IGAabcdef123" not in redacted


def test_classify_timeout_retryable() -> None:
    c = classify_exception(httpx.ReadTimeout("timeout"))
    assert c.error_type == "network_timeout"
    assert c.publish_retryable is True


def test_classify_draft_not_approved() -> None:
    c = classify_exception(PublisherService.DraftNotApprovedError("not approved"))
    assert c.error_type == "draft_not_approved"
    assert c.publish_retryable is False


def test_classify_message_unknown() -> None:
    c = classify_message("something weird from Meta")
    assert c.error_type == "unknown"
    assert c.publish_retryable is False


def test_next_publish_attempt_count_increments() -> None:
    state: dict = {
        "real_publish": {
            "publish_attempt_count": 2,
        }
    }
    assert next_publish_attempt_count(state) == 3
    assert next_publish_attempt_count({}) == 1


@pytest.mark.parametrize(
    "snippet,expected_type",
    [
        ("OAuthException", "meta_token_invalid"),
        ("access token", "meta_token_invalid"),
        ("image could not be accessed", "meta_media_fetch"),
    ],
)
def test_classify_message_token_and_media(snippet: str, expected_type: str) -> None:
    c = classify_message(snippet + " details here")
    assert c.error_type == expected_type
